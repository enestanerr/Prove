# Prove report — report.pdf

**3 contradicted · 0 suspect · 0 unverified · 10 verified**

- read from a chart or image: 1 contradicted, 2 verified
- computed: 7 verified
- source lookup: 2 contradicted, 1 verified

Numeric statements found: 32   checked: 21   skipped with reason: 11   missed: 0

## Contradicted (3)

**c9 · read from a chart or image · Figure 1 · page 2**
> 503
The label printed on the Q2 bar should match where the bar ends.
`the Q2 bar in Figure 1 reads 620–636 (first reading 620–636, second reading 622–634); the document says 503`
The chart reading and the printed number cannot both be right.
Chart note: Bar axis starts at zero.
Chart note: Printed value labels sit above the bars.

**s2 · source lookup · page 3** `doi: 10.5555/prove.synth.0001` — Reconciling quarterly service figures in small organisations
DOI 10.5555/prove.synth.0001 does not resolve: Crossref, DataCite and doi.org answer “not found”.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words are not on the source page. The closest passage reads: “these domains may be used as illustrative examples in documents without prior coordination with us they”.

## Verified (10)

**c1 · computed · page 1**
> Revenue rose from $2.60M in Q2 to $2.97M in Q3, up 14%.
Revenue growth should be the change from $2.60M to $2.97M.
`2.97M ÷ 2.60M − 1 = 14.23%; possible range 13.82%–14.64%; the document says 14%`
Recomputing from the printed numbers gives the printed figure.

**c2 · computed · page 1**
> Gross margin improved from 27.9% to 33.8%, an increase of 5.9%.
The margin gain should be 33.8% minus 27.9%, in percentage points.
`33.8% − 27.9% = 5.90 pp; possible range 5.80 pp–6.00 pp; the document says 5.9%`
Recomputing from the printed numbers gives the printed figure.

**c3 · computed · page 1**
> In total, 6,629 shipments were recorded in the quarter.
The summary shipment total should equal the table total.
`printed as 6,629 elsewhere; the document says 6,629`
Recomputing from the printed numbers gives the printed figure.

**c4 · computed · page 2**
> Total 6,629
The table total should be the sum of the five regions.
`1,455 + 884 + 733 + 2,224 + 1,333 = 6,629; the document says 6,629`
Recomputing from the printed numbers gives the printed figure.

**c5 · computed · page 1**
> About 10% of shipments came from the Coastal region.
Coastal's share should be Coastal shipments over the total.
`733 ÷ 6,629 = 11.06%; the document says about 10%`
Recomputing from the printed numbers gives the printed figure.

**c6 · computed · page 2**
> The East region accounted for 33.5% of shipments.
East's share should be East shipments over the total.
`2,224 ÷ 6,629 = 33.55%; the document says 33.5%`
Recomputing from the printed numbers gives the printed figure.

**c7 · computed · page 3**
> Total 111.2
The cost total should be the sum of the three items.
`43.9 + 25.9 + 41.4 = 111.2; possible range 111.05–111.35; the document says 111.2`
Recomputing from the printed numbers gives the printed figure.

**c8 · read from a chart or image · Figure 1 · page 2**
> Training hours reached 628 thousand in Q2.
The prose figure for Q2 training hours should match the Q2 bar in Figure 1.
`the Q2 bar in Figure 1 reads 620–636 (first reading 620–636, second reading 622–634); the document says 628 thousand`
The chart reading agrees with the printed number.
Chart note: Bar axis starts at zero.
Chart note: Printed value labels sit above the bars.

**c10 · read from a chart or image · Figure 2 · page 3**
> Online and store sales together reached 161 thousand in the Suburban area.
Online plus store sales in Suburban should match the stated 161 thousand.
`the 2 segments in Figure 2 add up to 150–172; the document says 161 thousand`
The chart reading agrees with the printed number.
Chart note: Stacked bars; segments read as own heights.

**s1 · source lookup · page 3** `doi: 10.1177/1948550616673876` — The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology
DOI 10.1177/1948550616673876 resolves to “The GRIM Test” (2016), matching the cited title.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
