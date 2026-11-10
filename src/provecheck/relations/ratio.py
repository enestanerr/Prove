"""ratio: a / b as a plain multiple. For a share printed as a percentage use pct_of."""

from provecheck.relations import RelationError, Value, divide, relation


@relation(
    "ratio",
    min_args=2,
    max_args=2,
    template="{0} ÷ {1}",
    summary="a ÷ b as a plain multiple (for a percentage use pct_of)",
)
def ratio(args: list[Value]) -> Value:
    a, b = (x.as_fraction() for x in args)
    if b.point == 0:
        raise RelationError("division-by-zero", "ratio: the divisor is zero")
    return Value(a.point / b.point, divide(a.range, b.range, "ratio"))
