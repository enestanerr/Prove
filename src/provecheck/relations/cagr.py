"""cagr: ((end / start) ^ (1 / years) - 1) × 100.

The one relation that leaves exact rationals. It is evaluated with ``decimal``
at 50 digits and the range is pushed outward by one unit in the last place.
"""

from decimal import ROUND_CEILING, ROUND_FLOOR, Context, Decimal
from fractions import Fraction

from provecheck.intervals import outward, to_decimal
from provecheck.numbers import PERCENT
from provecheck.relations import RelationError, Value, divide, relation, same_kind

_CTX = Context(prec=50)


def _rate(ratio: Decimal, years: Decimal) -> Decimal:
    return (_CTX.power(ratio, _CTX.divide(Decimal(1), years)) - 1) * 100


@relation(
    "cagr",
    min_args=3,
    max_args=3,
    template="({1} ÷ {0})^(1 ÷ {2}) − 1",
    summary="((end ÷ start)^(1 ÷ years) − 1) × 100; args are start, end, years",
)
def cagr(args: list[Value]) -> Value:
    start, end, years = args
    same_kind([start, end], "cagr")
    if start.range.lo <= 0 or end.range.lo <= 0:
        raise RelationError("bad-args", "cagr: start and end must be positive")
    if years.range.lo <= 0:
        raise RelationError("bad-args", "cagr: years must be positive")
    ratio = divide(end.range, start.range, "cagr")
    corners = [
        _rate(to_decimal(r, rnd), to_decimal(y, rnd))
        for r in (ratio.lo, ratio.hi)
        for y in (years.range.lo, years.range.hi)
        for rnd in (ROUND_FLOOR, ROUND_CEILING)
    ]
    point = _rate(to_decimal(end.point / start.point), to_decimal(years.point))
    return Value(Fraction(point), outward(min(corners), max(corners)), PERCENT)
