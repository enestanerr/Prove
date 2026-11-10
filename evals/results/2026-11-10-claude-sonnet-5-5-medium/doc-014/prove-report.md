# Prove report — report.pdf

**2 contradicted · 1 suspect · 0 unverified · 8 verified**

- computed: 2 contradicted, 1 suspect, 3 verified
- read from a chart or image: 2 verified
- source lookup: 3 verified

Numeric statements found: 35   checked: 20   skipped with reason: 15   missed: 0

## Contradicted (2)

**c4 · computed · page 2**
> Total 6,908
The orders total should be the sum of the four regions.
`2,375 + 557 + 1,502 + 2,444 = 6,878; the document says 6,908`
No rounding of the printed numbers can produce this figure.

**c6 · computed · page 3**
> Total 77.2
The cost total should be the sum of the four items.
`11.3 + 42.2 + 12.4 + 9.7 = 75.6; possible range 75.4–75.8; the document says 77.2`
No rounding of the printed numbers can produce this figure.

## Suspect (1)

**c1 · computed · page 1**
> Revenue rose from $7.7M in Q2 to $8.4M in Q3, up 8%.
Revenue growth should be the change from $7.7M to $8.4M.
`8.4M ÷ 7.7M − 1 = 9.09%; possible range 7.74%–10.46%; the document says 8%`
Possible only if the inputs sit at the edge of their rounding.

## Verified (8)

**c2 · computed · page 1**
> a gain of 4.6 percentage points
The retention gain should be 47.9% minus 43.3%.
`47.9% − 43.3% = 4.60 pp; possible range 4.50 pp–4.70 pp; the document says 4.6 pp`
Recomputing from the printed numbers gives the printed figure.

**c3 · computed · page 1**
> About 23% of orders came from the Valley region.
The Valley share should be Valley orders over the sum of the four regions.
`1,502 ÷ (2,375 + 557 + 1,502 + 2,444) = 21.84%; the document says about 23%`
Recomputing from the printed numbers gives the printed figure.

**c5 · computed · page 2**
> The East region accounted for 8.1% of orders.
The East share should be East orders over the sum of the four regions.
`557 ÷ (2,375 + 557 + 1,502 + 2,444) = 8.10%; the document says 8.1%`
Recomputing from the printed numbers gives the printed figure.

**c7 · read from a chart or image · Figure 1 · page 2**
> Marketing spend reached 839 thousand in Sep.
The prose figure for September spend should match the Sep point in Figure 1.
`the Sep point in Figure 1 reads 825–855 (first reading 825–855, second reading 828–852); the document says 839 thousand`
The chart reading agrees with the printed number.

**c8 · read from a chart or image · Figure 2 · page 3**
> reached 322 thousand in the Rural area
Online plus store sales in Rural should match the stated 322 thousand.
`the 2 segments in Figure 2 add up to 312–332; the document says 322 thousand`
The chart reading agrees with the printed number.

**s1 · source lookup · page 3** `doi: 10.1177/1948550616673876` — The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology
DOI 10.1177/1948550616673876 resolves to “The GRIM Test” (2016), matching the cited title.

**s2 · source lookup · page 3** `doi: 10.3758/s13428-015-0664-2` — The prevalence of statistical reporting errors in psychology (1985–2013)
DOI 10.3758/s13428-015-0664-2 resolves to “The prevalence of statistical reporting errors in psychology (1985–2013)” (2015), matching the cited title.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words appear on the source page.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
