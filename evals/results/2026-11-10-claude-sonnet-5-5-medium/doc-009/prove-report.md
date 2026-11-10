# Prove report — report.pdf

**2 contradicted · 1 suspect · 0 unverified · 9 verified**

- computed: 1 contradicted, 1 suspect, 5 verified
- read from a chart or image: 2 verified
- source lookup: 1 contradicted, 2 verified

Numeric statements found: 37   checked: 20   skipped with reason: 17   missed: 0

## Contradicted (2)

**c6 · computed · page 2**
> The Valley region accounted for 26,1% of shipments.
Valley's share should be Valley shipments over the total.
`1.485 ÷ 7.277 = 20.41%; the document says 26,1%`
No rounding of the printed numbers can produce this figure.

**s2 · source lookup · page 3** `doi: 10.5555/prove.synth.0009` — Reconciling quarterly service figures in small organisations
DOI 10.5555/prove.synth.0009 does not resolve: Crossref, DataCite and doi.org answer “not found”.

## Suspect (1)

**c1 · computed · page 1**
> Revenue rose from €5,6M in Q2 to €6,0M in Q3, up 6%.
Revenue growth should be the change from 5,6M to 6,0M.
`6,0M ÷ 5,6M − 1 = 7.14%; possible range 5.31%–9.01%; the document says 6%`
Possible only if the inputs sit at the edge of their rounding.

## Verified (9)

**c2 · computed · page 1**
> Retention rate improved from 54,6% to 60,4%, a gain of 5,8 percentage points.
The retention gain should be 60,4% minus 54,6% in points.
`60,4% − 54,6% = 5.80 pp; possible range 5.70 pp–5.90 pp; the document says 5,8 pp`
Recomputing from the printed numbers gives the printed figure.

**c3 · computed · page 2**
> Total 7.277
The table total should be the sum of the four regions.
`2.470 + 2.226 + 1.485 + 1.096 = 7,277; the document says 7.277`
Recomputing from the printed numbers gives the printed figure.

**c4 · computed · page 1**
> In total, 7.277 shipments were recorded in the quarter.
The summary total should equal the table total.
`printed as 7.277 elsewhere; the document says 7.277`
Recomputing from the printed numbers gives the printed figure.

**c5 · computed · page 1**
> About 16% of shipments came from the Highland region.
Highland's share should be Highland shipments over the total.
`1.096 ÷ 7.277 = 15.06%; the document says about 16%`
Recomputing from the printed numbers gives the printed figure.

**c7 · computed · page 3**
> Total 108,5
The cost total should be rent plus travel plus software.
`31,5 + 51,5 + 25,5 = 108.5; possible range 108.35–108.65; the document says 108,5`
Recomputing from the printed numbers gives the printed figure.

**c8 · read from a chart or image · Figure 1 · page 2**
> Marketing spend reached 544 thousand in Q2.
The prose figure for Q2 marketing spend should match the Q2 bar in Figure 1.
`the Q2 bar in Figure 1 reads 533.5–553.5 (first reading 535–552, second reading 537–550); the document says 544`
The chart reading agrees with the printed number.

**c9 · read from a chart or image · Figure 2 · page 3**
> Online and store sales together reached 306 thousand in the Rural area.
The Rural online and store segments should sum to the stated 306 thousand.
`the 2 segments in Figure 2 add up to 291–321; the document says 306`
The chart reading agrees with the printed number.

**s1 · source lookup · page 3** `doi: 10.3758/s13428-015-0664-2` — The prevalence of statistical reporting errors in psychology (1985–2013)
DOI 10.3758/s13428-015-0664-2 resolves to “The prevalence of statistical reporting errors in psychology (1985–2013)” (2015), matching the cited title.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words appear on the source page.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
