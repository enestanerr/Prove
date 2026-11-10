# Prove report — report.pdf

**4 contradicted · 0 suspect · 0 unverified · 8 verified**

- computed: 2 contradicted, 5 verified
- read from a chart or image: 1 contradicted, 1 verified
- source lookup: 1 contradicted, 2 verified

Numeric statements found: 36   checked: 21   skipped with reason: 15   missed: 0

## Contradicted (4)

**c1 · computed · page 1**
> Revenue rose from $6.94M in Q2 to $7.77M in Q3, up 15%.
Revenue growth should be the change from $6.94M to $7.77M.
`7.77M ÷ 6.94M − 1 = 11.96%; possible range 11.81%–12.11%; the document says 15%`
No rounding of the printed numbers can produce this figure.

**c2 · computed · page 1**
> On-time rate improved from 29.8% to 35.5%, an increase of 5.7%.
An increase of 5.7% in the on-time rate should be the relative change from 29.8% to 35.5%.
`35.5% ÷ 29.8% − 1 = 19.13%; possible range 18.76%–19.50%; the document says 5.7%`
No rounding of the printed numbers can produce this figure.

**c9 · read from a chart or image · Figure 2 · page 3**
> Online and store sales together reached 447 thousand in the Metro area.
The Metro total in the prose should match the Online and Stores segments stacked in Figure 2.
`the 2 segments in Figure 2 add up to 342–364; the document says 447 thousand`
The chart reading and the printed number cannot both be right.
Chart note: Segment heights read as top minus bottom; stacked bar axis starts at zero.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words are not on the source page. The closest passage reads: “these domains may be used as illustrative examples in documents without prior coordination with us they”.

## Verified (8)

**c3 · computed · page 1**
> In total, 5,407 service calls were recorded in the quarter.
The printed total of service calls should equal the sum of the five regions.
`940 + 880 + 1,382 + 1,515 + 690 = 5,407; the document says 5,407`
Recomputing from the printed numbers gives the printed figure.

**c4 · computed · page 2**
> Total 5,407
The table total should equal the sum of the five regions.
`940 + 880 + 1,382 + 1,515 + 690 = 5,407; the document says 5,407`
Recomputing from the printed numbers gives the printed figure.

**c5 · computed · page 1**
> About 16% of service calls came from the Highland region.
The Highland share should be Highland calls over the sum of all regions.
`880 ÷ (940 + 880 + 1,382 + 1,515 + 690) = 16.28%; the document says about 16%`
Recomputing from the printed numbers gives the printed figure.

**c6 · computed · page 2**
> The West region accounted for 12.8% of service calls.
The West share should be West calls over the sum of all regions.
`690 ÷ (940 + 880 + 1,382 + 1,515 + 690) = 12.76%; the document says 12.8%`
Recomputing from the printed numbers gives the printed figure.

**c7 · computed · page 3**
> Total 122.5
The cost total should equal insurance plus rent plus utilities.
`73.6 + 30.4 + 18.5 = 122.5; possible range 122.35–122.65; the document says 122.5`
Recomputing from the printed numbers gives the printed figure.

**c8 · read from a chart or image · Figure 1 · page 2**
> Marketing spend reached 811 thousand in Aug.
The prose figure for August marketing spend should match the August point in Figure 1.
`the Aug point in Figure 1 reads 800–820 (first reading 800–820, second reading 802–820); the document says 811 thousand`
The chart reading agrees with the printed number.

**s1 · source lookup · page 3** `doi: 10.1177/1948550616673876` — The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology
DOI 10.1177/1948550616673876 resolves to “The GRIM Test” (2016), matching the cited title.

**s2 · source lookup · page 3** `doi: 10.3758/s13428-015-0664-2` — The prevalence of statistical reporting errors in psychology (1985-2013)
DOI 10.3758/s13428-015-0664-2 resolves to “The prevalence of statistical reporting errors in psychology (1985–2013)” (2015), matching the cited title.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
