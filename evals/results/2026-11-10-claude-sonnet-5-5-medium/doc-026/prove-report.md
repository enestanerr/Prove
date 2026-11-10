# Prove report — report.pdf

**2 contradicted · 1 suspect · 0 unverified · 8 verified**

- computed: 2 contradicted, 1 suspect, 3 verified
- read from a chart or image: 2 verified
- source lookup: 3 verified

Numeric statements found: 36   checked: 21   skipped with reason: 15   missed: 0

## Contradicted (2)

**c4 · computed · page 2**
> Total 5,956
The orders total should be the sum of the four regions.
`1,486 + 425 + 2,364 + 1,651 = 5,926; the document says 5,956`
No rounding of the printed numbers can produce this figure.

**c5 · computed · page 2**
> The Valley region accounted for 37.6% of orders.
Valley's share should be its orders over the sum of the four regions.
`2,364 ÷ (1,486 + 425 + 2,364 + 1,651) = 39.89%; the document says 37.6%`
No rounding of the printed numbers can produce this figure.

## Suspect (1)

**c6 · computed · page 3**
> Total 222.6
The cost total should be the sum of the five items.
`75.3 + 25.2 + 18.9 + 35.9 + 67.2 = 222.5; possible range 222.25–222.75; the document says 222.6`
Possible only if the inputs sit at the edge of their rounding.

## Verified (8)

**c1 · computed · page 1**
> Revenue rose from $7.06M in Q2 to $7.51M in Q3, up 6%.
Revenue growth should be the change from $7.06M to $7.51M.
`7.51M ÷ 7.06M − 1 = 6.37%; possible range 6.23%–6.52%; the document says 6%`
Recomputing from the printed numbers gives the printed figure.

**c2 · computed · page 1**
> a gain of 4.2 percentage points
The retention gain should be 50.7% minus 46.5%.
`50.7% − 46.5% = 4.20 pp; possible range 4.10 pp–4.30 pp; the document says 4.2 pp`
Recomputing from the printed numbers gives the printed figure.

**c3 · computed · page 1**
> About 27% of orders came from the South region.
South's share should be its orders over the sum of the four regions.
`1,651 ÷ (1,486 + 425 + 2,364 + 1,651) = 27.86%; the document says about 27%`
Recomputing from the printed numbers gives the printed figure.

**c7 · read from a chart or image · Figure 1 · page 2**
> Support tickets reached 307 thousand in Q4.
The prose figure for Q4 tickets should match the Q4 bar in Figure 1.
`the Q4 bar in Figure 1 reads 297–313 (first reading 298–312, second reading 300–311); the document says 307 thousand`
The chart reading agrees with the printed number.

**c8 · read from a chart or image · Figure 2 · page 3**
> together reached 271 thousand in the Metro area.
Metro online plus store sales should match the 271 thousand in the prose.
`the 2 segments in Figure 2 add up to 259–283; the document says 271 thousand`
The chart reading agrees with the printed number.

**s1 · source lookup · page 3** `doi: 10.3758/s13428-015-0664-2` — The prevalence of statistical reporting errors in psychology (1985-2013)
DOI 10.3758/s13428-015-0664-2 resolves to “The prevalence of statistical reporting errors in psychology (1985–2013)” (2015), matching the cited title.

**s2 · source lookup · page 3** `doi: 10.1177/1948550616673876` — The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology
DOI 10.1177/1948550616673876 resolves to “The GRIM Test” (2016), matching the cited title.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words appear on the source page.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
