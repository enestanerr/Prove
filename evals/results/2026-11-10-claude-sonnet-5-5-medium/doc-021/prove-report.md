# Prove report — report.pdf

**2 contradicted · 1 suspect · 0 unverified · 9 verified**

- computed: 1 contradicted, 1 suspect, 5 verified
- read from a chart or image: 2 verified
- source lookup: 1 contradicted, 2 verified

Numeric statements found: 31   checked: 20   skipped with reason: 11   missed: 0

## Contradicted (2)

**c6 · computed · page 2**
> The Central region accounted for 25.7% of shipments.
Central share should be Central shipments over the total.
`1,241 ÷ 5,716 = 21.71%; the document says 25.7%`
No rounding of the printed numbers can produce this figure.

**s2 · source lookup · page 3** `doi: 10.5555/prove.synth.0021` — Reconciling quarterly service figures in small organisations
DOI 10.5555/prove.synth.0021 does not resolve: Crossref, DataCite and doi.org answer “not found”.

## Suspect (1)

**c1 · computed · page 1**
> Revenue rose from $3.6M in Q2 to $4.2M in Q3, up 15%.
Revenue growth should be the change from $3.6M to $4.2M.
`4.2M ÷ 3.6M − 1 = 16.67%; possible range 13.70%–19.72%; the document says 15%`
Possible only if the inputs sit at the edge of their rounding.

## Verified (9)

**c2 · computed · page 1**
> Occupancy rate improved from 31.3% to 36.5%, an increase of 5.2%.
The occupancy increase should be the gap in points between 36.5% and 31.3%.
`36.5% − 31.3% = 5.20 pp; possible range 5.10 pp–5.30 pp; the document says 5.2%`
Recomputing from the printed numbers gives the printed figure.

**c3 · computed · page 2**
> Total 5,716
The table total should be the sum of the four regions.
`2,465 + 636 + 1,374 + 1,241 = 5,716; the document says 5,716`
Recomputing from the printed numbers gives the printed figure.

**c4 · computed · page 1**
> In total, 5,716 shipments were recorded in the quarter.
The summary total should equal the table total.
`printed as 5,716 elsewhere; the document says 5,716`
Recomputing from the printed numbers gives the printed figure.

**c5 · computed · page 1**
> About 11% of shipments came from the West region.
West share should be West shipments over the total.
`636 ÷ 5,716 = 11.13%; the document says about 11%`
Recomputing from the printed numbers gives the printed figure.

**c7 · computed · page 3**
> Total 214.0
The cost total should be the sum of the three items.
`41.6 + 86.8 + 85.6 = 214; possible range 213.85–214.15; the document says 214.0`
Recomputing from the printed numbers gives the printed figure.

**c8 · read from a chart or image · Figure 1 · page 2**
> Support tickets reached 831 thousand in Q4.
The 831 thousand in the text should match the Q4 bar in Figure 1.
`the Q4 bar in Figure 1 reads 818–845 (first reading 818–845, second reading 822–840); the document says 831`
The chart reading agrees with the printed number.
Chart note: Quarter order on the x axis is Q4, Q1, Q2, Q3.

**c9 · read from a chart or image · Figure 2 · page 3**
> together reached 239 thousand in the Metro area.
The Metro Online and Stores segments should add up to 239 thousand.
`the 2 segments in Figure 2 add up to 228–251; the document says 239`
The chart reading agrees with the printed number.

**s1 · source lookup · page 3** `doi: 10.1177/1948550616673876` — The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology
DOI 10.1177/1948550616673876 resolves to “The GRIM Test” (2016), matching the cited title.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words appear on the source page.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
