# The claims file

`claims.json` is what you write and what `provecheck check` judges. Schema name:
`prove.claims.v1`. Everything in it must be traceable to the document.

```json
{
  "schema": "prove.claims.v1",
  "document": {"path": "report.pdf", "locale": "en"},
  "numbers": [],
  "claims": [],
  "charts": [],
  "sources": [],
  "skipped": []
}
```

`document.locale` is the number format of the document: `en` for `1,234.5`; `tr`, `de`,
`fr`, `es`, `it` (any of them means "European") for `1.234,5`.

## numbers

One entry per printed number you use, as a target or as an input.

```json
{"id": "n1", "text": "2.10M", "value": "2100000", "decimals": 2, "unit": "USD",
 "exact": null, "loc": {"page": 3, "quote": "revenue rose from $2.10M to $2.30M"}}
```

| Field | Rule |
| :- | :- |
| `text` | The number exactly as printed, with its suffix or percent sign: `2.10M`, `4,812`, `14%`, `%14`, `2,1 milyon`, `(1,234)`. No currency symbol needed. |
| `value` | What `text` means, as a plain decimal string: `"2100000"`, `"28.3"`, `"-1234"`. A percentage keeps its number: `14%` is `"14"`. |
| `decimals` | Digits printed after the decimal separator: `2.10M` is 2, `14%` is 0. |
| `unit` | Free text for the reader. `"%"` or `"pp"` here marks a bare number as a percentage ("a gain of 2.5 points"). |
| `exact` | `null` (rounded, the default) or the reason it is exact: `count` (people, orders, rows), `ledger` (money printed to the cent), `defined` (100%, 12 months, a stated threshold), `cell` (a stored spreadsheet value). |
| `scale` | Only when the multiplier is in the context, not in `text`: a table headed "USD thousands" gives `"scale": "1000"`. Then `value` is the scaled value. |
| `locale` | Only for a number written in the other format than the document's. |
| `loc.page` | Page in `doc.json`, from 1. Markdown is split into pages at `---`. |
| `loc.quote` | A short passage copied from the page that contains `text`: the sentence, or `Label | value` for a table row. It must be unique enough to find. |
| `loc.image` | `true` only for a number printed inside a figure and absent from the page text (see `charts.md`). |

`provecheck` parses `text` itself and compares with `value` and `decimals`. It also
looks for `quote` on the page and for `text` inside `quote`. Whitespace, curly quotes,
dash variants, table pipes and Markdown `*` are forgiven. Digits are not.

Leave a number rounded when unsure. Marking a rounded number `exact` is the one way to
cause a false alarm.

## claims

### Derived numbers

```json
{"id": "c1", "kind": "derived", "target": "n3", "hedge": null,
 "derivation": {"op": "pct_change", "args": [{"ref": "n1"}, {"ref": "n2"}]},
 "say": "Revenue growth should be the change from $2.10M to $2.30M."}
```

- `target` — the printed number being checked.
- `derivation` — how it should be computed. An argument is `{"ref": "n1"}`,
  `{"const": "12"}` (or `"100%"`), or a nested `{"op": …, "args": […]}`.
- `say` — one plain sentence about the check for the reader. Never about the verdict.
- `hedge` — `null`, or the hedge word printed with the number:
  `approx` (about, around, roughly, nearly, ~, yaklaşık), `over` (over, more than),
  `under` (under, less than), `at_least`, `at_most` (up to).

| `op` | Args | Value |
| :- | :- | :- |
| `eq` | b | the same quantity printed elsewhere (a cross-reference) |
| `sum` | a… | a₁ + … + aₙ |
| `diff` | a, b | a − b |
| `product` | a… | a₁ × … × aₙ; a percentage counts as a fraction, so 20% × 500 = 100 |
| `ratio` | a, b | a ÷ b as a plain multiple ("3.2 times") |
| `pct_of` | part, whole | part ÷ whole × 100, a percentage |
| `pct_change` | old, new | (new ÷ old − 1) × 100, a percentage |
| `pp_diff` | a%, b% | a − b in percentage points |
| `mean` | a… | sum ÷ n |
| `cagr` | start, end, years | ((end ÷ start)^(1 ÷ years) − 1) × 100 |
| `max` / `min` | a… | largest / smallest |
| `rank` | item, others…, position | place of the item, 1 = largest, −1 = smallest. No `target`; the position is a `const`. |

`PROVE relations` prints this list. There is no free-form expression.

Units must agree. A percentage target needs a percentage result (`pct_of`, not
`ratio`). Operands of `sum`, `diff`, `mean` must all be percentages or all plain.
"Rose 5%" is `pct_change`; "rose 5 points" is `pp_diff`. Use the one the sentence says.

### Charts

See `charts.md`. A chart claim points at a chart in `charts` and a mark in it.

## sources

```json
{"id": "s1", "kind": "doi", "value": "10.1234/abcd", "cited_title": "…",
 "cited_year": 2021, "quote": null, "loc": {"page": 9, "quote": "[7] …"}}
```

`kind` is `doi`, `arxiv` (value like `2605.06021`), `url`, or `quote`. For `quote`,
`value` is the URL of the source and `quote` holds the quoted words exactly.

## skipped

Every numeric token that `PROVE scan` lists and that is not in `numbers` goes here.

```json
{"text": "2026", "loc": {"page": 1, "quote": "Q3 2026 report"}, "reason": "year"}
{"text": "2026", "reason": "year"}
{"loc": {"page": 9, "quote": "[7] Smith (2021). Journal 12(3), 45-67."}, "reason": "reference list"}
```

The first skips one occurrence. The second skips that token everywhere (add
`"loc": {"page": 4}` to limit it to a page). The third, with no `text`, skips every
number inside the quoted passage. Typical reasons: year, date, page number, section
number, figure number, phone number, identifier, reference list, axis tick.

## When `check` says a claim is unverified

| Reason | What it means | What to do |
| :- | :- | :- |
| `not-grounded` | The quote is not on that page, or `text` is not in the quote | Copy the quote from `doc.json`; fix the page. Never change the number. |
| `parse-mismatch` | `value` or `decimals` disagree with `text` | Correct `value` / `decimals` to what `text` says |
| `parse-error` | `text` is not a number `provecheck` can read | Trim `text` to the number and its suffix |
| `unit-mismatch` | A percentage is compared with a plain number | Use the right op, or set `unit` |
| `scale-mismatch` | The two sides differ by exactly 1,000 or 1,000,000 | Add `scale` to the numbers printed in thousands or millions |
| `ambiguous-format` | `1,234` could be 1234 or 1.234 | Set the number's `locale` |
| `division-by-zero` | A divisor could be zero within its rounding | Nothing; it stays unverified |

If the cause is in the document rather than in your file, leave it. Unverified is an
honest result.
