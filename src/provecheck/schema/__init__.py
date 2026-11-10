"""Hand-written validator for ``claims.json`` (schema ``prove.claims.v1``).

It mirrors ``claims.v1.schema.json`` in this folder and adds the checks a JSON
Schema cannot express (ids exist, ops are known, argument counts). The core
stays dependency-free; the JSON Schema file is what other tools can use.
Messages name the exact path so the model can fix its own file.
"""

from __future__ import annotations

import json
from importlib import resources

from provecheck.grounding import EXACT_REASONS
from provecheck.numbers import NumberParseError, parse_const, parse_decimal, parse_scale
from provecheck.relations import REGISTRY

CLAIMS_SCHEMA = "prove.claims.v1"
HEDGES = ("approx", "over", "under", "at_least", "at_most")
CHART_CHECKS = ("label_vs_mark", "text_vs_chart", "table_vs_chart", "parts_sum", "order")
ORDER_RELATIONS = ("largest", "smallest", "gt", "lt")
SOURCE_KINDS = ("doi", "arxiv", "url", "quote")
AXIS_SCALES = ("linear", "log")
MAX_DEPTH = 20


def load_schema(name: str = "claims.v1.schema.json") -> dict:
    return json.loads(resources.files(__name__).joinpath(name).read_text(encoding="utf-8"))


class _V:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def err(self, path: str, msg: str) -> None:
        self.errors.append(f"{path}: {msg}")

    def typed(self, obj: dict, key: str, kind: type | tuple, path: str, required: bool = True):
        """Return obj[key] when it has the right type, else record an error and return None."""
        if key not in obj or obj[key] is None:
            if required:
                self.err(f"{path}.{key}", "is required")
            return None
        val = obj[key]
        if isinstance(val, bool) or not isinstance(val, kind):
            names = kind.__name__ if isinstance(kind, type) else "/".join(k.__name__ for k in kind)
            self.err(f"{path}.{key}", f"must be {names}, got {type(val).__name__}")
            return None
        return val

    def decimal(self, obj: dict, key: str, path: str, required: bool = True) -> None:
        val = self.typed(obj, key, str, path, required)
        if val is not None:
            try:
                parse_decimal(val)
            except NumberParseError:
                self.err(
                    f"{path}.{key}", f'must be a plain decimal string such as "1234.5", got {val!r}'
                )

    def loc(self, obj: dict, path: str, need_quote: bool = True) -> None:
        loc = self.typed(obj, "loc", dict, path)
        if loc is None:
            return
        page = self.typed(loc, "page", int, f"{path}.loc")
        if page is not None and page < 1:
            self.err(f"{path}.loc.page", "pages are numbered from 1")
        quote = self.typed(loc, "quote", str, f"{path}.loc", required=need_quote)
        if quote is not None and not quote.strip():
            self.err(f"{path}.loc.quote", "must not be empty")
        if loc.get("image") is not None and not isinstance(loc["image"], bool):
            self.err(f"{path}.loc.image", "must be true or false")


def _ids(v: _V, items: list, path: str) -> dict[str, dict]:
    seen: dict[str, dict] = {}
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            v.err(f"{path}[{i}]", "must be an object")
            continue
        ident = v.typed(item, "id", str, f"{path}[{i}]")
        if ident is None:
            continue
        if ident in seen:
            v.err(f"{path}[{i}].id", f"duplicate id {ident!r}")
        seen[ident] = item
    return seen


def _number(v: _V, n: dict, path: str) -> None:
    text = v.typed(n, "text", str, path)
    if text is not None and not text.strip():
        v.err(f"{path}.text", "must not be empty")
    v.decimal(n, "value", path)
    decimals = v.typed(n, "decimals", int, path, required=False)
    if decimals is not None and decimals < 0:
        v.err(f"{path}.decimals", "must be 0 or more")
    if n.get("exact") is not None and n["exact"] not in EXACT_REASONS:
        v.err(
            f"{path}.exact",
            f"must be null or one of {', '.join(EXACT_REASONS)}; got {n['exact']!r}",
        )
    if n.get("scale") is not None:
        try:
            parse_scale(n["scale"])
        except NumberParseError as exc:
            v.err(f"{path}.scale", str(exc))
    v.typed(n, "unit", str, path, required=False)
    v.typed(n, "locale", str, path, required=False)
    v.loc(n, path)


