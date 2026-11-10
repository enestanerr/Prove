# Prove report — report.pdf

**3 contradicted · 0 suspect · 0 unverified · 9 verified**

- computed: 1 contradicted, 6 verified
- read from a chart or image: 1 contradicted, 1 verified
- source lookup: 1 contradicted, 2 verified

Numeric statements found: 34   checked: 23   skipped with reason: 11   missed: 0

## Contradicted (3)

**c1 · computed · page 1**
> Revenue rose from $3.17M in Q2 to $3.37M in Q3, up 0%.
Revenue growth should be the change from $3.17M to $3.37M.
`3.37M ÷ 3.17M − 1 = 6.31%; possible range 5.98%–6.64%; the document says 0%`
No rounding of the printed numbers can produce this figure.

**c8 · read from a chart or image · Figure 1 · page 2**
> Support tickets reached 553 thousand in Q3.
The prose figure for Q3 support tickets should match the Q3 bar in Figure 1.
`the Q3 bar in Figure 1 reads 725–748 (first reading 725–748, second reading 728–744); the document says 553`
The chart reading and the printed number cannot both be right.
Chart note: Bar axis starts at zero.
Chart note: Quarters are ordered Q4, Q1, Q2, Q3 on the x axis.

**s2 · source lookup · page 3** `doi: 10.5555/prove.synth.0010` — Reconciling quarterly service figures in small organisations
DOI 10.5555/prove.synth.0010 does not resolve: Crossref, DataCite and doi.org answer “not found”.

## Verified (9)

**c2 · computed · page 1**
> Occupancy rate improved from 39.5% to 41.7%, an increase of 2.2%.
The occupancy increase should be the point difference between 41.7% and 39.5%.
`41.7% − 39.5% = 2.20 pp; possible range 2.10 pp–2.30 pp; the document says 2.2%`
Recomputing from the printed numbers gives the printed figure.

**c3 · computed · page 2**
> Total 8,113
The table total should be the sum of the five regions.
`591 + 2,204 + 2,420 + 431 + 2,467 = 8,113; the document says 8,113`
Recomputing from the printed numbers gives the printed figure.

**c4 · computed · page 1**
> In total, 8,113 service calls were recorded in the quarter.
The summary total should match the table total.
`printed as 8,113 elsewhere; the document says 8,113`
Recomputing from the printed numbers gives the printed figure.

**c5 · computed · page 1**
> About 29% of service calls came from the North region.
The North share should be North calls divided by the total.
`2,467 ÷ 8,113 = 30.41%; the document says about 29%`
Recomputing from the printed numbers gives the printed figure.

**c6 · computed · page 2**
> The Valley region accounted for 27.2% of service calls.
The Valley share should be Valley calls divided by the total.
`2,204 ÷ 8,113 = 27.17%; the document says 27.2%`
Recomputing from the printed numbers gives the printed figure.

**c7 · computed · page 3**
> Total 244.4
The cost total should be the sum of the five items.
`51.0 + 47.6 + 54.1 + 61.8 + 29.9 = 244.4; possible range 244.15–244.65; the document says 244.4`
Recomputing from the printed numbers gives the printed figure.

**c9 · read from a chart or image · Figure 2 · page 3**
> Online and store sales together reached 281 thousand in the Metro area.
The Metro online and store segments should add up to the stated 281 thousand.
`the 2 segments in Figure 2 add up to 269–294; the document says 281`
The chart reading agrees with the printed number.
Chart note: Stacked bar; axis starts at zero.

**s1 · source lookup · page 3** `doi: 10.1177/1948550616673876` — The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology
DOI 10.1177/1948550616673876 resolves to “The GRIM Test” (2016), matching the cited title.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words appear on the source page.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
