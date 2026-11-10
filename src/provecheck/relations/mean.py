"""mean: (a1 + ... + an) / n."""

from fractions import Fraction

from provecheck.relations import Value, relation, same_kind


@relation("mean", min_args=1, template="({+}) ÷ {n}", summary="(a1 + ... + an) ÷ n")
def mean(args: list[Value]) -> Value:
    kind = same_kind(args, "mean")
    point, rng = args[0].point, args[0].range
    for a in args[1:]:
        point, rng = point + a.point, rng + a.range
    n = Fraction(1, len(args))
    return Value(point * n, rng.scale(n), kind)
