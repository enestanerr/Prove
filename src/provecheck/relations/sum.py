"""sum: a1 + ... + an."""

from provecheck.relations import Value, relation, same_kind


@relation("sum", min_args=1, template="{+}", summary="a1 + ... + an")
def sum_(args: list[Value]) -> Value:
    kind = same_kind(args, "sum")
    point, rng = args[0].point, args[0].range
    for a in args[1:]:
        point, rng = point + a.point, rng + a.range
    return Value(point, rng, kind)
