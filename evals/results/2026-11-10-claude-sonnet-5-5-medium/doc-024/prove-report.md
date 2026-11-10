# Prove report — report.pdf

**4 contradicted · 0 suspect · 0 unverified · 9 verified**

- computed: 2 contradicted, 5 verified
- read from a chart or image: 1 contradicted, 2 verified
- source lookup: 1 contradicted, 2 verified

Numeric statements found: 35   checked: 20   skipped with reason: 15   missed: 0

## Contradicted (4)

**c1 · computed · page 1**
> Revenue rose from $9.10M in Q2 to $10.60M in Q3, up 20%.
Revenue growth should be the change from $9.10M to $10.60M.
`10.60M ÷ 9.10M − 1 = 16.48%; possible range 16.36%–16.60%; the document says 20%`
No rounding of the printed numbers can produce this figure.

**c6 · computed · page 2**
> The South region accounted for 25.7% of service calls.
The South share should be South calls over total calls.
`966 ÷ 3,415 = 28.29%; the document says 25.7%`
No rounding of the printed numbers can produce this figure.

**c9 · read from a chart or image · Figure 1 · page 2**
> 71
The value label on the Q1 bar should match where the bar ends.
`the Q1 bar in Figure 1 reads 225.5–241.5 (first reading 227–240, second reading 229–237); the document says 71`
The chart reading and the printed number cannot both be right.
Chart note: Bar order on the x axis is Q4, Q1, Q2, Q3.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words are not on the source page. The closest passage reads: “these domains may be used as illustrative examples in documents without prior coordination with us they”.

## Verified (9)

**c2 · computed · page 1**
> a gain of 4.9 percentage points.
The retention gain should be 25.2% minus 20.3% in percentage points.
`25.2% − 20.3% = 4.90 pp; possible range 4.80 pp–5.00 pp; the document says 4.9 pp`
Recomputing from the printed numbers gives the printed figure.

**c3 · computed · page 2**
> Total 3,415
The table total should be the sum of the four regions.
`966 + 909 + 1,161 + 379 = 3,415; the document says 3,415`
Recomputing from the printed numbers gives the printed figure.

**c4 · computed · page 1**
> In total, 3,415 service calls were recorded in the quarter.
The total on page 1 should equal the table total on page 2.
`printed as 3,415 elsewhere; the document says 3,415`
Recomputing from the printed numbers gives the printed figure.

**c5 · computed · page 1**
> About 26% of service calls came from the North region.
The North share should be North calls over total calls.
`909 ÷ 3,415 = 26.62%; the document says about 26%`
Recomputing from the printed numbers gives the printed figure.

**c7 · computed · page 3**
> Total 109.2
The cost total should be the sum of travel, staff and software.
`11.0 + 21.0 + 77.2 = 109.2; possible range 109.05–109.35; the document says 109.2`
Recomputing from the printed numbers gives the printed figure.

**c8 · read from a chart or image · Figure 1 · page 2**
> Marketing spend reached 234 thousand in Q1.
The prose figure for Q1 marketing spend should match the Q1 bar in Figure 1.
`the Q1 bar in Figure 1 reads 225.5–241.5 (first reading 227–240, second reading 229–237); the document says 234 thousand`
The chart reading agrees with the printed number.
Chart note: Bar order on the x axis is Q4, Q1, Q2, Q3.

**c10 · read from a chart or image · Figure 2 · page 3**
> Online and store sales together reached 164 thousand in the Metro area.
Metro online plus store segments should add up to the 164 thousand in the text.
`the 2 segments in Figure 2 add up to 155–172; the document says 164 thousand`
The chart reading agrees with the printed number.

**s1 · source lookup · page 3** `doi: 10.1177/1948550616673876` — The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology
DOI 10.1177/1948550616673876 resolves to “The GRIM Test” (2016), matching the cited title.

**s2 · source lookup · page 3** `doi: 10.3758/s13428-015-0664-2` — The prevalence of statistical reporting errors in psychology (1985-2013)
DOI 10.3758/s13428-015-0664-2 resolves to “The prevalence of statistical reporting errors in psychology (1985–2013)” (2015), matching the cited title.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