def _node(v: _V, node: object, path: str, numbers: dict, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        v.err(path, f"derivation is nested deeper than {MAX_DEPTH}")
        return
    if not isinstance(node, dict):
        v.err(path, 'must be {"ref": …}, {"const": …} or {"op": …, "args": […]}')
        return
    keys = [k for k in ("ref", "const", "op") if k in node]
    if len(keys) != 1:
        v.err(path, 'must have exactly one of "ref", "const", "op"')
        return
    if "ref" in node:
        if node["ref"] not in numbers:
            v.err(f"{path}.ref", f"no number with id {node['ref']!r}")
    elif "const" in node:
        try:
            parse_const(node["const"])
        except NumberParseError:
            v.err(
                f"{path}.const",
                f'must be a decimal string such as "12" or "100%", got {node["const"]!r}',
            )
    else:
        rel = REGISTRY.get(node["op"])
        args = node.get("args")
        if rel is None:
            v.err(
                f"{path}.op", f"unknown op {node['op']!r}; known ops: {', '.join(sorted(REGISTRY))}"
            )
        if not isinstance(args, list):
            v.err(f"{path}.args", "must be a list")
            return
        if rel is not None:
            if len(args) < rel.min_args or (rel.max_args is not None and len(args) > rel.max_args):
                want = (
                    f"exactly {rel.min_args}"
                    if rel.max_args == rel.min_args
                    else f"at least {rel.min_args}"
                    if rel.max_args is None
                    else f"{rel.min_args} to {rel.max_args}"
                )
                v.err(f"{path}.args", f"{node['op']} takes {want} arguments, got {len(args)}")
        for i, arg in enumerate(args):
            _node(v, arg, f"{path}.args[{i}]", numbers, depth + 1)


def _mark_ref(v: _V, mark: object, path: str, chart: dict | None) -> None:
    if not isinstance(mark, dict) or not isinstance(mark.get("label"), str):
        v.err(path, 'must be {"label": …, "series": …}')
        return
    if chart is not None and find_mark(chart, mark) is None:
        v.err(path, f"chart {chart.get('id')!r} has no mark {mark_name(mark)}")


def mark_name(mark: dict) -> str:
    return f"{mark.get('label')!r}" + (f" / {mark['series']!r}" if mark.get("series") else "")


def find_mark(chart: dict, ref: dict) -> dict | None:
    for m in chart.get("marks") or []:
        if isinstance(m, dict) and m.get("label") == ref.get("label"):
            if ref.get("series") is None or m.get("series") == ref.get("series"):
                return m
    return None


def _claim(v: _V, c: dict, path: str, numbers: dict, charts: dict) -> None:
    kind = c.get("kind")
    say = v.typed(c, "say", str, path)
    if say is not None and not say.strip():
        v.err(f"{path}.say", "must be one plain sentence")
    if kind == "derived":
        node = c.get("derivation")
        own_target = isinstance(node, dict) and getattr(
            REGISTRY.get(node.get("op")), "own_target", False
        )
        target = v.typed(c, "target", str, path, required=not own_target)
        if target is not None and target not in numbers:
            v.err(f"{path}.target", f"no number with id {target!r}")
        if c.get("hedge") is not None and c["hedge"] not in HEDGES:
            v.err(
                f"{path}.hedge", f"must be null or one of {', '.join(HEDGES)}; got {c['hedge']!r}"
            )
        if node is None:
            v.err(
                f"{path}.derivation", "is required; leave the number without a claim if it has none"
            )
            return
        _node(v, node, f"{path}.derivation", numbers)
        if isinstance(node, dict) and node.get("op") == "eq" and isinstance(node.get("args"), list):
            if len(node["args"]) == 2 and node["args"][0] != {"ref": target}:
                v.err(
                    f"{path}.derivation.args[0]",
                    "with two arguments, eq's first must be the claim's target",
                )
    elif kind == "chart":
        check = c.get("check")
        if check not in CHART_CHECKS:
            v.err(f"{path}.check", f"must be one of {', '.join(CHART_CHECKS)}; got {check!r}")
        chart = charts.get(c.get("chart"))
        if chart is None:
            v.err(f"{path}.chart", f"no chart with id {c.get('chart')!r}")
        if check != "order":
            target = v.typed(c, "target", str, path)
            if target is not None and target not in numbers:
                v.err(f"{path}.target", f"no number with id {target!r}")
        if check == "parts_sum":
            marks = c.get("marks")
            if marks is not None:
                if not isinstance(marks, list) or not marks:
                    v.err(
                        f"{path}.marks",
                        "must be a non-empty list of marks, or omitted for all marks",
                    )
                else:
                    for i, m in enumerate(marks):
                        _mark_ref(v, m, f"{path}.marks[{i}]", chart)
        else:
            _mark_ref(v, c.get("mark"), f"{path}.mark", chart)
        if check == "order":
            rel = c.get("relation")
            if rel not in ORDER_RELATIONS:
                v.err(
                    f"{path}.relation", f"must be one of {', '.join(ORDER_RELATIONS)}; got {rel!r}"
                )
            if rel in ("gt", "lt"):
                _mark_ref(v, c.get("than"), f"{path}.than", chart)
    else:
        v.err(f"{path}.kind", f'must be "derived" or "chart", got {kind!r}')


def _reading(v: _V, mark: dict, key: str, path: str, required: bool) -> None:
    r = mark.get(key)
    if r is None:
        if required:
            v.err(f"{path}.{key}", 'is required: {"lo": …, "hi": …}')
        return
    if not isinstance(r, dict):
        v.err(f"{path}.{key}", 'must be {"lo": …, "hi": …}')
        return
    v.decimal(r, "lo", f"{path}.{key}")
    v.decimal(r, "hi", f"{path}.{key}")
    try:
        if parse_decimal(r["lo"]) > parse_decimal(r["hi"]):
            v.err(f"{path}.{key}", "lo is greater than hi")
    except (NumberParseError, KeyError, TypeError):
        pass


def _chart(v: _V, g: dict, path: str, numbers: dict) -> None:
    loc = v.typed(g, "loc", dict, path)
    if loc is not None:
        v.typed(loc, "page", int, f"{path}.loc")
    v.typed(g, "type", str, path)
    axis = v.typed(g, "y_axis", dict, path, required=g.get("type") != "pie")
    if axis is not None:
        v.decimal(axis, "min", f"{path}.y_axis")
        v.decimal(axis, "max", f"{path}.y_axis")
        scale = axis.get("scale", "linear")
        if scale not in AXIS_SCALES:
            v.err(f"{path}.y_axis.scale", f"must be one of {', '.join(AXIS_SCALES)}; got {scale!r}")
        try:
            lo, hi = parse_decimal(axis["min"]), parse_decimal(axis["max"])
            if lo >= hi:
                v.err(f"{path}.y_axis", "min must be less than max")
            elif scale == "log" and lo <= 0:
                v.err(f"{path}.y_axis.min", "a log axis cannot start at 0 or below")
        except (NumberParseError, KeyError, TypeError):
            pass
        if axis.get("multiplier") is not None:
            try:
                parse_scale(axis["multiplier"])
            except NumberParseError as exc:
                v.err(f"{path}.y_axis.multiplier", str(exc))
    marks = v.typed(g, "marks", list, path)
    for i, m in enumerate(marks or []):
        mp = f"{path}.marks[{i}]"
        if not isinstance(m, dict):
            v.err(mp, "must be an object")
            continue
        v.typed(m, "label", str, mp)
        v.typed(m, "series", str, mp, required=False)
        _reading(v, m, "read_a", mp, required=True)
        _reading(v, m, "read_b", mp, required=False)
        label = m.get("printed_label")
        if label is not None and label not in numbers:
            v.err(f"{mp}.printed_label", f"no number with id {label!r}")
    notes = g.get("notes")
    if notes is not None and not (
        isinstance(notes, list) and all(isinstance(n, str) for n in notes)
    ):
        v.err(f"{path}.notes", "must be a list of strings")


def validate_claims(data: object) -> list[str]:
    """Return a list of problems; an empty list means the file is valid."""
    v = _V()
    if not isinstance(data, dict):
        return ["claims file: must be a JSON object"]
    if data.get("schema") != CLAIMS_SCHEMA:
        v.err("schema", f'must be "{CLAIMS_SCHEMA}", got {data.get("schema")!r}')
    doc = v.typed(data, "document", dict, "claims file")
    if doc is not None:
        v.typed(doc, "path", str, "document")
        v.typed(doc, "sha256", str, "document", required=False)
        v.typed(doc, "locale", str, "document", required=False)
    for key in ("numbers", "claims"):
        v.typed(data, key, list, "claims file")
    for key in ("charts", "sources", "skipped"):
        v.typed(data, key, list, "claims file", required=False)

    def items(key: str) -> list:
        return data[key] if isinstance(data.get(key), list) else []

    numbers = _ids(v, items("numbers"), "numbers")
    charts = _ids(v, items("charts"), "charts")
    for i, n in enumerate(items("numbers")):
        if isinstance(n, dict):
            _number(v, n, f"numbers[{i}]")
    for i, g in enumerate(items("charts")):
        if isinstance(g, dict):
            _chart(v, g, f"charts[{i}]", numbers)
    _ids(v, items("claims"), "claims")
    for i, c in enumerate(items("claims")):
        if isinstance(c, dict):
            _claim(v, c, f"claims[{i}]", numbers, charts)
    _ids(v, items("sources"), "sources")
    for i, s in enumerate(items("sources")):
        if not isinstance(s, dict):
            continue
        path = f"sources[{i}]"
        if s.get("kind") not in SOURCE_KINDS:
            v.err(
                f"{path}.kind", f"must be one of {', '.join(SOURCE_KINDS)}; got {s.get('kind')!r}"
            )
        v.typed(s, "value", str, path)
        if s.get("kind") == "quote" and not (
            isinstance(s.get("quote"), str) and s["quote"].strip()
        ):
            v.err(f"{path}.quote", "a quote source needs the quoted words")
        v.typed(s, "cited_title", str, path, required=False)
        v.typed(s, "cited_year", int, path, required=False)
        if s.get("loc") is not None:
            v.loc(s, path, need_quote=False)
    for i, s in enumerate(items("skipped")):
        path = f"skipped[{i}]"
        if not isinstance(s, dict):
            v.err(path, "must be an object")
            continue
        reason = v.typed(s, "reason", str, path)
        if reason is not None and not reason.strip():
            v.err(f"{path}.reason", "must say why the number is not checked")
        text = v.typed(s, "text", str, path, required=False)
        quote = (s.get("loc") or {}).get("quote") if isinstance(s.get("loc"), dict) else None
        if text is None and not quote:
            v.err(path, 'needs "text", or a "loc.quote" to skip a whole passage')
    return v.errors
