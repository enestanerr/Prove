# Prove report — report.pdf

**3 contradicted · 1 suspect · 0 unverified · 9 verified**

- computed: 1 contradicted, 1 suspect, 5 verified
- read from a chart or image: 1 contradicted, 2 verified
- source lookup: 1 contradicted, 2 verified

Numeric statements found: 32   checked: 21   skipped with reason: 11   missed: 0

## Contradicted (3)

**c3 · computed · page 1**
> In total, 6,579 visits were recorded in the quarter.
Total visits in the summary should equal the sum of the four regions.
`1,253 + 1,975 + 2,447 + 1,084 = 6,759; the document says 6,579`
No rounding of the printed numbers can produce this figure.

**c9 · read from a chart or image · Figure 1 · page 2**
> 611
The value label on the Q3 bar should match where the bar ends.
`the Q3 bar in Figure 1 reads 802.5–822.5 (first reading 805–820, second reading 808–818); the document says 611`
The chart reading and the printed number cannot both be right.
Chart note: Other bars carry value labels 152, 775, 805; only Q3 was checked.

**s2 · source lookup · page 3** `doi: 10.5555/prove.synth.0019` — Reconciling quarterly service figures in small organisations
DOI 10.5555/prove.synth.0019 does not resolve: Crossref, DataCite and doi.org answer “not found”.

## Suspect (1)

**c7 · computed · page 3**
> Total 170.9
The cost total should equal the sum of the four items.
`31.3 + 46.5 + 41.0 + 52.2 = 171.0; possible range 170.8–171.2; the document says 170.9`
Possible only if the inputs sit at the edge of their rounding.

## Verified (9)

**c1 · computed · page 1**
> Revenue rose from $4.5M in Q2 to $4.8M in Q3, up 7%.
Revenue growth should be the change from $4.5M to $4.8M.
`4.8M ÷ 4.5M − 1 = 6.67%; possible range 4.40%–8.99%; the document says 7%`
Recomputing from the printed numbers gives the printed figure.

**c2 · computed · page 1**
> a gain of 4.3 percentage points
The occupancy gain should be 41.2% minus 36.9%.
`41.2% − 36.9% = 4.30 pp; possible range 4.20 pp–4.40 pp; the document says 4.3 pp`
Recomputing from the printed numbers gives the printed figure.

**c4 · computed · page 2**
> Total 6,759
The table total should equal the sum of the four regions.
`1,253 + 1,975 + 2,447 + 1,084 = 6,759; the document says 6,759`
Recomputing from the printed numbers gives the printed figure.

**c5 · computed · page 1**
> About 18% of visits came from the South region.
South's share should be South visits over the sum of all regions.
`1,253 ÷ (1,253 + 1,975 + 2,447 + 1,084) = 18.54%; the document says about 18%`
Recomputing from the printed numbers gives the printed figure.

**c6 · computed · page 2**
> The Valley region accounted for 29.2% of visits.
Valley's share should be Valley visits over the sum of all regions.
`1,975 ÷ (1,253 + 1,975 + 2,447 + 1,084) = 29.22%; the document says 29.2%`
Recomputing from the printed numbers gives the printed figure.

**c8 · read from a chart or image · Figure 1 · page 2**
> Training hours reached 814 thousand in Q3.
The prose figure for Q3 training hours should match the Q3 bar in Figure 1.
`the Q3 bar in Figure 1 reads 802.5–822.5 (first reading 805–820, second reading 808–818); the document says 814`
The chart reading agrees with the printed number.
Chart note: Other bars carry value labels 152, 775, 805; only Q3 was checked.

**c10 · read from a chart or image · Figure 2 · page 3**
> Online and store sales together reached 220 thousand in the Rural area.
The Rural stacked segments should add up to the stated 220 thousand.
`the 2 segments in Figure 2 add up to 212–228; the document says 220`
The chart reading agrees with the printed number.

**s1 · source lookup · page 3** `doi: 10.1177/1948550616673876` — The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology
DOI 10.1177/1948550616673876 resolves to “The GRIM Test” (2016), matching the cited title.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words appear on the source page.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
