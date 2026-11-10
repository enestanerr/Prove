"""product: a1 × ... × an. A percentage operand counts as a fraction (20% of 500 = 100)."""

from provecheck.numbers import PERCENT
from provecheck.relations import HUNDRED, Value, relation


@relation(
    "product",
    min_args=2,
    template="{×}",
    summary="a1 × ... × an; a percentage operand counts as a fraction (20% × 500 = 100)",
)
def product(args: list[Value]) -> Value:
    all_percent = all(a.kind == PERCENT for a in args)
    parts = [a.as_fraction() for a in args]
    point, rng = parts[0].point, parts[0].range
    for a in parts[1:]:
        point, rng = point * a.point, rng * a.range
    if all_percent:  # 50% × 50% = 25%
        return Value(point * 100, rng * HUNDRED, PERCENT)
    return Value(point, rng)
