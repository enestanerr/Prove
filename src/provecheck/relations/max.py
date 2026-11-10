"""max: the largest of a1 ... an."""

from provecheck.intervals import Interval
from provecheck.relations import Value, relation, same_kind


@relation("max", min_args=1, template="max({,})", summary="the largest of a1 ... an")
def max_(args: list[Value]) -> Value:
    kind = same_kind(args, "max")
    rng = Interval(max(a.range.lo for a in args), max(a.range.hi for a in args))
    return Value(max(a.point for a in args), rng, kind)
