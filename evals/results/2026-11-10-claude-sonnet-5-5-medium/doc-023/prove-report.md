# Prove report — report.pdf

**4 contradicted · 1 suspect · 0 unverified · 6 verified**

- computed: 3 contradicted, 1 suspect, 2 verified
- read from a chart or image: 1 contradicted, 1 verified
- source lookup: 3 verified

Numeric statements found: 35   checked: 20   skipped with reason: 15   missed: 0

## Contradicted (4)

**c1 · computed · page 1**
> Revenue rose from $1.38M in Q2 to $1.57M in Q3, up 17%.
Revenue growth should be the change from $1.38M to $1.57M.
`1.57M ÷ 1.38M − 1 = 13.77%; possible range 13.00%–14.55%; the document says 17%`
No rounding of the printed numbers can produce this figure.

**c4 · computed · page 2**
> Total 4,544
The shipments total should equal the sum of the four regions.
`1,720 + 1,485 + 547 + 772 = 4,524; the document says 4,544`
No rounding of the printed numbers can produce this figure.

**c5 · computed · page 2**
> The Valley region accounted for 14.9% of shipments.
Valley's share should be Valley shipments over the sum of the four regions.
`772 ÷ (1,720 + 1,485 + 547 + 772) = 17.06%; the document says 14.9%`
No rounding of the printed numbers can produce this figure.

**c7 · read from a chart or image · Figure 1 · page 2**
> Marketing spend reached 839 thousand in Q2.
The prose figure for Q2 marketing spend should match the Q2 bar in Figure 1.
`the Q2 bar in Figure 1 reads 650–680 (first reading 650–680, second reading 655–672); the document says 839`
The chart reading and the printed number cannot both be right.
Chart note: Bars are ordered Q4, Q1, Q2, Q3 on the x axis.

## Suspect (1)

**c6 · computed · page 3**
> Total 162.0
The cost total should equal the sum of the four items.
`61.0 + 26.7 + 24.9 + 49.5 = 162.1; possible range 161.9–162.3; the document says 162.0`
Possible only if the inputs sit at the edge of their rounding.

## Verified (6)

**c2 · computed · page 1**
> a gain of 3.3 percentage points
The margin gain should be 37.0% minus 33.7%.
`37.0% − 33.7% = 3.30 pp; possible range 3.20 pp–3.40 pp; the document says 3.3 pp`
Recomputing from the printed numbers gives the printed figure.

**c3 · computed · page 1**
> About 38% of shipments came from the South region.
South's share should be South shipments over the sum of the four regions.
`1,720 ÷ (1,720 + 1,485 + 547 + 772) = 38.02%; the document says about 38%`
Recomputing from the printed numbers gives the printed figure.

**c8 · read from a chart or image · Figure 2 · page 3**
> Online and store sales together reached 225 thousand in the Rural area.
The Rural online and store segments in Figure 2 should add up to the stated 225 thousand.
`the 2 segments in Figure 2 add up to 213–237; the document says 225`
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
