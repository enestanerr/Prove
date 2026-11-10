# Changelog

## 0.1.0 (unreleased)

First version.

**The judge (`provecheck`, standard library only)**

- Interval arithmetic over exact fractions; every printed number carries the interval
  its rounding allows.
- The verdict rule of `docs/SPEC.md` §2: `verified`, `contradicted`, `suspect`,
  `unverified`. `contradicted` means impossible under any rounding of what is printed.
- Printed-number parser: signs, currency, suffixes (`k`, `M`, `bn`, `million`, …),
  percentages before or after the number, English and European formats, Turkish forms
  (`2,1 milyon`, `%14`), context scale for tables in thousands or millions.
- Thirteen relations, one file each: `eq`, `sum`, `diff`, `product`, `ratio`, `pct_of`,
  `pct_change`, `pp_diff`, `mean`, `cagr`, `max`, `min`, `rank`.
- Grounding: a number must be found, as printed, in the quote and on the page the claims
  file gives.
- Coverage: every numeric token in the document is checked, skipped with a reason, or
  reported as missed.
- Guards that only ever move a verdict away from `contradicted`: round figures, unit
  and scale mix-ups, ambiguous number formats, numbers read from an image. A note when
  a flagged claim leans on a number another claim contradicts.
- Hedges: about, over, under, at least, at most.

**Charts**

- Two-read protocol with a minimum width of 2% of the axis span; unstable and
  single readings end `unverified`.
- Checks: `label_vs_mark`, `text_vs_chart`, `table_vs_chart`, `parts_sum`, `order`.
- `provecheck crop` for PDF pages and images, with a dependency-free path for PNG.

**Sources**

- DOI (Crossref, DataCite, doi.org), arXiv, URL and quotation checks through one HTTP
  client with a cache and an offline mode. Wording is factual.

**In and out**

- Ingest: text, Markdown, HTML, CSV, and PDF with the `pdf` extra.
- Reports: self-contained HTML, Markdown, JSON (`prove.report.v1`) and an SVG card.
- Exit codes for CI.

**Skill and plugin**

- `plugin/` with the `prove` skill, its reference files and the `provecheck.pyz`
  zipapp; a marketplace entry at the repo root.

**Evals**

- A seeded synthetic corpus with planted errors and traps, a deterministic judge eval
  that gates CI on zero false alarms, and an end-to-end runner for headless Claude Code.
