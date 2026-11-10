# Prove — architecture

## One idea

```
document ──► model reads it ──► claims.json ──► provecheck ──► verdicts ──► report
             (proposes checks)                  (decides)
```

The model is good at reading and at knowing which numbers belong together. It is not
trusted with arithmetic or with the verdict. `provecheck` is deterministic: the same
`claims.json` and document always give the same report.

## Repository layout

```
prove/                              repo root
├── CLAUDE.md  PLAN.md  docs/       this package (dev instructions)
├── README.md  LICENSE  CHANGELOG.md  CONTRIBUTING.md
├── pyproject.toml                  package "provecheck", console script "provecheck"
├── .claude-plugin/
│   └── marketplace.json            marketplace "enestanerr", one plugin, source "./plugin"
├── plugin/                         PLUGIN ROOT (no CLAUDE.md here, no bin/ here)
│   ├── .claude-plugin/plugin.json
│   ├── skills/prove/
│   │   ├── SKILL.md
│   │   ├── reference/              claims-schema.md, charts.md, examples.md (loaded on demand)
│   │   └── scripts/provecheck.pyz  built artifact, committed for releases
│   └── hooks/hooks.json            v0.2, opt-in gate
├── src/provecheck/
│   ├── __main__.py  cli.py
│   ├── numbers.py                  parse printed numbers, locale, exactness
│   ├── intervals.py                Interval over Fraction; Target for hedged claims
│   ├── relations/                  one file per op (sum.py, pct_change.py, …) + registry
│   ├── grounding.py                quote/text/parse checks
│   ├── scan.py                     find every numeric token (coverage)
│   ├── verdict.py                  the rule in SPEC §2, its guards, the check pipeline
│   ├── charts.py                   two-read merge, min width, chart checks
│   ├── display.py                  exact fractions -> the text a reader sees
│   ├── sources/                    doi.py, arxiv.py, url.py, quote.py, client.py (cache)
│   ├── logic.py                    v0.2, Z3 (optional extra)
│   ├── ingest/                     text.py, markdown.py, html.py, png.py, pdf.py*, xlsx.py*  (*extras)
│   ├── report/                     html.py, md.py, card.py; __init__ builds prove.report.v1
│   └── schema/                     the validator, claims.v1.schema.json, report.v1.schema.json
├── tests/                          unit, property (Hypothesis), golden reports, fixtures/
├── evals/                          synth/generate.py, run_judge.py, run_e2e.py, score.py, results/
├── examples/                       three fictional documents with claims, truth, expected reports
├── reference/                      the tested reference of the verdict rule
└── tools/                          build_pyz.py, build_skill_zip.py, build_examples.py, mdpdf.py,
                                    readme_table.py, validate_examples.py, record_source_fixtures.py
```

Why the plugin is in `./plugin/` and not at the repo root: the repo root holds a
`CLAUDE.md` for development, and Claude Code warns about a `CLAUDE.md` at a plugin root.
Why there is no `bin/`: claude.ai and Cowork refuse plugins that ship one.

## CLI surface

```
provecheck ingest <doc> [-o doc.json] [--render-pages DIR]   text, tables, page images
provecheck scan   <doc|doc.json>                              every numeric token
provecheck text   <doc|doc.json> [--page N]                   page text, to copy quotes from
provecheck relations                                          the ops a derivation can use
provecheck check  claims.json --doc doc.json [-o verdicts.json]
provecheck crop   --doc <pdf> --page N --box x0,y0,x1,y1 --upscale 2 -o crop.png
provecheck sources claims.json [--offline]
provecheck logic  claims.json                                 v0.2
provecheck report verdicts.json [--html] [--md] [--json] [--card]
provecheck audit  <doc>                                       v0.2: all of the above with an
                                                              API key, no Claude Code needed
```

The console command is `provecheck`, not `prove`: most Unix systems already have Perl's
`prove` test runner on the PATH.

## Two ways it runs

**Skill mode (v0.1, no API key).** Inside Claude Code, Cowork or claude.ai, the skill
tells Claude to: ingest → read → write `claims.json` → run `check` → run `report` →
show the summary. Claude is the reader. `provecheck.pyz` in the skill folder is the
judge. Nothing leaves the machine except optional source lookups.

**Standalone mode (v0.2).** `provecheck audit report.pdf` calls the Anthropic API for
the reading step. Same judge. For CI and for people who do not use Claude Code.

## The zipapp

`tools/build_pyz.py` packs the stdlib-only core into `plugin/skills/prove/scripts/
provecheck.pyz` with `zipapp`. It runs with any `python3` ≥ 3.10 and needs no install,
which is what makes the skill work in sandboxes with no network. Optional features
detect their dependency at run time and say exactly what to install:

| Feature | Extra | Without it |
| :- | :- | :- |
| PDF text, tables, page images | `provecheck[pdf]` (PyMuPDF) | Claude reads the PDF with its own tools; cropping is unavailable |
| XLSX stored values and formulas | `provecheck[xlsx]` (openpyxl) | CSV/Markdown tables only |
| Logic tier | `provecheck[logic]` (z3-solver) | logic claims are `unverified` |
| Faster fuzzy quote match | `provecheck[fuzzy]` (rapidfuzz) | falls back to `difflib` |

CI fails if the `.pyz` in the repo is not what `build_pyz.py` would build from `src/`.

## Dependency policy

Core: standard library only. Dev: `pytest`, `hypothesis`, `ruff`, `jsonschema` (tests
only; the runtime validator is hand-written against the same schema so the core stays
dependency-free). Extras as listed above. Managed with `uv`.

## Testing strategy

| Layer | What | How |
| :- | :- | :- |
| Rule | SPEC §2 | `reference/test_reference.py` ported to pytest; must stay 10/10 |
| Arithmetic | interval ops, each relation | Hypothesis: the point is always inside the range; widening an operand never shrinks the range; exact operands give a zero-width range |
| Parsing | numbers, locales, suffixes | table-driven tests + Hypothesis round-trips |
| Grounding | quote / text / parse mismatch | fixtures with deliberately altered numbers |
| Golden | whole pipeline from a fixed `claims.json` | byte-stable `report.json` snapshots |
| Sources | resolvers | recorded HTTP fixtures, no network in CI |
| End to end | model writes the claims | `evals/`, run by hand, results committed (see `docs/EVALS.md`) |

## CI and release

- GitHub Actions: tests on Python 3.10–3.13 (Linux, macOS, Windows), ruff, pyz
  freshness, schema validation of `examples/` and `reference/`.
- Release: tag `vX.Y.Z` → build → PyPI via trusted publishing → GitHub release with
  `prove-skill.zip` (the `plugin/skills/prove` folder) attached for claude.ai uploads.
- `plugin.json` `version` is bumped in the same commit as `pyproject.toml`.

## Contribution surface (designed in from day one)

Each of these is a single-file, single-test pull request. Seed the issue tracker with
them as "good first issue" at launch:

- a new relation (`median`, `weighted_mean`, `unit_convert`, `date_diff`)
- a new source resolver (PubMed, OpenAlex, CourtListener, SEC EDGAR, ISBN)
- a new number format or locale (Indian lakh/crore, Swiss apostrophes, Arabic-Indic digits)
- a new ingest format (DOCX, PPTX, ODS, LaTeX)
- a new example document with an expected report
