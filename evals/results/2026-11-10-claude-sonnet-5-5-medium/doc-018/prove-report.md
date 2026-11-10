# Prove report — report.pdf

**3 contradicted · 0 suspect · 0 unverified · 9 verified**

- computed: 1 contradicted, 6 verified
- read from a chart or image: 1 contradicted, 1 verified
- source lookup: 1 contradicted, 2 verified

Numeric statements found: 36   checked: 21   skipped with reason: 15   missed: 0

## Contradicted (3)

**c6 · computed · page 2**
> The Central region accounted for 35.1% of visits.
The Central share should be Central visits over total visits.
`1,986 ÷ 6,105 = 32.53%; the document says 35.1%`
No rounding of the printed numbers can produce this figure.

**c8 · read from a chart or image · Figure 1 · page 2**
> Support tickets reached 429 thousand in Q4.
The prose figure for Q4 tickets should match the Q4 bar in Figure 1.
`the Q4 bar in Figure 1 reads 270–288 (first reading 270–288, second reading 272–286); the document says 429`
The chart reading and the printed number cannot both be right.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words are not on the source page. The closest passage reads: “these domains may be used as illustrative examples in documents without prior coordination with us they”.

## Verified (9)

**c1 · computed · page 1**
> Revenue rose from $8.23M in Q2 to $9.04M in Q3, up 10%.
Revenue growth should be the change from $8.23M to $9.04M.
`9.04M ÷ 8.23M − 1 = 9.84%; possible range 9.71%–9.97%; the document says 10%`
Recomputing from the printed numbers gives the printed figure.

**c2 · computed · page 1**
> On-time rate improved from 47.2% to 52.3%, an increase of 5.1%.
The on-time improvement should be the point difference between 52.3% and 47.2%.
`52.3% − 47.2% = 5.10 pp; possible range 5.00 pp–5.20 pp; the document says 5.1%`
Recomputing from the printed numbers gives the printed figure.

**c3 · computed · page 1**
> In total, 6,105 visits were recorded in the quarter.
Total visits should be the sum of the five regions.
`376 + 2,243 + 1,007 + 493 + 1,986 = 6,105; the document says 6,105`
Recomputing from the printed numbers gives the printed figure.

**c4 · computed · page 2**
> Total 6,105
The table total should be the sum of the five regions.
`376 + 2,243 + 1,007 + 493 + 1,986 = 6,105; the document says 6,105`
Recomputing from the printed numbers gives the printed figure.

**c5 · computed · page 1**
> About 15% of visits came from the South region.
The South share should be South visits over total visits.
`1,007 ÷ 6,105 = 16.49%; the document says about 15%`
Recomputing from the printed numbers gives the printed figure.

**c7 · computed · page 3**
> Total 89.7
The cost total should be the sum of the three items.
`38.4 + 38.9 + 12.4 = 89.7; possible range 89.55–89.85; the document says 89.7`
Recomputing from the printed numbers gives the printed figure.

**c9 · read from a chart or image · Figure 2 · page 3**
> Online and store sales together reached 168 thousand in the Rural area.
Rural online plus store segments should add to the 168 thousand in the text.
`the 2 segments in Figure 2 add up to 158–178; the document says 168`
The chart reading agrees with the printed number.

**s1 · source lookup · page 3** `doi: 10.3758/s13428-015-0664-2` — The prevalence of statistical reporting errors in psychology (1985–2013)
DOI 10.3758/s13428-015-0664-2 resolves to “The prevalence of statistical reporting errors in psychology (1985–2013)” (2015), matching the cited title.

**s2 · source lookup · page 3** `doi: 10.1177/1948550616673876` — The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology
DOI 10.1177/1948550616673876 resolves to “The GRIM Test” (2016), matching the cited title.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
