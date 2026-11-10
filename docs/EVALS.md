# Prove — evals

A checker that raises false alarms is worse than no checker. The README will carry
measured numbers, and this is how they are produced. Report them as measured.

## Two questions, two evals

| Eval | Question | Needs a model | Runs in CI |
| :- | :- | :- | :- |
| **Judge eval** | Given correct claims, does `provecheck` give the right verdict? | No | Yes |
| **End-to-end eval** | Given only the document, does the whole thing catch planted errors without inventing new ones? | Yes | No, run by hand |

## The synthetic corpus

`evals/synth/generate.py --seed S --n N` writes reports about fictional organisations
from seeded random data. For each report it knows the truth, so it can plant errors and
record exactly where they are.

Each report has: prose with derived figures, 2–4 tables, 1–3 charts (matplotlib, saved
as PNG and embedded), and a short reference list. Output formats: Markdown and PDF.

**Planted errors** (each recorded in `truth.json` with location and type):

| Type | Example |
| :- | :- |
| `sum` | a total row that is off |
| `pct_change` | growth rate computed wrong or from the wrong base |
| `pct_of` | a share that does not match its parts |
| `crossref` | the same figure printed differently in summary and table |
| `pp_vs_pct` | "rose 5%" where the data rose 5 percentage points |
| `chart_label` | a value label that disagrees with the bar it sits on |
| `chart_text` | prose that disagrees with the chart |
| `parts_sum` | pie slices that do not sum to the stated whole |
| `doi_missing` | a DOI that does not resolve (fixture-backed) |
| `misquote` | a quotation altered from its source (fixture-backed) |

**Traps** (things that look wrong and are not; the checker must *not* flag them):

- totals that differ from the sum of rounded rows only by rounding
- growth rates consistent only because operands are rounded (the 2.1M → 2.3M case)
- hedged claims ("about 14%")
- charts with a non-zero baseline, log axes, dual axes
- European number formats in an otherwise English document, when declared

## Metrics

- **Recall by error type**: planted errors that end `contradicted` (or `suspect` for
  types where rounding makes certainty impossible; report both).
- **False alarms**: `contradicted` verdicts on traps and on clean claims. Target: zero
  in the judge eval. Report the count per 1,000 claims in the end-to-end eval.
- **Coverage**: share of numeric statements that got a claim or a reasoned skip.
- **Chart reading error**: |reading midpoint − true value| as a share of axis span, and
  the share of marks whose interval contains the true value.
- **Cost**: tokens and wall time per document, per model and effort.

## Runners

```
uv run python evals/run_judge.py            # deterministic, uses gold claims.json
uv run python evals/run_e2e.py --model <id> --effort medium --n 30
```

`run_e2e.py` drives headless Claude Code (`claude -p`) with the plugin loaded, one
document per run, and stores `claims.json`, `verdicts.json`, usage and the Claude Code
and plugin versions under `evals/results/<date>-<model>-<effort>/`. Check the current
headless and model-selection flags in the docs before writing it.

Keep the end-to-end set small (30 documents) so one run is affordable. Use medium
effort for the main table; run high once to see whether it changes anything.

## What goes in the README

One table, dated, with versions:

```
Synthetic corpus v1, 30 reports, 412 planted errors, 96 traps. Run 2026-11-12.
Model            Recall   False alarms   Chart marks within interval   Tokens / doc
Fable 5.2 (med)  …        …              …                             …
Opus 5.5  (med)  …        …              …                             …
Sonnet 5.5 (med) …        …              …                             …
```

Under it, two sentences: this is our own synthetic set, and the corpus generator and
every result file are in the repo so anyone can rerun it. The per-model rows are where
readers see what Fable 5.2's chart reading adds; do not editorialise beyond the numbers.

## How it is implemented

| File | Role |
| :- | :- |
| `evals/synth/generate.py` | `build(seed, index)` makes one report in memory: Markdown, gold claims, truth. `main` also renders figures and PDFs into `evals/corpus/` (not committed; rebuild with the seed) |
| `evals/score.py` | Matches each claim to the truth by **where its target number sits in the document**, so model-written and gold claims are scored the same way |
| `evals/run_judge.py` | Gold claims of 200 synthetic reports plus the three examples. Exit code 1 on any false alarm or judge miss. Runs in CI |
| `evals/run_e2e.py` | Headless Claude Code, one document per run, in an empty folder outside the repo. `--model` is required. `--jobs`, `--resume` |
| `evals/show_transcript.py` | Prints the tool calls and errors of one run, for tightening `SKILL.md` |
| `tools/readme_table.py` | Writes the README results block from `evals/results/`; a test fails if they differ |

Corpus v1 plants these types: `sum`, `pct_change`, `pct_of`, `crossref`, `pp_vs_pct`,
`chart_label`, `chart_text`, `parts_sum` (stacked bars), `doi_missing`, `misquote`.
Traps: rounded growth rates, totals of rounded rows, hedged shares; some charts have a
non-zero baseline; one report in five uses European number formats. Pies and log axes
are covered by unit tests, not by corpus v1.

Scoring terms:

- **caught** — the planted number's claim ended `contradicted`.
- **false alarm** — `contradicted` on a trap or on a clean number.
- **knock-on flag** (`cascade`) — `contradicted` on a clean number whose derivation uses
  a planted wrong number. Reported separately: the document is inconsistent there, but
  the cause is elsewhere. The report marks these with a note.
- **numbers missed** — numeric tokens that ended in neither `numbers` nor `skipped`.

## Regression rule

Every bug report that turns out to be a wrong verdict becomes a fixture in the judge
eval before it is fixed.
