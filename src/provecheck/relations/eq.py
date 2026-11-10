"""eq: the same quantity printed in two places (a cross-reference)."""

from provecheck.relations import Value, relation


@relation(
    "eq",
    min_args=1,
    max_args=2,
    template="{-1}",
    summary="the same quantity printed elsewhere; with two args the first is the target",
)
def eq(args: list[Value]) -> Value:
    return args[-1]
