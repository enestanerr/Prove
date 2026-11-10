# Prove — specification (v1)

This is the contract between the model (which reads the document and proposes checks)
and `provecheck` (which decides). If code and this file disagree, one of them is a bug.

## 1. Vocabulary

| Term | Meaning |
| :- | :- |
| **printed number** | A number exactly as it appears in the document, e.g. `2.1M`, `4,812`, `14%` |
| **claim** | A statement that a printed number should equal something checkable |
| **derivation** | A small expression tree saying how the claimed number should be computed |
| **verdict** | What `provecheck` concluded about one claim |
| **assurance** | How the verdict was reached: `computed`, `read`, `resolved`, `proved` |

## 2. The verdict rule

A printed number is a rounded view of a true value. `2.1M` means the true value lies in
`[2.05M, 2.15M]`. Every printed number therefore carries an interval:

```
half_unit = scale / (2 * 10**decimals)        # 2.1M -> 1e6 / 20 = 50,000
interval  = [point - half_unit, point + half_unit]   (closed)
exact numbers: interval = [point, point]
```

Evaluate the derivation twice: once on the printed points (the **point**), once with
interval arithmetic on the operands' intervals (the **range**). Then:

| Verdict | Condition | Meaning |
| :- | :- | :- |
| `verified` | point lies inside the claim's interval | Recomputing from what is printed gives what is printed |
| `contradicted` | claim's interval and the range do not overlap | No true values behind the printed operands can produce the claim |
| `suspect` | neither of the above | Possible only if operands sit at the edge of their rounding |
| `unverified` | no derivation, operand not grounded, parse mismatch, unit or scale mix-up, division by an interval containing zero, offline | Not checked. Never shown as an error |
| `skipped` | number is not a quantity to check (a year, a page number, a phone number) | Listed with the reason |

Worked examples. These eight, plus a locale case and a chart case, are executable in
`reference/test_reference.py`:

| Document says | Point | Range | Verdict |
| :- | :- | :- | :- |
| from 2.1M to 2.3M, "up 14%" | 9.52% | 4.65% .. 14.63% | `suspect` |
| from 2.10M to 2.30M, "up 14%" | 9.52% | 9.03% .. 10.02% | `contradicted` |
| from 165 to 186, "up 12.7%" | 12.73% | — | `verified` |
| exact rows sum to 4,792; total prints 4,812 | 4,792 | 4,792 | `contradicted` |
| 20 rounded rows sum to 4,792; total prints 4,812 | 4,792 | 4,782 .. 4,802 | `contradicted` |
| 45 rounded rows sum to 4,792; total prints 4,812 | 4,792 | 4,769.5 .. 4,814.5 | `suspect` |
| 33.3% + 33.3% + 33.3% = "100%" | 99.9 | — | `verified` |
| 1,356 of 4,792 is "28.3%" | 28.30% | — | `verified` |

The first row is the reason this rule exists. A naive checker recomputes 9.5%, sees 14%
and reports an error. But 2.05M → 2.349M is a 14.6% rise and both print as "2.1M" and
"2.3M". Prove says `suspect` and shows the range. It says `contradicted` only in the
second row, where two decimals leave no room.

Prior art for this style of reasoning: the GRIM test (Brown & Heathers) and statcheck
(Nuijten & Epskamp). Credit them in the README.

### 2.1 Guards

A claims file can be wrong in ways that have nothing to do with the document. Each guard
below turns a would-be `contradicted` into something weaker. No guard ever produces
`contradicted`, and none changes a `verified`.

| Guard | When | Result |
| :- | :- | :- |
| Round figure (§3.2) | the claim stops being contradicted if a number such as `2,300,000` is read as rounded to its last non-zero digit | `suspect`, with a note |
| Unit mismatch | the target is a percentage and the derivation gives a plain number, or the reverse; or percentages and plain numbers are mixed in a sum | `unverified`, reason `unit-mismatch` |
| Scale mismatch | the two sides agree after multiplying by 10³, 10⁶ or 10⁹ (thousands vs millions) | `unverified`, reason `scale-mismatch` |
| Ambiguous format (§3.1) | the claim would be verified if like-formatted numbers were read with the other decimal separator | `unverified`, reason `ambiguous-format` |
| Read from an image (§6) | an operand or the target was not grounded in text | `suspect`, assurance `read` |

The scale guard is skipped when the claim's interval contains zero and for one-sided
hedges, where "agrees after scaling" has no meaning.

When a flagged claim uses a number that another claim contradicts (a share computed
from a wrong total), the report says so in a note. The verdict is not changed.

## 3. Printed numbers

### 3.1 Parsing (deterministic, in `provecheck`)

