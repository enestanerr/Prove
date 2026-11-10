"""Chart checks (SPEC §8).

The model reads each mark twice and gives an interval both times. This module
merges the two reads, enforces a minimum width, and compares the result with a
printed number. Assurance is ``read``: the comparison is exact, the reading is
the model's.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal
from fractions import Fraction

from provecheck.intervals import Interval, Target, outward, to_decimal
from provecheck.numbers import parse_decimal, parse_scale

MIN_WIDTH = Fraction(2, 100)  # of the axis span
_CTX = Context(prec=50)
# A printed number and a reading that differ by exactly one of these factors point at
# a unit mix-up in the claims file (thousands vs millions, share vs percent), not at
# an error in the document.
SCALE_FACTORS = tuple(Fraction(10) ** e for e in (3, 6, 9, -3, -6, -9))
PERCENT_FACTORS = (Fraction(100), Fraction(1, 100))


@dataclass(frozen=True)
class Axis:
    lo: Fraction
    hi: Fraction
    log: bool = False
    multiplier: Fraction = Fraction(1)

    @classmethod
    def of(cls, chart: dict) -> Axis:
        axis = chart.get("y_axis")
        if axis is None:  # a pie: slices are shares of 100
            return cls(Fraction(0), Fraction(100))
        return cls(
            parse_decimal(axis["min"]),
            parse_decimal(axis["max"]),
            axis.get("scale", "linear") == "log",
            parse_scale(axis.get("multiplier")),
        )


@dataclass(frozen=True)
class Reading:
    """One mark after the two-read protocol."""

    status: str  # "ok" | "unstable" | "single-read"
    a: Interval
    b: Interval | None
    final: Interval | None  # in base units (axis units × multiplier)


def _interval(r: dict) -> Interval:
    return Interval(parse_decimal(r["lo"]), parse_decimal(r["hi"]))


def _min_width(iv: Interval, axis: Axis) -> Interval:
    """A reading narrower than 2% of the axis span is widened to 2%."""
    if not axis.log:
        need = (axis.hi - axis.lo) * MIN_WIDTH
        return iv if iv.width >= need else iv.widen((need - iv.width) / 2)
    if iv.lo <= 0:
        return iv
    # On a log axis the span is measured in log space: hi/lo must reach (max/min)^0.02.
    lo, hi = to_decimal(iv.lo), to_decimal(iv.hi)
    span = _CTX.divide(to_decimal(axis.hi), to_decimal(axis.lo))
    factor = _CTX.power(span, Decimal(MIN_WIDTH.numerator) / Decimal(MIN_WIDTH.denominator))
    if _CTX.divide(hi, lo) >= factor:
        return iv
    centre, half = _CTX.sqrt(_CTX.multiply(lo, hi)), _CTX.sqrt(factor)
    wide = outward(_CTX.divide(centre, half), _CTX.multiply(centre, half))
    return wide.hull(iv)


def read_mark(mark: dict, axis: Axis) -> Reading:
    a = _interval(mark["read_a"])
    if mark.get("read_b") is None:
        return Reading("single-read", a, None, None)
    b = _interval(mark["read_b"])
    if not a.overlaps(b):
        return Reading("unstable", a, b, None)
    final = _min_width(a.hull(b), axis).scale(axis.multiplier)
    return Reading("ok", a, b, final)


def compare(target: Target, reading: Interval) -> str:
    """``contradicted`` only when the printed number and the reading cannot meet."""
    return "verified" if target.overlaps(reading) else "contradicted"


def scale_confusion(target: Target, reading: Interval, percent: bool = False) -> Fraction | None:
    """The factor that would reconcile the two, when they are off by a unit scale."""
    if reading.lo <= 0 or target.contains(0):
        return None  # anything near zero stays near zero at any scale
    for k in SCALE_FACTORS + (PERCENT_FACTORS if percent else ()):
        if target.overlaps(reading.scale(k)):
            return k
    return None


def total(readings: list[Interval]) -> Interval:
    out = readings[0]
    for r in readings[1:]:
        out = out + r
    return out


def order(relation: str, mark: Interval, others: list[Interval]) -> str:
    """An ordering claim is contradicted only when the readings rule it out."""
    if relation in ("largest", "gt"):
        refuted = any(o.lo > mark.hi for o in others)
    else:
        refuted = any(o.hi < mark.lo for o in others)
    return "contradicted" if refuted else "verified"
