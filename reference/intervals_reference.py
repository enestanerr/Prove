"""Reference implementation of Prove's core verdict rule (stdlib only).

This file is a *specification by example*, not the product code. The real
package (src/provecheck/) must reproduce every result in test_reference.py.

Core idea: a number printed in a document is a rounded view of a true value.
"2.1M" means the true value lies in [2.05M, 2.15M]. A derived claim is only
CONTRADICTED when no true values inside those intervals could produce it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction as F

SCALES = {
    "k": 10**3, "K": 10**3, "bin": 10**3,
    "m": 10**6, "M": 10**6, "mn": 10**6, "million": 10**6, "milyon": 10**6,
    "b": 10**9, "B": 10**9, "bn": 10**9, "billion": 10**9, "milyar": 10**9,
}
_NUM = re.compile(
    r"^\s*(?P<sign>[-+−]?)\s*[$€£₺]?\s*(?P<body>\d[\d.,  ]*\d|\d)\s*"
    r"(?P<suffix>%|[A-Za-z]+)?\s*$"
)


@dataclass(frozen=True)
class Interval:
    lo: F
    hi: F

    def __post_init__(self):
        if self.lo > self.hi:
            raise ValueError("empty interval")

    def overlaps(self, other: "Interval") -> bool:
        return self.lo <= other.hi and other.lo <= self.hi

    def contains(self, x: F) -> bool:
        return self.lo <= x <= self.hi

    def __add__(self, o):
        return Interval(self.lo + o.lo, self.hi + o.hi)

    def __sub__(self, o):
        return Interval(self.lo - o.hi, self.hi - o.lo)

    def __mul__(self, o):
        p = [self.lo * o.lo, self.lo * o.hi, self.hi * o.lo, self.hi * o.hi]
        return Interval(min(p), max(p))

    def __truediv__(self, o):
        if o.lo <= 0 <= o.hi:
            raise ZeroDivisionError("divisor interval contains zero")
        q = [self.lo / o.lo, self.lo / o.hi, self.hi / o.lo, self.hi / o.hi]
        return Interval(min(q), max(q))


@dataclass(frozen=True)
class Num:
    """A number exactly as printed, plus what the print implies."""
    text: str
    point: F          # value as printed (2.1M -> 2100000)
    half_unit: F      # half of the last printed digit, in base units
    is_percent: bool = False
    exact: bool = False

    @property
    def interval(self) -> Interval:
        if self.exact:
            return Interval(self.point, self.point)
        return Interval(self.point - self.half_unit, self.point + self.half_unit)


def parse_number(text: str, locale: str = "en", exact: bool = False) -> Num:
    """Parse a printed number. locale 'en': 1,234.5  |  'eu' (tr, de, ...): 1.234,5"""
    m = _NUM.match(text)
    if not m:
        raise ValueError(f"not a number: {text!r}")
    body = m.group("body").replace(" ", "").replace(" ", "")
    thousands, decimal = (",", ".") if locale == "en" else (".", ",")
    body = body.replace(thousands, "")
    if decimal in body:
        whole, frac = body.split(decimal)
    else:
        whole, frac = body, ""
    decimals = len(frac)
    value = F(int(whole + frac), 10**decimals)
    suffix = m.group("suffix") or ""
    is_percent = suffix == "%"
    scale = 1 if is_percent or not suffix else SCALES.get(suffix)
    if scale is None:
        raise ValueError(f"unknown suffix: {suffix!r}")
    if m.group("sign") in ("-", "−"):
        value = -value
    return Num(text, value * scale, F(scale, 2 * 10**decimals), is_percent, exact)


# --- relations (each returns (point, interval) of the value the document should print) ---

def _pair(fn, nums):
    return fn([n.point for n in nums]), fn([n.interval for n in nums])


def rel_sum(nums):
    def f(xs):
        acc = xs[0]
        for x in xs[1:]:
            acc = acc + x
        return acc
    return _pair(f, nums)


def rel_pct_change(old: Num, new: Num):
    """(new / old - 1) * 100, as a percentage."""
    hundred_i, one_i = Interval(F(100), F(100)), Interval(F(1), F(1))
    point = (new.point / old.point - 1) * 100
    interval = (new.interval / old.interval - one_i) * hundred_i
    return point, interval


def rel_pct_of(part: Num, whole: Num):
    point = part.point / whole.point * 100
    interval = (part.interval / whole.interval) * Interval(F(100), F(100))
    return point, interval


VERIFIED, SUSPECT, CONTRADICTED = "verified", "suspect", "contradicted"


def judge(claimed: Num, point: F, interval: Interval) -> str:
    """The whole verdict rule.

    verified     - recomputing from the printed operands rounds to the printed claim
    contradicted - no true values behind the printed operands can produce the claim
    suspect      - possible only if operands sit at the edge of their rounding
    """
    if claimed.interval.contains(point):
        return VERIFIED
    if not claimed.interval.overlaps(interval):
        return CONTRADICTED
    return SUSPECT
