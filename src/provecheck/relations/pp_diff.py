"""pp_diff: a% - b% in percentage points."""

from provecheck.numbers import PERCENT
from provecheck.relations import RelationError, Value, relation


@relation(
    "pp_diff",
    min_args=2,
    max_args=2,
    template="{0} − {1}",
    summary="a% − b% in percentage points; both operands must be percentages",
)
def pp_diff(args: list[Value]) -> Value:
    a, b = args
    if a.kind != PERCENT or b.kind != PERCENT:
        raise RelationError("unit-mismatch", "pp_diff: both operands must be percentages")
    return Value(a.point - b.point, a.range - b.range, PERCENT)
