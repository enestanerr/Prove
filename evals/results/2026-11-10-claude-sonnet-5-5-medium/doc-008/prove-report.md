# Prove report — report.pdf

**3 contradicted · 1 suspect · 0 unverified · 8 verified**

- computed: 1 contradicted, 1 suspect, 5 verified
- read from a chart or image: 1 contradicted, 1 verified
- source lookup: 1 contradicted, 2 verified

Numeric statements found: 36   checked: 21   skipped with reason: 15   missed: 0

## Contradicted (3)

**c6 · computed · page 2**
> The Highland region accounted for 28.5% of shipments.
Highland's share should be Highland shipments over the total.
`1,532 ÷ 6,505 = 23.55%; the document says 28.5%`
No rounding of the printed numbers can produce this figure.

**c8 · read from a chart or image · Figure 1 · page 2**
> Training hours reached 1 thousand in Jun.
The prose figure for June training hours should match the June point in Figure 1.
`the Jun point in Figure 1 reads 190–215 (first reading 190–215, second reading 195–210); the document says 1 thousand`
The chart reading and the printed number cannot both be right.

**s2 · source lookup · page 3** `doi: 10.5555/prove.synth.0008` — Reconciling quarterly service figures in small organisations
DOI 10.5555/prove.synth.0008 does not resolve: Crossref, DataCite and doi.org answer “not found”.

## Suspect (1)

**c1 · computed · page 1**
> Revenue rose from $3.0M in Q2 to $3.4M in Q3, up 11%.
Revenue growth should be the change from $3.0M to $3.4M.
`$3.4M ÷ $3.0M − 1 = 13.33%; possible range 9.84%–16.95%; the document says 11%`
Possible only if the inputs sit at the edge of their rounding.

## Verified (8)

**c2 · computed · page 1**
> On-time rate improved from 31.3% to 33.2%, an increase of 1.9%.
The on-time improvement in points should be 33.2% minus 31.3%.
`33.2% − 31.3% = 1.90 pp; possible range 1.80 pp–2.00 pp; the document says 1.9%`
Recomputing from the printed numbers gives the printed figure.

**c3 · computed · page 1**
> In total, 6,505 shipments were recorded in the quarter.
Total shipments should be the sum of the five regions.
`1,872 + 1,978 + 569 + 554 + 1,532 = 6,505; the document says 6,505`
Recomputing from the printed numbers gives the printed figure.

**c4 · computed · page 2**
> Total 6,505 The Highland
The table total should be the sum of the five regions.
`1,872 + 1,978 + 569 + 554 + 1,532 = 6,505; the document says 6,505`
Recomputing from the printed numbers gives the printed figure.

**c5 · computed · page 1**
> About 9% of shipments came from the North region.
North's share should be North shipments over the total.
`569 ÷ 6,505 = 8.75%; the document says about 9%`
Recomputing from the printed numbers gives the printed figure.

**c7 · computed · page 3**
> Total 84.8 Figure 2
The cost total should be rent plus staff plus travel.
`46.5 + 20.8 + 17.5 = 84.8; possible range 84.65–84.95; the document says 84.8`
Recomputing from the printed numbers gives the printed figure.

**c9 · read from a chart or image · Figure 2 · page 3**
> Online and store sales together reached 171 thousand in the Suburban area.
Suburban online plus store sales should match the stated 171 thousand.
`the 2 segments in Figure 2 add up to 160–182; the document says 171 thousand`
The chart reading agrees with the printed number.
Chart note: Stacked bars; each segment read as its own height.

**s1 · source lookup · page 3** `doi: 10.3758/s13428-015-0664-2` — The prevalence of statistical reporting errors in psychology (1985-2013)
DOI 10.3758/s13428-015-0664-2 resolves to “The prevalence of statistical reporting errors in psychology (1985–2013)” (2015), matching the cited title.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words appear on the source page.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
