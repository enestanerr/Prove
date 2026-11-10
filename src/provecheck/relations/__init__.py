"""Relations: how a printed number should be computed (SPEC §4).

One module per relation. Each module calls ``@relation(...)`` on a function
``(args: list[Value]) -> Value`` that returns the **point** (computed from the
printed values) and the **range** (computed with interval arithmetic on what
the prints allow). Adding a relation is one new file in this folder plus its
test; nothing else needs to change.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction

from provecheck.intervals import Interval
from provecheck.numbers import PERCENT, PLAIN

HUNDRED = Interval.point(100)
ONE = Interval.point(1)


class RelationError(ValueError):
    """A derivation that cannot be evaluated. ``reason`` becomes the unverified reason."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class Value:
    point: Fraction
    range: Interval
    kind: str = PLAIN  # "plain" or "percent"

    @classmethod
    def exact(cls, x: Fraction | int, kind: str = PLAIN) -> Value:
        return cls(Fraction(x), Interval.point(x), kind)

    def as_fraction(self) -> Value:
        """A percentage as a plain fraction: 20% -> 0.2. Plain values are unchanged."""
        if self.kind != PERCENT:
            return self
        return Value(self.point / 100, self.range.scale(Fraction(1, 100)), PLAIN)


@dataclass(frozen=True)
class Relation:
    name: str
    fn: Callable[[list[Value]], Value]
    min_args: int
    max_args: int | None
    template: str | Callable[[list[str]], str]  # how the computation reads
    summary: str
    own_target: bool = False  # the last argument is the claimed value (rank)

    def __call__(self, args: list[Value]) -> Value:
        return self.fn(args)

    def explain(self, parts: list[str]) -> str:
        """The computation written out, e.g. ``2.30M ÷ 2.10M − 1``.

        Template placeholders: ``{0}``, ``{1}``, ``{-1}`` for single operands,
        ``{+}``, ``{×}``, ``{,}`` for all operands joined, ``{n}`` for their count.
        """
        if callable(self.template):
            return self.template(parts)
        shown = parts
        if len(parts) > 8:
            shown = [*parts[:3], "…", *parts[-2:]]
        out = self.template
        for mark, sep in (("{+}", " + "), ("{×}", " × "), ("{,}", ", ")):
            if mark in out:
                joined = sep.join(shown)
                if len(parts) > 8:
                    joined += f" ({len(parts)} values)"
                out = out.replace(mark, joined)
        out = out.replace("{n}", str(len(parts))).replace("{-1}", parts[-1])
        for i, part in enumerate(parts):
            out = out.replace("{" + str(i) + "}", part)
        return out


REGISTRY: dict[str, Relation] = {}


def relation(
    name: str,
    *,
    min_args: int,
    max_args: int | None = None,
    template: str | Callable[[list[str]], str],
    summary: str,
    own_target: bool = False,
) -> Callable[[Callable[[list[Value]], Value]], Callable[[list[Value]], Value]]:
    def deco(fn: Callable[[list[Value]], Value]) -> Callable[[list[Value]], Value]:
        REGISTRY[name] = Relation(name, fn, min_args, max_args, template, summary, own_target)
        return fn

    return deco


def same_kind(args: list[Value], op: str) -> str:
    """All operands must be the same kind: you cannot add 14% to 3 million."""
    kinds = {a.kind for a in args}
    if len(kinds) > 1:
        raise RelationError(
            "unit-mismatch", f"{op}: percentages and plain numbers are mixed in the operands"
        )
    return kinds.pop()


def divide(a: Interval, b: Interval, op: str) -> Interval:
    try:
        return a / b
    except ZeroDivisionError:
        raise RelationError(
            "division-by-zero", f"{op}: the divisor could be zero within its rounding"
        ) from None


def get(name: str) -> Relation:
    try:
        return REGISTRY[name]
    except KeyError:
        known = ", ".join(sorted(REGISTRY))
        raise RelationError("unknown-op", f"unknown op {name!r}; known ops: {known}") from None


def _load_all() -> None:
    for mod in pkgutil.iter_modules(__path__):
        importlib.import_module(f"{__name__}.{mod.name}")


_load_all()