- Signs `-`, `+`, `−`; accounting negatives `(1,234)`; currency symbols and codes are
  ignored for value.
- The percent sign may follow or precede the number (`14%`, Turkish `%14`, `yüzde 14`).
  `pp` marks percentage points.
- Suffixes: `%`, `pp`, `percent`, `k`, `K`, `M`, `m`, `mn`, `B`, `b`, `bn`, `tn`,
  `thousand`, `million`, `billion`, `trillion`, and Turkish `bin`, `milyon`, `milyar`,
  `trilyon`. Unknown suffix → parse error → `unverified`.
- `decimals` = digits printed after the decimal separator of the mantissa.
- Locale decides separators. `en`: `1,234.5`. `eu` (tr, de, fr, es, it, …): `1.234,5`.
  Spaces and apostrophes group digits in both. Groups must be thousands groups; a
  leading zero group (`0.766` read as 766) is not a number.
- The document declares one locale; a number may override it with `locale`.
- **Ambiguity.** `1,234` is 1234 in `en` and 1.234 in `eu`. It is read by the document
  locale. If a claim would be `contradicted` but is `verified` when the ambiguous
  numbers that are written alike are read the other way, the verdict is `unverified`,
  reason `ambiguous-format`. Numbers are re-read in groups (all, those read as
  thousands, those read as decimals), never one among like-formatted ones, and a
  `count` is never re-read as a fraction.
- **Context scale.** A table headed "USD thousands" gives its numbers `"scale": "1000"`.
  The value and the half-unit are multiplied by it.
- The model also sends `value` and `decimals`. `provecheck` parses `text` itself and
  compares. Disagreement → `unverified` with reason `parse-mismatch`; text that cannot
  be parsed → `parse-error`.

### 3.2 Exact vs rounded

Default: every printed number is **rounded to what is printed**. A number is `exact`
only when the model marks it and gives a reason from this list:

- `count` — discrete items (people, orders, rows)
- `ledger` — currency printed to its minor unit (cents, kuruş)
- `defined` — a constant or a definition (100%, 12 months, a stated threshold)
- `cell` — a spreadsheet cell whose stored value was read from the file, not the display

Default-rounded is the conservative choice: it can only move a verdict from
`contradicted` toward `suspect`.

**Round figures.** A whole number that ends in two or more zeros and is not marked
exact (`2,300,000`, `500`, `200M`) may have been rounded to its last non-zero digit.
The verdict rule uses the printed precision as above. Only if the result is
`contradicted` is the claim re-evaluated with such numbers read widely (`2,300,000` as
`[2.25M, 2.35M]`); if it is then no longer contradicted, the verdict is `suspect` with a
note. Percentages are never treated this way, and one trailing zero (`240`) is not
enough.

### 3.3 Hedges

| `hedge` | Trigger words | Claim interval becomes |
| :- | :- | :- |
| `approx` | about, around, roughly, nearly, almost, ~, yaklaşık | widened by max(one printed unit, 5% of the value) on each side |
| `over` / `under` | over, more than / under, less than | open-ended on one side from the printed point |
| `at_least` / `at_most` | at least / at most, up to | closed one-sided |

## 4. Relations (v1)

Each relation lives in `src/provecheck/relations/<name>.py` with its own tests.

| `op` | Args | Value |
| :- | :- | :- |
| `eq` | b (or target, b) | b (cross-reference: the same quantity printed in two places) |
| `sum` | a… | a₁ + … + aₙ |
| `diff` | a, b | a − b |
| `product` | a… | a₁ × … × aₙ |
| `ratio` | a, b | a / b |
| `pct_of` | part, whole | part / whole × 100 |
| `pct_change` | old, new | (new / old − 1) × 100 |
| `pp_diff` | a%, b% | a − b in percentage points |
| `mean` | a… | sum / n |
| `cagr` | start, end, years | ((end / start)^(1/years) − 1) × 100 |
| `max` / `min` | a… | largest / smallest |
| `rank` | item, a…, position | the item's place among the values; 1 = largest, −1 = smallest |

Args are `{"ref": "<number id>"}`, `{"const": "<decimal string>"}` (or `"100%"`), or a
nested `{"op": …, "args": […]}`. There is no free-form expression string and no `eval`.
`cagr` is the one relation that leaves exact rationals; evaluate it with `decimal` at 50
digits and widen the range outward by one unit in the last place.

Notes:

- **Kinds.** A value is a percentage or a plain number. `pct_of`, `pct_change`, `cagr`
  and `pp_diff` give percentages; `ratio` gives a plain number; `sum`, `diff`, `mean`,
  `max`, `min` and `eq` keep the kind of their operands, which must agree. In `product`
  and `ratio` a percentage operand counts as a fraction (20% × 500 = 100). The target's
  kind must match the result, otherwise `unit-mismatch`.
