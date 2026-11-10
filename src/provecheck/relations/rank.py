"""rank: an ordering claim such as "largest" or "second highest".

Args: item, a1 ... an, position. The value is the item's place among the item
and the others, 1 being the largest. A negative position counts from the
bottom: -1 is the smallest, -2 the second smallest. The last argument is the
claimed position, so the claim needs no printed target of its own.
"""

from fractions import Fraction

from provecheck.intervals import Interval
from provecheck.relations import RelationError, Value, relation, same_kind


@relation(
    "rank",
    min_args=3,
    template=lambda parts: f"place of {parts[0]} among {len(parts) - 1} values",
    summary="args: item, others..., position; 1 = largest, -1 = smallest",
    own_target=True,
)
def rank(args: list[Value]) -> Value:
    item, others, position = args[0], args[1:-1], args[-1]
    same_kind([item, *others], "rank")
    pos = position.point
    if not position.range.is_point or pos.denominator != 1 or pos == 0:
        raise RelationError("bad-args", "rank: position must be a whole number constant, not 0")
    if abs(pos) > len(others) + 1:
        raise RelationError("bad-args", "rank: position is larger than the number of values")
    if pos > 0:  # how many are larger
        point = sum(o.point > item.point for o in others)
        surely = sum(o.range.lo > item.range.hi for o in others)
        maybe = sum(o.range.hi > item.range.lo for o in others)
        return Value(Fraction(1 + point), Interval(1 + surely, 1 + maybe))
    point = sum(o.point < item.point for o in others)
    surely = sum(o.range.hi < item.range.lo for o in others)
    maybe = sum(o.range.lo < item.range.hi for o in others)
    return Value(Fraction(-1 - point), Interval(-1 - maybe, -1 - surely))
