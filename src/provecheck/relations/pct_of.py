"""pct_of: part / whole × 100."""

from provecheck.numbers import PERCENT
from provecheck.relations import HUNDRED, RelationError, Value, divide, relation, same_kind


@relation(
    "pct_of",
    min_args=2,
    max_args=2,
    template="{0} ÷ {1}",
    summary="part ÷ whole × 100, a percentage",
)
def pct_of(args: list[Value]) -> Value:
    same_kind(args, "pct_of")
    part, whole = args
    if whole.point == 0:
        raise RelationError("division-by-zero", "pct_of: the whole is zero")
    rng = divide(part.range, whole.range, "pct_of") * HUNDRED
    return Value(part.point / whole.point * 100, rng, PERCENT)
