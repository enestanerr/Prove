# Prove report — examples/kestrel-q3/report.md

**3 contradicted · 1 suspect · 2 unverified · 4 verified**

- computed: 2 contradicted, 1 suspect, 3 verified
- read from a chart or image: 1 contradicted, 1 verified
- source lookup: 2 unverified

Numeric statements found: 26   checked: 16   skipped with reason: 10   missed: 0

## Contradicted (3)

**c1 · computed · page 1**
> Revenue rose from $2.10M in Q2 to $2.30M in Q3, up 14%.
The growth figure should be the change from $2.10M to $2.30M.
`2.30M ÷ 2.10M − 1 = 9.52%; possible range 9.03%–10.02%; the document says 14%`
No rounding of the printed numbers can produce this figure.

**c2 · computed · page 2**
> Total | 4,812
The total row should be the sum of the four regions.
`1,204 + 988 + 1,356 + 1,244 = 4,792; the document says 4,812`
No rounding of the printed numbers can produce this figure.

**c4 · read from a chart or image · Figure 2 · page 3**
> Q3 marketing spend reached 350k
The prose figure for Q3 marketing spend should match the Q3 bar in Figure 2.
`the Q3 bar in Figure 2 reads 300–320 (first reading 300–320, second reading 302–318); the document says 350`
The chart reading and the printed number cannot both be right.

## Suspect (1)

**c5 · computed · page 1**
> Newsletter subscribers grew from 2.1M to 2.3M over the same period, also up 14%.
Subscriber growth should be the change from 2.1M to 2.3M.
`2.3M ÷ 2.1M − 1 = 9.52%; possible range 4.65%–14.63%; the document says 14%`
Possible only if the inputs sit at the edge of their rounding.

## Unverified (2)

**s1 · source lookup · page 4** `doi: 10.1234/example.2021.001` — An example cited title
Sources were not checked. Run `provecheck sources`.

**s2 · source lookup · page 4** `doi: 10.1177/1948550616673876` — The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology
Sources were not checked. Run `provecheck sources`.

## Verified (4)

**c3 · computed · page 2**
> East accounted for 28.3% of orders
East's share should be its orders divided by the sum of all regions.
`1,356 ÷ (1,204 + 988 + 1,356 + 1,244) = 28.30%; the document says 28.3%`
Recomputing from the printed numbers gives the printed figure.

**c6 · computed · page 1**
> Gross margin improved from 41.2% to 43.7%, a gain of 2.5 percentage points.
The margin gain should be 43.7% minus 41.2%, in percentage points.
`43.7% − 41.2% = 2.50 pp; possible range 2.40 pp–2.60 pp; the document says 2.5 pp`
Recomputing from the printed numbers gives the printed figure.

**c7 · computed · page 2**
> East | 1,356
East should have the most orders of the four regions.
`place of 1,356 among 4 values, counting from the largest: 1; the document claims place 1`
The printed numbers give this ranking.

**c8 · read from a chart or image · Figure 2 · page 3**
The Q3 bar should be the tallest of the four quarters in Figure 2.
`the Q3 bar in Figure 2 reads 300–320; the others read Q4 255–275, Q1 230–250, Q2 265–285; the document calls Q3 the largest`
The chart readings do not contradict the stated order.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