- **`eq` is symmetric.** Two prints of one quantity agree when either one rounds to the
  other: `2.3M` and `2,304,112` are `verified` whichever is the target.
- **`rank`** needs no printed target: its last argument is the claimed position.

## 5. The claims file

`claims.json` is written by the model and read by `provecheck check`.

```json
{
  "schema": "prove.claims.v1",
  "document": {"path": "report.pdf", "sha256": "…", "locale": "en"},
  "numbers": [
    {"id": "n1", "text": "2.10M", "value": "2100000", "decimals": 2, "unit": "USD",
     "exact": null, "loc": {"page": 3, "quote": "revenue rose from $2.10M to $2.30M"}}
  ],
  "claims": [
    {"id": "c1", "kind": "derived", "target": "n3", "hedge": null,
     "derivation": {"op": "pct_change", "args": [{"ref": "n1"}, {"ref": "n2"}]},
     "say": "Revenue growth should be the change from $2.10M to $2.30M."}
  ],
  "charts": [],
  "sources": [],
  "skipped": [
    {"text": "2026", "loc": {"page": 1, "quote": "Q3 2026 report"}, "reason": "year"}
  ]
}
```

A complete, valid example is in `reference/claims.example.json`. The JSON Schema is at
`src/provecheck/schema/claims.v1.schema.json`; the runtime validator is hand-written
against it so the core stays dependency-free, and it also checks what a schema cannot
(ids exist, ops are known, argument counts).

Optional number fields: `scale` (§3.1), `locale` (§3.1), `loc.image` (§6). A `unit` of
`%` or `pp` marks a bare number as a percentage.

`say` is one plain sentence the report shows to the reader. It is the model's
explanation of the check, never of the verdict.

## 6. Grounding

Before any arithmetic, for every number:

1. `loc.quote` must occur in the extracted text of `loc.page`.
2. `text` must occur inside `loc.quote`.
3. Parsing `text` must agree with `value` and `decimals` (§3.1).

Any failure → every claim that uses the number is `unverified`, reason `not-grounded`
(or `parse-mismatch` / `parse-error` for step 3). This is what stops a model from
"fixing" a number on the way in.

Matching is case-sensitive, after Unicode NFKC and a normalisation that forgives
typography only: whitespace is collapsed, curly quotes and dash variants are unified,
table pipes count as spaces, Markdown `*` and backticks are dropped. Digits are never
forgiven. A quote found on another page is still a failure; the message says where it
was found.

Numbers without text to check against carry `assurance: read` and can never produce
`contradicted` in a derived claim:

- a page with no text layer (a scan), unless `provecheck ingest` produced OCR text;
- a number printed inside a figure, marked `"loc": {…, "image": true}`;
- every number, when no document text is given to `check` at all.

## 7. Coverage

`provecheck scan <doc>` lists every numeric token in the document with its location,
using the deterministic parser. `provecheck check` then requires that each token is
either a `numbers[]` entry or a `skipped[]` entry with a reason. The report prints:

```
Numeric statements found: 212   checked: 171   skipped with reason: 33   missed: 8
```

`missed` > 0 is shown prominently. The skill tells the model to go back for them.

A word that starts with a letter and runs into digits (`Q3`, `FY2026`, `COVID-19`,
`v0.1`) is an identifier and ordinals (`1st`) are not quantities; neither is a token.

A `skipped[]` entry is one of: `text` with `loc.quote` (one occurrence); `text` alone,
optionally with `loc.page` (that token everywhere, or on that page); `loc.quote` with no
`text` (every number inside the quoted passage, for a reference list or a phone block).

## 8. Charts

The model reads a chart from the page image and writes what it sees. `provecheck`
compares readings to printed numbers. Assurance is `read`, not `computed`.

```json
{"id": "g1", "loc": {"page": 5, "figure": "Figure 2"}, "type": "bar",
 "y_axis": {"min": "0", "max": "400", "scale": "linear", "unit": "k"},
 "marks": [
   {"label": "Q3", "series": "Revenue",
    "read_a": {"lo": "300", "hi": "320"}, "read_b": {"lo": "302", "hi": "318"},
    "printed_label": "n44"}
 ],
 "notes": ["bar axis starts at 0"]}
```

A chart check is a claim with `kind: "chart"`, a `check` name from the list below, the
printed number it concerns (`target`), and the chart and mark it points at. See `c4` in
`reference/claims.example.json`.

Rules:

- **Two reads.** `read_a` from the whole figure. `read_b` after
  `provecheck crop --page 5 --box … --upscale 2`. If the two intervals do not overlap,
  the mark is `unstable` and every check on it is `unverified`. A mark read only once
  is `unverified` too (`single-read`).
