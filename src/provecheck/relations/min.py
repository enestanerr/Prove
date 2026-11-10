"""min: the smallest of a1 ... an."""

from provecheck.intervals import Interval
from provecheck.relations import Value, relation, same_kind


@relation("min", min_args=1, template="min({,})", summary="the smallest of a1 ... an")
def min_(args: list[Value]) -> Value:
    kind = same_kind(args, "min")
    rng = Interval(min(a.range.lo for a in args), min(a.range.hi for a in args))
    return Value(min(a.point for a in args), rng, kind)
