# Prove report — report.pdf

**4 contradicted · 1 suspect · 0 unverified · 7 verified**

- computed: 3 contradicted, 1 suspect, 3 verified
- read from a chart or image: 2 verified
- source lookup: 1 contradicted, 2 verified

Numeric statements found: 37   checked: 22   skipped with reason: 15   missed: 0

## Contradicted (4)

**c2 · computed · page 1**
> On-time rate improved from 58.4% to 60.5%, an increase of 2.1%.
The on-time rate 'increase of 2.1%' should be the percent change from 58.4% to 60.5%.
`60.5% ÷ 58.4% − 1 = 3.60%; possible range 3.42%–3.77%; the document says 2.1%`
No rounding of the printed numbers can produce this figure.

**c3 · computed · page 1**
> In total, 7,471 service calls were recorded in the quarter.
Total service calls in the summary should equal the sum of the five regions.
`1,903 + 1,614 + 472 + 2,480 + 912 = 7,381; the document says 7,471`
No rounding of the printed numbers can produce this figure.

**c6 · computed · page 2**
> The Valley region accounted for 22.3% of service calls.
Valley's share should be Valley calls over the sum of all regions.
`1,903 ÷ (1,903 + 1,614 + 472 + 2,480 + 912) = 25.78%; the document says 22.3%`
No rounding of the printed numbers can produce this figure.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words are not on the source page. The closest passage reads: “these domains may be used as illustrative examples in documents without prior coordination with us they”.

## Suspect (1)

**c7 · computed · page 3**
> Total 218.8
The cost total should equal the sum of the four cost items.
`24.1 + 74.9 + 50.4 + 69.5 = 218.9; possible range 218.7–219.1; the document says 218.8`
Possible only if the inputs sit at the edge of their rounding.

## Verified (7)

**c1 · computed · page 1**
> Revenue rose from $7.49M in Q2 to $7.80M in Q3, up 4%.
Revenue growth should be the change from $7.49M to $7.80M.
`7.80M ÷ 7.49M − 1 = 4.14%; possible range 4.00%–4.28%; the document says 4%`
Recomputing from the printed numbers gives the printed figure.

**c4 · computed · page 2**
> Total 7,381
The table total should equal the sum of the five regions.
`1,903 + 1,614 + 472 + 2,480 + 912 = 7,381; the document says 7,381`
Recomputing from the printed numbers gives the printed figure.

**c5 · computed · page 1**
> About 21% of service calls came from the Central region.
Central's share should be Central calls over the sum of all regions.
`1,614 ÷ (1,903 + 1,614 + 472 + 2,480 + 912) = 21.87%; the document says about 21%`
Recomputing from the printed numbers gives the printed figure.

**c8 · read from a chart or image · Figure 1 · page 2**
> Training hours reached 471 thousand in Jul.
The prose figure for July training hours should match the July point in Figure 1.
`the Jul point in Figure 1 reads 455–490 (first reading 455–490, second reading 460–485); the document says 471`
The chart reading agrees with the printed number.

**c9 · read from a chart or image · Figure 2 · page 3**
> together reached 188 thousand in the Suburban area.
The Suburban online and store segments together should match the 188 thousand in the text.
`the 2 segments in Figure 2 add up to 170–207; the document says 188`
The chart reading agrees with the printed number.
Chart note: Only the Suburban area is read; Metro and Rural are not cited in the text.

**s1 · source lookup · page 3** `doi: 10.1177/1948550616673876` — The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology
DOI 10.1177/1948550616673876 resolves to “The GRIM Test” (2016), matching the cited title.

**s2 · source lookup · page 3** `doi: 10.3758/s13428-015-0664-2` — The prevalence of statistical reporting errors in psychology (1985-2013)
DOI 10.3758/s13428-015-0664-2 resolves to “The prevalence of statistical reporting errors in psychology (1985–2013)” (2015), matching the cited title.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