- **Final reading** = the union of the two intervals (wider is safer).
- **Minimum width.** A reading narrower than 2% of the axis span is widened to 2%. On a
  log axis the span is measured in log space.
- **Axis.** `y_axis.min` and `max` are in axis units. A pie has no axis; its slices are
  read as percentages of the whole. `y_axis.multiplier` converts axis units to the
  units of the printed number when they differ (an axis in thousands against a full
  number).
- **Checks**
  - `label_vs_mark` — a value printed on or beside the mark vs the mark's reading
  - `text_vs_chart` — a number in the prose that the chart depicts
  - `table_vs_chart` — a table cell that the chart depicts
  - `parts_sum` — pie slices or stacked segments vs their stated total (`marks` lists
    them; default: every mark of the chart)
  - `order` — `relation` is `largest`, `smallest`, or `gt` / `lt` with a second mark in
    `than`
- **Verdicts.** `contradicted` only when the printed number's interval and the final
  reading are disjoint. Otherwise `verified` (overlap) or `unverified` (unstable). An
  ordering claim is `contradicted` only when the readings rule it out. The round-figure
  and scale guards of §2.1 apply; the scale guard also catches a share axis (0–1)
  against a percentage.
- **Notes, not verdicts.** A bar chart whose axis does not start at zero, a dual axis,
  a log scale without a label: reported as notes for the reader. They are not errors.

## 9. Sources

```json
{"id": "s1", "kind": "doi", "value": "10.1234/abcd", "cited_title": "…",
 "cited_year": 2021, "quote": null, "loc": {"page": 9, "quote": "[7] …"}}
```

| `kind` | Check | `verified` when | `contradicted` when |
| :- | :- | :- | :- |
| `doi` | Crossref, then DataCite, then doi.org | it resolves and the title matches (≥ 0.85 similarity) | all three answer "not found", or it resolves to a clearly different work (< 0.5 similarity) |
| `arxiv` | arXiv API | id exists and title matches | id does not exist |
| `url` | HTTP GET, follow redirects | 2xx | 404 / 410 |
| `quote` | fetch the source, normalise, search | the quoted words appear | the source loads with real text and holds a passage close to the quote but not the same |

Everything else (timeouts, paywalls, 403, offline, a title that is similar but not the
same, a page that loads without anything like the quote) is `unverified`. Assurance
`resolved`. A cited title that is the start of the registered one (the subtitle left
out) counts as a match. Wording in the report is factual: "DOI does not resolve", never
"fabricated". Resolvers live in `src/provecheck/sources/<kind>.py`; network calls go
through one client with a polite User-Agent, a timeout and an on-disk cache.

## 10. Logic (v0.2)

For stated rules and a conclusion drawn from them (eligibility rules, pricing tiers,
scheduling constraints, permission rules):

```json
{"id": "l1", "plain": "Orders over $50 ship free; members always ship free. So a
  non-member with a $50 order pays shipping.",
 "smtlib": "(declare-const total Real) … (assert (not conclusion))",
 "expect": "unsat"}
```

`provecheck logic` runs Z3. `unsat` on the negated conclusion → `verified`, assurance
`proved`. `sat` → `contradicted`, with the counterexample model printed in plain words.
Also check that the rules alone are satisfiable; if not, report "the rules contradict
each other". The formalisation is the model's; the report always shows `plain` next to
the SMT so a reader can judge whether it is faithful. `z3-solver` is an optional extra.

## 11. Outputs

- `prove-report.html` — one self-contained file, no external requests. Summary counts,
  coverage line, then claims grouped `contradicted` → `suspect` → `unverified` →
  `verified`. Each card: the quote and location, `say`, the computation written out,
  point and range, verdict, assurance tag.
- `prove-report.md` — the same, compact, for pasting into chat or a pull request.
- `prove-report.json` — machine-readable, schema `prove.report.v1`.
- `prove-card.svg` — a small shareable scorecard (counts only, no document content).
- Exit codes of `provecheck report`: `0` nothing contradicted, `1` at least one
  `contradicted`, `2` usage or input error. `--fail-on suspect` tightens it for CI;
  `--fail-on never` turns it off. `provecheck check` exits `0` when it wrote verdicts
  and `2` on a usage or input error, including an invalid claims file.
- Summary counts are also given per assurance tag, so verdicts that rest on a chart
  reading or a source lookup are never mixed with computed ones in a headline.

## 12. What Prove does not claim

- It does not judge opinions, forecasts or strategy.
- It does not know whether a source is right, only whether it exists and says what is
  quoted.
- A clean report means the checked claims passed. The coverage line says how many were
  checked. The report says this in its footer, every time.
