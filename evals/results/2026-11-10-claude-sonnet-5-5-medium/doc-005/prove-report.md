# Prove report — report.pdf

**3 contradicted · 2 suspect · 0 unverified · 7 verified**

- read from a chart or image: 1 contradicted, 1 verified
- computed: 2 suspect, 5 verified
- source lookup: 2 contradicted, 1 verified

Numeric statements found: 33   checked: 22   skipped with reason: 11   missed: 0

## Contradicted (3)

**c8 · read from a chart or image · Figure 1 · page 2**
> Energy use reached 404 thousand in Q3.
The prose figure for Q3 energy use should match the Q3 bar in Figure 1.
`the Q3 bar in Figure 1 reads 218–238 (first reading 220–236, second reading 222–234); the document says 404`
The chart reading and the printed number cannot both be right.

**s2 · source lookup · page 3** `doi: 10.5555/prove.synth.0005` — Reconciling quarterly service figures in small organisations
DOI 10.5555/prove.synth.0005 does not resolve: Crossref, DataCite and doi.org answer “not found”.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words are not on the source page. The closest passage reads: “these domains may be used as illustrative examples in documents without prior coordination with us they”.

## Suspect (2)

**c1 · computed · page 1**
> Revenue rose from $3.9M in Q2 to $4.4M in Q3, up 14%.
Revenue growth should be the change from $3.9M to $4.4M.
`4.4M ÷ 3.9M − 1 = 12.82%; possible range 10.13%–15.58%; the document says 14%`
Possible only if the inputs sit at the edge of their rounding.

**c7 · computed · page 3**
> Total 220.2
The cost total should be the sum of the five items.
`16.2 + 39.4 + 79.5 + 57.8 + 27.4 = 220.3; possible range 220.05–220.55; the document says 220.2`
Possible only if the inputs sit at the edge of their rounding.

## Verified (7)

**c2 · computed · page 1**
> a gain of 2.9 percentage points
The occupancy gain should be 57.2% minus 54.3% in points.
`57.2% − 54.3% = 2.90 pp; possible range 2.80 pp–3.00 pp; the document says 2.9 pp`
Recomputing from the printed numbers gives the printed figure.

**c3 · computed · page 2**
> Total 7,403
The table total should be the sum of the four regions.
`2,335 + 823 + 2,272 + 1,973 = 7,403; the document says 7,403`
Recomputing from the printed numbers gives the printed figure.

**c4 · computed · page 1**
> In total, 7,403 orders were recorded in the quarter.
The order total on page 1 should equal the table total on page 2.
`printed as 7,403 elsewhere; the document says 7,403`
Recomputing from the printed numbers gives the printed figure.

**c5 · computed · page 1**
> About 32% of orders came from the South region.
The South share should be South orders divided by total orders.
`2,272 ÷ 7,403 = 30.69%; the document says about 32%`
Recomputing from the printed numbers gives the printed figure.

**c6 · computed · page 2**
> The Highland region accounted for 11.1% of orders.
The Highland share should be Highland orders divided by total orders.
`823 ÷ 7,403 = 11.12%; the document says 11.1%`
Recomputing from the printed numbers gives the printed figure.

**c9 · read from a chart or image · Figure 2 · page 3**
> Online and store sales together reached 303 thousand in the Rural area.
Online plus store sales in Rural should match the stated 303 thousand.
`the 2 segments in Figure 2 add up to 295–311; the document says 303`
The chart reading agrees with the printed number.

**s1 · source lookup · page 3** `doi: 10.1177/1948550616673876` — The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology
DOI 10.1177/1948550616673876 resolves to “The GRIM Test” (2016), matching the cited title.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
