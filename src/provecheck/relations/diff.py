"""diff: a - b."""

from provecheck.relations import Value, relation, same_kind


@relation("diff", min_args=2, max_args=2, template="{0} − {1}", summary="a − b")
def diff(args: list[Value]) -> Value:
    kind = same_kind(args, "diff")
    a, b = args
    return Value(a.point - b.point, a.range - b.range, kind)
