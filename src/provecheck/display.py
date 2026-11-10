"""Turn exact fractions into the text a reader sees. Floats never touch a verdict."""

from __future__ import annotations

from fractions import Fraction

from provecheck.intervals import Interval
from provecheck.numbers import PERCENT, Printed


def exact(x: Fraction) -> str:
    """Lossless text form for JSON: ``"4792"`` or ``"200/21"``."""
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def fixed(x: Fraction, places: int, keep: int = 0) -> str:
    """Round half-even to ``places`` decimals, group thousands, keep at least ``keep`` decimals."""
    q = round(x * 10**places)
    digits = str(abs(q)).rjust(places + 1, "0")
    whole, frac = (digits[:-places], digits[-places:]) if places else (digits, "")
    frac = frac.rstrip("0").ljust(keep, "0")
    return ("-" if q < 0 else "") + f"{int(whole):,}" + (f".{frac}" if frac else "")


def show(
    x: Fraction, like: Printed | None = None, kind: str | None = None, pp: bool = False
) -> str:
    """Format a value the way the printed number ``like`` is written, with a little more precision.

    ``pp`` marks a difference of percentages, shown in percentage points.
    """
    kind = kind or (like.kind if like else "plain")
    decimals = like.decimals if like else 0
    if kind == PERCENT:
        places = max(2, decimals + 1)
        unit = " pp" if pp or (like is not None and like.suffix == "pp") else "%"
        return fixed(x, places, places) + unit
    if like is not None and like.scale != 1:
        suffix = like.suffix if like.kind != PERCENT else ""
        if len(suffix) > 2:
            suffix = " " + suffix
        return fixed(x / like.scale, decimals + 2, decimals) + suffix
    if x.denominator == 1:
        return f"{x.numerator:,}"
    return fixed(x, max(decimals + 2, 2), decimals)


def show_range(
    rng: Interval, like: Printed | None = None, kind: str | None = None, pp: bool = False
) -> str:
    lo, hi = show(rng.lo, like, kind, pp), show(rng.hi, like, kind, pp)
    return f"{lo} to {hi}" if rng.lo < 0 else f"{lo}–{hi}"


def plain(x: Fraction, places: int = 2) -> str:
    """A bare number such as a chart reading: up to ``places`` decimals, no unit."""
    return fixed(x, places)
