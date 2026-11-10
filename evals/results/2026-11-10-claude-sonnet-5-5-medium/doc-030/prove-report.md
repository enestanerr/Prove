# Prove report — report.pdf

**5 contradicted · 0 suspect · 0 unverified · 7 verified**

- computed: 2 contradicted, 5 verified
- read from a chart or image: 1 contradicted, 1 verified
- source lookup: 2 contradicted, 1 verified

Numeric statements found: 36   checked: 21   skipped with reason: 15   missed: 0

## Contradicted (5)

**c2 · computed · page 1**
> Occupancy rate improved from 24.0% to 28.7%, an increase of 4.7%.
An increase of 4.7% in occupancy should be the relative change from 24.0% to 28.7%.
`28.7% ÷ 24.0% − 1 = 19.58%; possible range 19.13%–20.04%; the document says 4.7%`
No rounding of the printed numbers can produce this figure.

**c7 · computed · page 3**
> Insurance 38.1 Total 195.7
The cost total should be the sum of the four items.
`59.0 + 30.3 + 70.4 + 38.1 = 197.8; possible range 197.6–198; the document says 195.7`
No rounding of the printed numbers can produce this figure.

**c8 · read from a chart or image · Figure 1 · page 2**
> Support tickets reached 101 thousand in Q2.
The prose figure for Q2 support tickets should match the Q2 bar in Figure 1.
`the Q2 bar in Figure 1 reads 267.5–285.5 (first reading 268–285, second reading 270–283); the document says 101`
The chart reading and the printed number cannot both be right.
Chart note: Quarter order on the x axis is Q4, Q1, Q2, Q3.

**s2 · source lookup · page 3** `doi: 10.5555/prove.synth.0030` — Reconciling quarterly service figures in small organisations
DOI 10.5555/prove.synth.0030 does not resolve: Crossref, DataCite and doi.org answer “not found”.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words are not on the source page. The closest passage reads: “these domains may be used as illustrative examples in documents without prior coordination with us they”.

## Verified (7)

**c1 · computed · page 1**
> Revenue rose from $4.16M in Q2 to $4.70M in Q3, up 13%.
Revenue growth should be the change from $4.16M to $4.70M.
`4.70M ÷ 4.16M − 1 = 12.98%; possible range 12.73%–13.24%; the document says 13%`
Recomputing from the printed numbers gives the printed figure.

**c3 · computed · page 1**
> In total, 3,752 enrolments were recorded in the quarter.
Total enrolments should be the sum of the four regions.
`959 + 874 + 745 + 1,174 = 3,752; the document says 3,752`
Recomputing from the printed numbers gives the printed figure.

**c4 · computed · page 2**
> Highland 1,174 Total 3,752
The table total should equal the total in the summary.
`printed as 3,752 elsewhere; the document says 3,752`
Recomputing from the printed numbers gives the printed figure.

**c5 · computed · page 1**
> About 26% of enrolments came from the West region.
West share should be 959 of 3,752 enrolments.
`959 ÷ 3,752 = 25.56%; the document says about 26%`
Recomputing from the printed numbers gives the printed figure.

**c6 · computed · page 2**
> The North region accounted for 23.3% of enrolments.
North share should be 874 of 3,752 enrolments.
`874 ÷ 3,752 = 23.29%; the document says 23.3%`
Recomputing from the printed numbers gives the printed figure.

**c9 · read from a chart or image · Figure 2 · page 3**
> Online and store sales together reached 338 thousand in the Rural area.
The Rural sales figure should match the sum of the Online and Stores segments in Figure 2.
`the 2 segments in Figure 2 add up to 326–352; the document says 338`
The chart reading agrees with the printed number.

**s1 · source lookup · page 3** `doi: 10.3758/s13428-015-0664-2` — The prevalence of statistical reporting errors in psychology (1985-2013)
DOI 10.3758/s13428-015-0664-2 resolves to “The prevalence of statistical reporting errors in psychology (1985–2013)” (2015), matching the cited title.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
