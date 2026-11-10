"""Worked examples used in docs/SPEC.md. Run: python3 test_reference.py"""
from fractions import Fraction as F
from intervals_reference import (CONTRADICTED, SUSPECT, VERIFIED, judge, parse_number,
                                 rel_pct_change, rel_pct_of, rel_sum)

def pct(x): return f"{float(x):.2f}%"
results = []
def case(name, verdict, expected, detail=""):
    ok = verdict == expected
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} | {name} -> {verdict} (expected {expected}) {detail}")

# 1. One-decimal operands: "from 2.1M to 2.3M, up 14%"
p, i = rel_pct_change(parse_number("2.1M"), parse_number("2.3M"))
case("2.1M -> 2.3M, 'up 14%'", judge(parse_number("14%"), p, i), SUSPECT,
     f"point {pct(p)}, possible range {pct(i.lo)}..{pct(i.hi)}")

# 2. Two-decimal operands: "from 2.10M to 2.30M, up 14%"
p, i = rel_pct_change(parse_number("2.10M"), parse_number("2.30M"))
case("2.10M -> 2.30M, 'up 14%'", judge(parse_number("14%"), p, i), CONTRADICTED,
     f"point {pct(p)}, possible range {pct(i.lo)}..{pct(i.hi)}")

# 3. Correct claim: "from 165 to 186, up 12.7%"
p, i = rel_pct_change(parse_number("165"), parse_number("186"))
case("165 -> 186, 'up 12.7%'", judge(parse_number("12.7%"), p, i), VERIFIED, f"point {pct(p)}")

# 4. Table of exact counts: rows sum to 4,792 but the total row prints 4,812
rows = [parse_number(t, exact=True) for t in ["1,204", "988", "1,356", "1,244"]]
p, i = rel_sum(rows)
case("exact rows sum 4,792 vs total 4,812", judge(parse_number("4,812", exact=True), p, i),
     CONTRADICTED, f"sum {p}")

# 5. Same 20-unit gap, 20 rounded rows: still impossible (max drift 20*0.5 + 0.5 = 10.5)
rows20 = [parse_number("240")] * 19 + [parse_number("232")]   # sums to 4,792
p, i = rel_sum(rows20)
case("20 rounded rows sum 4,792 vs total 4,812", judge(parse_number("4,812"), p, i),
     CONTRADICTED, f"sum range {i.lo}..{i.hi}")

# 6. Same gap, 45 rounded rows: rounding alone could explain it (45*0.5 = 22.5)
rows45 = [parse_number("106")] * 22 + [parse_number("107")] * 23   # 2332 + 2461 = 4793
rows45[0] = parse_number("105")                                      # -> 4,792
p, i = rel_sum(rows45)
case("45 rounded rows sum 4,792 vs total 4,812", judge(parse_number("4,812"), p, i),
     SUSPECT, f"sum {p}, range {float(i.lo)}..{float(i.hi)}")

# 7. Shares "33.3% + 33.3% + 33.3% = 100%"
p, i = rel_sum([parse_number("33.3%")] * 3)
case("three 33.3% shares vs '100%'", judge(parse_number("100%"), p, i), VERIFIED, f"sum {float(p)}")

# 8. Share of total: "1,356 of 4,792 is 28.3%"
p, i = rel_pct_of(parse_number("1,356", exact=True), parse_number("4,792", exact=True))
case("1,356 of 4,792 is '28.3%'", judge(parse_number("28.3%"), p, i), VERIFIED, f"point {pct(p)}")

# 9. Locale: Turkish/European format "1.234,5" must equal en "1,234.5"
a, b = parse_number("1.234,5", locale="eu"), parse_number("1,234.5")
case("locale parse 1.234,5 == 1,234.5", VERIFIED if a.point == b.point == F(12345, 10) else "mismatch", VERIFIED)

# 10. Chart label vs bar: label prints 350, two readings of the bar agree on 300..320
label = parse_number("350")
from intervals_reference import Interval
reading = Interval(F(300), F(320))
verdict = CONTRADICTED if not label.interval.overlaps(reading) else VERIFIED
case("chart label 350 vs bar read 300..320", verdict, CONTRADICTED)

print(f"\n{sum(results)}/{len(results)} passed")
raise SystemExit(0 if all(results) else 1)
