"""pct_change: (new / old - 1) × 100."""

from provecheck.numbers import PERCENT
from provecheck.relations import HUNDRED, ONE, RelationError, Value, divide, relation, same_kind


@relation(
    "pct_change",
    min_args=2,
    max_args=2,
    template="{1} ÷ {0} − 1",
    summary="(new ÷ old − 1) × 100, a percentage; args are old, new",
)
def pct_change(args: list[Value]) -> Value:
    same_kind(args, "pct_change")
    old, new = args
    if old.point == 0:
        raise RelationError("division-by-zero", "pct_change: the old value is zero")
    rng = (divide(new.range, old.range, "pct_change") - ONE) * HUNDRED
    return Value((new.point / old.point - 1) * 100, rng, PERCENT)
