"""Exact interval arithmetic over ``fractions.Fraction`` (SPEC §2).

``Interval`` is closed and finite: it is what a printed number or a recomputed
value can be. ``Target`` is what a claim allows: usually the printed number's
interval, but a hedge ("over 50%", "at least 3") can open or unbound one side.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Context, Decimal
from fractions import Fraction

_PREC = 50


@dataclass(frozen=True)
class Interval:
    lo: Fraction
    hi: Fraction

    def __post_init__(self) -> None:
        object.__setattr__(self, "lo", Fraction(self.lo))
        object.__setattr__(self, "hi", Fraction(self.hi))
        if self.lo > self.hi:
            raise ValueError(f"empty interval: {self.lo} > {self.hi}")

    @classmethod
    def point(cls, x: Fraction | int) -> Interval:
        return cls(Fraction(x), Fraction(x))

    @property
    def width(self) -> Fraction:
        return self.hi - self.lo

    @property
    def mid(self) -> Fraction:
        return (self.lo + self.hi) / 2

    @property
    def is_point(self) -> bool:
        return self.lo == self.hi

    def contains(self, x: Fraction | int) -> bool:
        return self.lo <= x <= self.hi

    def contains_interval(self, other: Interval) -> bool:
        return self.lo <= other.lo and other.hi <= self.hi

    def overlaps(self, other: Interval) -> bool:
        return self.lo <= other.hi and other.lo <= self.hi

    def widen(self, amount: Fraction | int) -> Interval:
        """Grow by ``amount`` on each side."""
        if amount < 0:
            raise ValueError("widen amount must not be negative")
        return Interval(self.lo - amount, self.hi + amount)

    def hull(self, other: Interval) -> Interval:
        """Smallest interval containing both (the union, made convex)."""
        return Interval(min(self.lo, other.lo), max(self.hi, other.hi))

    def scale(self, k: Fraction | int) -> Interval:
        a, b = self.lo * k, self.hi * k
        return Interval(min(a, b), max(a, b))

    def __neg__(self) -> Interval:
        return Interval(-self.hi, -self.lo)

    def __add__(self, o: Interval) -> Interval:
        return Interval(self.lo + o.lo, self.hi + o.hi)

    def __sub__(self, o: Interval) -> Interval:
        return Interval(self.lo - o.hi, self.hi - o.lo)

    def __mul__(self, o: Interval) -> Interval:
        p = (self.lo * o.lo, self.lo * o.hi, self.hi * o.lo, self.hi * o.hi)
        return Interval(min(p), max(p))

    def __truediv__(self, o: Interval) -> Interval:
        if o.lo <= 0 <= o.hi:
            raise ZeroDivisionError("divisor interval contains zero")
        q = (self.lo / o.lo, self.lo / o.hi, self.hi / o.lo, self.hi / o.hi)
        return Interval(min(q), max(q))


@dataclass(frozen=True)
class Target:
    """The set of values a claim allows. ``None`` means unbounded on that side."""

    lo: Fraction | None
    hi: Fraction | None
    lo_open: bool = False
    hi_open: bool = False

    @classmethod
    def of(cls, interval: Interval) -> Target:
        return cls(interval.lo, interval.hi)

    def contains(self, x: Fraction | int) -> bool:
        if self.lo is not None and (x < self.lo or (self.lo_open and x == self.lo)):
            return False
        if self.hi is not None and (x > self.hi or (self.hi_open and x == self.hi)):
            return False
        return True

    def overlaps(self, other: Interval) -> bool:
        if self.lo is not None and (other.hi < self.lo or (self.lo_open and other.hi == self.lo)):
            return False
        if self.hi is not None and (other.lo > self.hi or (self.hi_open and other.lo == self.hi)):
            return False
        return True


def to_decimal(x: Fraction, rounding: str | None = None) -> Decimal:
    """Fraction -> Decimal at 50 digits, rounded down/up when asked."""
    ctx = Context(prec=_PREC, rounding=rounding) if rounding else Context(prec=_PREC)
    return ctx.divide(Decimal(x.numerator), Decimal(x.denominator))


def outward(lo: Decimal, hi: Decimal) -> Interval:
    """Decimal bounds -> Interval, pushed outward by one unit in the last place."""

    def ulp(d: Decimal) -> Decimal:
        return (
            Decimal(1).scaleb(d.adjusted() - (_PREC - 5)) if d != 0 else Decimal(1).scaleb(-_PREC)
        )

    lo_d = Context(prec=_PREC, rounding=ROUND_FLOOR).subtract(lo, ulp(lo))
    hi_d = Context(prec=_PREC, rounding=ROUND_CEILING).add(hi, ulp(hi))
    return Interval(Fraction(lo_d), Fraction(hi_d))
