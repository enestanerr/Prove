# Prove report — report.pdf

**5 contradicted · 0 suspect · 0 unverified · 6 verified**

- computed: 3 contradicted, 3 verified
- read from a chart or image: 2 verified
- source lookup: 2 contradicted, 1 verified

Numeric statements found: 32   checked: 21   skipped with reason: 11   missed: 0

## Contradicted (5)

**c4 · computed · page 2**
> Total 8,625
The shipments total should be the sum of the four regions.
`2,392 + 2,171 + 2,157 + 1,795 = 8,515; the document says 8,625`
No rounding of the printed numbers can produce this figure.

**c5 · computed · page 2**
> The West region accounted for 24.9% of shipments.
West's share should be West shipments over the sum of the four regions.
`2,392 ÷ (2,392 + 2,171 + 2,157 + 1,795) = 28.09%; the document says 24.9%`
No rounding of the printed numbers can produce this figure.

**c6 · computed · page 3**
> Total 331.3
The cost total should be the sum of the five items.
`78.2 + 58.2 + 17.0 + 91.4 + 84.5 = 329.3; possible range 329.05–329.55; the document says 331.3`
No rounding of the printed numbers can produce this figure.

**s2 · source lookup · page 3** `doi: 10.5555/prove.synth.0017` — Reconciling quarterly service figures in small organisations
DOI 10.5555/prove.synth.0017 does not resolve: Crossref, DataCite and doi.org answer “not found”.

**s3 · source lookup · page 3** `quote: https://www.iana.org/help/example-domains`
The quoted words are not on the source page. The closest passage reads: “these domains may be used as illustrative examples in documents without prior coordination with us they”.

## Verified (6)

**c1 · computed · page 1**
> Revenue rose from $6.4M in Q2 to $7.2M in Q3, up 13%.
Revenue growth should be the change from $6.4M to $7.2M.
`$7.2M ÷ $6.4M − 1 = 12.50%; possible range 10.85%–14.17%; the document says 13%`
Recomputing from the printed numbers gives the printed figure.

**c2 · computed · page 1**
> Retention rate improved from 51.2% to 54.5%, an increase of 3.3%.
The retention increase, read as percentage points, should be 54.5% minus 51.2%.
`54.5% − 51.2% = 3.30 pp; possible range 3.20 pp–3.40 pp; the document says 3.3%`
Recomputing from the printed numbers gives the printed figure.

**c3 · computed · page 1**
> About 25% of shipments came from the South region.
South's share should be South shipments over the sum of the four regions.
`2,171 ÷ (2,392 + 2,171 + 2,157 + 1,795) = 25.50%; the document says about 25%`
Recomputing from the printed numbers gives the printed figure.

**c7 · read from a chart or image · Figure 1 · page 2**
> Support tickets reached 819 thousand in Jun.
The prose figure for June tickets should match the Jun point in Figure 1.
`the Jun point in Figure 1 reads 800–830 (first reading 800–830, second reading 805–828); the document says 819 thousand`
The chart reading agrees with the printed number.

**c8 · read from a chart or image · Figure 2 · page 3**
> reached 292 thousand in the Rural area
The Rural stacked segments should add up to the stated 292 thousand.
`the 2 segments in Figure 2 add up to 278–304; the document says 292 thousand`
The chart reading agrees with the printed number.

**s1 · source lookup · page 3** `doi: 10.1177/1948550616673876` — The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology
DOI 10.1177/1948550616673876 resolves to “The GRIM Test” (2016), matching the cited title.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
