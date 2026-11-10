"""The verdict rule (SPEC §2) and the check pipeline around it.

``judge`` is the whole rule. Everything else in this module prepares its two
inputs (what the claim allows, what the printed operands can produce) and
records how the answer was reached. Guards only ever move a verdict away from
``contradicted``.
"""

from __future__ import annotations

from fractions import Fraction

from provecheck import CONTRADICTED, SUSPECT, UNVERIFIED, VERIFIED, __version__, charts
from provecheck.display import exact, plain, show, show_range
from provecheck.grounding import DocIndex, NumberInfo, ground_number
from provecheck.intervals import Interval, Target
from provecheck.numbers import PERCENT, normalize_locale, parse_const
from provecheck.relations import REGISTRY, RelationError, Value, get
from provecheck.scan import coverage
from provecheck.schema import find_mark, mark_name

VERDICTS_SCHEMA = "prove.verdicts.v1"
HEDGE_WORDS = {
    "approx": "about ",
    "over": "over ",
    "under": "under ",
    "at_least": "at least ",
    "at_most": "at most ",
}
PP_UNITS = {"pp", "ppt", "ppts", "percentage points"}
MARK_WORDS = {
    "bar": "bar",
    "grouped_bar": "bar",
    "stacked_bar": "segment",
    "pie": "slice",
    "line": "point",
}


def judge(target: Target, point: Fraction, rng: Interval) -> str:
    """The three-way rule.

    verified     - recomputing from the printed operands gives what is printed
    contradicted - no true values behind the printed operands can produce the claim
    suspect      - possible only if operands sit at the edge of their rounding
    """
    if target.contains(point):
        return VERIFIED
    if not target.overlaps(rng):
        return CONTRADICTED
    return SUSPECT


class Unusable(Exception):
    """A claim that cannot be judged. It becomes ``unverified`` with this reason."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason, self.message = reason, message


# A mode says how numbers are read: "strict" (as printed), "round" (round figures read
# widely, SPEC §3.2), or a set of number ids to read in the other locale (SPEC §3.1).
Mode = str | frozenset


def _printed(info: NumberInfo, mode: Mode):
    if info.problem is not None:
        raise Unusable(info.problem[0], f"number {info.id} ({info.text!r}): {info.problem[1]}")
    p = info.printed
    if isinstance(mode, frozenset) and info.id in mode and p.flipped() is not None:
        p = p.flipped()
    return p


def _interval(info: NumberInfo, mode: Mode) -> Interval:
    p = _printed(info, mode)
    wide = p.round_interval() if (mode == "round" and not info.exact) else None
    return wide or p.interval(info.exact)


def _target(info: NumberInfo, hedge: str | None, mode: Mode) -> Target:
    """What the claim allows: the printed number's interval, reshaped by a hedge (SPEC §3.3)."""
    p, base = _printed(info, mode), _interval(info, mode)
    if hedge == "approx":
        return Target.of(base.widen(max(p.unit, abs(p.point) * Fraction(5, 100))))
    if hedge == "over":
        return Target(p.point, None, lo_open=True)
    if hedge == "under":
        return Target(None, p.point, hi_open=True)
    if hedge == "at_least":
        return Target(p.point, None)
    if hedge == "at_most":
        return Target(None, p.point)
    return Target.of(base)


def _evaluate(
    node: dict, numbers: dict[str, NumberInfo], mode: Mode, used: list[str]
) -> tuple[Value, str]:
    """Evaluate a derivation tree -> (point and range, the computation written out)."""
    if "ref" in node:
        info = numbers[node["ref"]]
        used.append(info.id)
        return Value(_printed(info, mode).point, _interval(info, mode), info.kind), info.text
    if "const" in node:
        value, kind = parse_const(node["const"])
        return Value.exact(value, kind), str(node["const"])
    rel = get(node["op"])
    values, texts = [], []
    for arg in node["args"]:
        value, text = _evaluate(arg, numbers, mode, used)
        values.append(value)
        texts.append(f"({text})" if "op" in arg else text)
    return rel(values), rel.explain(texts)


def _round_note(infos: list[NumberInfo]) -> str:
    parts = []
    for info in infos:
        p = info.printed
        if p is not None and not info.exact and p.round_interval() is not None:
            parts.append(
                f"{info.text} may be rounded to the nearest {_factor(p.scale * 10**p.round_zeros)}"
            )
    return "Not ruled out, because " + " and ".join(parts) + "."


def _unit(info: NumberInfo) -> str:
    return str(info.entry.get("unit") or "").strip().lower()


def _factor(k: Fraction) -> str:
    return show(k) if k >= 1 else f"1/{show(1 / k)}"


def _verified_in_other_locale(attempt, infos: list[NumberInfo]) -> frozenset | None:
    """Would the claim hold if some numbers were read with the other decimal separator?

    1,234 is 1234 in English notation and 1.234 in European notation (SPEC §3.1).
    Tried: all ambiguous numbers, those read as thousands, those read as decimals,
    then each one alone.
    """
    amb = [i for i in infos if i.printed.alt is not None]
    if not amb:
        return None
    candidates = [
        frozenset(i.id for i in amb),
        frozenset(i.id for i in amb if i.printed.decimals == 0),
        frozenset(i.id for i in amb if i.printed.decimals != 0),
        *[frozenset([i.id]) for i in amb[:12]],
    ]
    for ids in dict.fromkeys(c for c in candidates if c):
        try:
            if attempt(ids)[0] == VERIFIED:
                return ids
        except (Unusable, RelationError):
            continue
    return None


def _scale_confusion(target: Target, value: Value) -> Fraction | None:
    """The factor of 1,000 that would reconcile a contradicted claim, if there is one.

    Thousands against millions is almost always a unit left out of the claims
    file, not an error in the document, so it is reported as unverified.
    """
    for k in charts.SCALE_FACTORS:
        if value.range.lo > 0 or value.range.hi < 0:
            hit = target.overlaps(value.range.scale(k))
        else:
            hit = value.point != 0 and target.contains(value.point * k)
        if hit:
            return k
    return None


def _number_ref(info: NumberInfo) -> dict:
    loc = info.entry.get("loc") or {}
    return {"id": info.id, "text": info.text, "page": loc.get("page"), "quote": loc.get("quote")}


def _unverified(rec: dict, reason: str, message: str) -> dict:
    rec.update(verdict=UNVERIFIED, reason=reason, message=message)
    return rec


def _derived(claim: dict, numbers: dict[str, NumberInfo]) -> dict:
    node, hedge = claim["derivation"], claim.get("hedge")
    top = REGISTRY.get(node.get("op"))
    own_target = bool(top and top.own_target)
    tinfo = numbers.get(claim.get("target")) if claim.get("target") else None
    where = tinfo
    if own_target and "ref" in node["args"][0]:  # a rank claim sits where its item is printed
        where = numbers[node["args"][0]["ref"]]
    rec = {
        "id": claim["id"], "kind": "derived", "verdict": None, "assurance": "computed",
        "reason": None, "message": None, "say": claim.get("say"), "hedge": hedge,
        "target": _number_ref(where) if where else None,
        "computation": None, "point": None, "range": None, "display": None,
        "sentence": None, "notes": [], "numbers": [],
    }  # fmt: skip

    def attempt(mode: Mode) -> tuple[str, Value, str, list[str]]:
        used: list[str] = []
        value, comp = _evaluate(node, numbers, mode, used)
        if own_target:
            claimed, _ = _evaluate(node["args"][-1], numbers, mode, [])
            return judge(Target.of(claimed.range), value.point, value.range), value, comp, used
        target = _target(tinfo, hedge, mode)
        if tinfo.kind != value.kind:
            want = "a percentage" if tinfo.kind == PERCENT else "a plain number"
            got = "a percentage" if value.kind == PERCENT else "a plain number"
            raise Unusable(
                "unit-mismatch", f"the printed number is {want} but the derivation gives {got}"
            )
        verdict = judge(target, value.point, value.range)
        if verdict == SUSPECT and node.get("op") == "eq" and hedge in (None, "approx"):
            # Two prints of one quantity agree when either one rounds to the other.
            if value.range.contains(_printed(tinfo, mode).point):
                verdict = VERIFIED
        return verdict, value, comp, used

    try:
        verdict, value, comp, used = attempt("strict")
    except Unusable as exc:
        return _unverified(rec, exc.reason, exc.message)
    except RelationError as exc:
        return _unverified(rec, exc.reason, str(exc))

    ids = list(dict.fromkeys(used + ([tinfo.id] if tinfo else [])))
    infos = [numbers[i] for i in ids]
    rec["numbers"] = ids
    like = tinfo.printed if tinfo else None
    pp = node.get("op") == "pp_diff" or bool(tinfo and _unit(tinfo) in PP_UNITS)
    if tinfo:
        printed = HEDGE_WORDS.get(hedge, "") + tinfo.text
        if pp and like.kind != PERCENT:  # "2.5" under a unit of percentage points
            printed += " pp"
    else:
        printed = f"place {abs(int(node['args'][-1]['const']))}"
    rec["computation"] = comp
    rec["point"] = exact(value.point)
    rec["range"] = [exact(value.range.lo), exact(value.range.hi)]
    rec["display"] = {
        "point": show(value.point, like, value.kind, pp),
        "range": None if value.range.is_point else show_range(value.range, like, value.kind, pp),
        "printed": printed,
    }
    if own_target:
        end = "largest" if value.point > 0 else "smallest"
        rng = value.range if value.point > 0 else -value.range
        sentence = f"{comp}, counting from the {end}: {abs(value.point)}"
        if not rng.is_point:
            sentence += f"; possible places {rng.lo}–{rng.hi}"
        rec["display"].update(point=str(abs(value.point)), range=None)
        rec["sentence"] = sentence + f"; the document claims {printed}"
    elif node.get("op") == "eq":
        rec["sentence"] = f"printed as {comp} elsewhere; the document says {printed}"
    else:
        sentence = f"{comp} = {rec['display']['point']}"
        if rec["display"]["range"]:
            sentence += f"; possible range {rec['display']['range']}"
        rec["sentence"] = sentence + f"; the document says {printed}"

    strict = verdict
    if verdict == CONTRADICTED and any(
        i.printed.round_interval() is not None and not i.exact for i in infos
    ):
        # SPEC §3.2: a round figure such as 2,300,000 may be rounded to its last non-zero digit.
        if attempt("round")[0] != CONTRADICTED:
            verdict = SUSPECT
            rec["notes"].append(_round_note(infos))
    if verdict == CONTRADICTED and not own_target and hedge in (None, "approx"):
        k = _scale_confusion(_target(tinfo, hedge, "strict"), value)
        if k is not None:
            return _unverified(
                rec,
                "scale-mismatch",
                f"the recomputed value and the printed number differ by a factor of {_factor(k)}; "
                "the units in the claim are probably mis-specified (check scale)",
            )
    if any(i.assurance == "read" for i in infos):
        rec["assurance"] = "read"
        if verdict == CONTRADICTED:
            verdict = SUSPECT
            rec["notes"].append(
                "Rests on a number read from an image with no text layer, so it is not "
                "reported as contradicted."
            )
    flipped = None
    if strict in (CONTRADICTED, SUSPECT):
        flipped = _verified_in_other_locale(attempt, infos)
    if flipped:
        texts = ", ".join(i.text for i in infos if i.id in flipped)
        message = (
            f"the number format is ambiguous: reading {texts} with the other decimal "
            "separator would make this claim verified (set the number's locale)"
        )
        if verdict == CONTRADICTED:
            return _unverified(rec, "ambiguous-format", message)
        rec["notes"].append(message[0].upper() + message[1:] + ".")
    rec["verdict"] = verdict
    return rec


def _reading_text(iv: Interval) -> str:
    return plain(iv.lo) if iv.is_point else f"{plain(iv.lo)}–{plain(iv.hi)}"


def _chart(claim: dict, chart_defs: dict[str, dict], numbers: dict[str, NumberInfo]) -> dict:
    chart, check, hedge = chart_defs[claim["chart"]], claim["check"], claim.get("hedge")
    axis = charts.Axis.of(chart)
    loc = chart.get("loc") or {}
    tinfo = numbers.get(claim.get("target")) if claim.get("target") else None
    rec = {
        "id": claim["id"], "kind": "chart", "check": check, "verdict": None, "assurance": "read",
        "reason": None, "message": None, "say": claim.get("say"), "hedge": hedge,
        "target": _number_ref(tinfo) if tinfo else None,
        "chart": {
            "id": chart["id"], "figure": loc.get("figure"), "page": loc.get("page"),
            "type": chart.get("type"), "unit": (chart.get("y_axis") or {}).get("unit"),
            "image": chart.get("image"), "notes": list(chart.get("notes") or []),
        },
        "marks": [], "display": None, "sentence": None, "notes": [],
        "numbers": [tinfo.id] if tinfo else [],
    }  # fmt: skip

    if check == "parts_sum":
        refs = claim.get("marks") or chart["marks"]
    elif check == "order" and claim["relation"] in ("gt", "lt"):
        refs = [claim["mark"], claim["than"]]
    elif check == "order":
        first = find_mark(chart, claim["mark"])
        series = claim["mark"].get("series")
        refs = [first] + [
            m
            for m in chart["marks"]
            if m is not first and (series is None or m.get("series") == series)
        ]
    else:
        refs = [claim["mark"]]
    readings = []
    for ref in refs:
        mark = find_mark(chart, ref)
        r = charts.read_mark(mark, axis)
        readings.append(r)
        rec["marks"].append(
            {
                "label": mark.get("label"), "series": mark.get("series"), "status": r.status,
                "read_a": _reading_text(r.a), "read_b": _reading_text(r.b) if r.b else None,
                "final": _reading_text(r.final.scale(1 / axis.multiplier)) if r.final else None,
            }
        )  # fmt: skip
    for status, why in (
        (
            "unstable",
            "the two readings of {} do not overlap, so the mark could not be read reliably",
        ),
        ("single-read", "{} was read only once; a second reading from a 2× crop is required"),
    ):
        bad = [
            mark_name(m) for m, r in zip(rec["marks"], readings, strict=True) if r.status == status
        ]
        if bad:
            reason = "unstable-reading" if status == "unstable" else "single-read"
            return _unverified(rec, reason, why.format(", ".join(bad)))

    word = MARK_WORDS.get(chart.get("type"), "mark")
    where = f" in {loc['figure']}" if loc.get("figure") else ""
    first = rec["marks"][0]
    if check == "order":
        relation = claim["relation"]
        verdict = charts.order(relation, readings[0].final, [r.final for r in readings[1:]])
        if relation in ("gt", "lt"):
            other = rec["marks"][1]
            words = "above" if relation == "gt" else "below"
            rec["sentence"] = (
                f"the {first['label']} {word}{where} reads {first['final']} and the "
                f"{other['label']} {word} reads {other['final']}; the document puts "
                f"{first['label']} {words} {other['label']}"
            )
        else:
            rest = ", ".join(f"{m['label']} {m['final']}" for m in rec["marks"][1:])
            rec["sentence"] = (
                f"the {first['label']} {word}{where} reads {first['final']}; the others read "
                f"{rest}; the document calls {first['label']} the {relation}"
            )
        rec["verdict"] = verdict
        return rec

    try:
        target = _target(tinfo, hedge, "strict")
        wide = _target(tinfo, hedge, "round")
    except Unusable as exc:
        return _unverified(rec, exc.reason, exc.message)
    reading = charts.total([r.final for r in readings])
    shown = _reading_text(reading.scale(1 / axis.multiplier))
    printed = HEDGE_WORDS.get(hedge, "") + tinfo.text
    rec["display"] = {"reading": shown, "printed": printed}
    if check == "parts_sum":
        rec["sentence"] = (
            f"the {len(readings)} {word}s{where} add up to {shown}; the document says {printed}"
        )
    else:
        rec["sentence"] = (
            f"the {first['label']} {word}{where} reads {shown} "
            f"(first reading {first['read_a']}, second reading {first['read_b']}); "
            f"the document says {printed}"
        )
    verdict = charts.compare(target, reading)
    if verdict == CONTRADICTED and wide.overlaps(reading):
        verdict = SUSPECT
        rec["notes"].append(_round_note([tinfo]))
    if verdict == CONTRADICTED and hedge in (None, "approx"):
        k = charts.scale_confusion(target, reading, percent=tinfo.kind == PERCENT)
        if k is not None:
            return _unverified(
                rec,
                "scale-mismatch",
                f"the reading and the printed number differ by a factor of {_factor(k)}; the axis "
                "unit or the number's scale is probably mis-specified",
            )
    rec["verdict"] = verdict
    return rec


def _refs(node: object) -> list[str]:
    if not isinstance(node, dict):
        return []
    if "ref" in node:
        return [node["ref"]]
    return [r for arg in node.get("args") or [] for r in _refs(arg)]


def check_claims(claims: dict, doc: dict | None = None) -> dict:
    """Judge every claim in a validated claims file against the document text."""
    index = DocIndex(doc)
    document = claims.get("document") or {}
    locale = normalize_locale(document.get("locale") or (doc or {}).get("locale"))
    numbers = {n["id"]: ground_number(n, index, locale) for n in claims["numbers"]}
    chart_defs = {g["id"]: g for g in claims.get("charts") or []}

    records, referenced = [], set()
    for claim in claims["claims"]:
        if claim["kind"] == "chart":
            records.append(_chart(claim, chart_defs, numbers))
        else:
            records.append(_derived(claim, numbers))
            referenced.update(_refs(claim["derivation"]))
        if claim.get("target"):
            referenced.add(claim["target"])
    for g in chart_defs.values():
        referenced.update(m["printed_label"] for m in g["marks"] if m.get("printed_label"))

    unchecked = []
    for info in numbers.values():
        if info.id not in referenced:
            ref = _number_ref(info)
            ref["reason"] = info.problem[0] if info.problem else "no-derivation"
            unchecked.append(ref)

    sources = [
        {
            "id": s["id"], "kind": s["kind"], "value": s["value"],
            "cited_title": s.get("cited_title"), "page": (s.get("loc") or {}).get("page"),
            "verdict": UNVERIFIED, "assurance": "resolved", "reason": "not-run",
            "message": "Sources were not checked. Run `provecheck sources`.",
        }
        for s in claims.get("sources") or []
    ]  # fmt: skip

    warnings = []
    theirs, ours = document.get("sha256"), (doc or {}).get("sha256")
    if theirs and ours and set(theirs) != {"0"} and theirs != ours:
        warnings.append(
            "The claims file was written for a different version of the document (sha256 differs)."
        )
    if doc is None:
        warnings.append(
            "No document text was given (--doc), so numbers could not be grounded. "
            "Every verdict rests on the model's reading and none is reported as contradicted."
        )

    skipped: dict[tuple[str, str], int] = {}
    for s in claims.get("skipped") or []:
        key = (s.get("text") or "(passage)", s["reason"])
        skipped[key] = skipped.get(key, 0) + 1

    return {
        "schema": VERDICTS_SCHEMA,
        "provecheck": __version__,
        "document": {
            "path": document.get("path"),
            "sha256": ours or theirs,
            "locale": locale,
            "pages": len(index.pages) if doc else None,
        },
        "summary": summarize(records, sources),
        "coverage": coverage(index, list(numbers.values()), claims.get("skipped") or [], locale)
        if doc
        else None,
        "claims": records,
        "unchecked_numbers": unchecked,
        "sources": sources,
        "skipped": [{"text": t, "reason": r, "count": n} for (t, r), n in skipped.items()],
        "warnings": warnings,
    }


def summarize(records: list[dict], sources: list[dict]) -> dict:
    """Counts by verdict, overall and per assurance tag. Chart verdicts stay separate."""
    out = {v: 0 for v in (CONTRADICTED, SUSPECT, UNVERIFIED, VERIFIED)}
    by: dict[str, dict[str, int]] = {}
    for rec in [*records, *sources]:
        out[rec["verdict"]] += 1
        tag = by.setdefault(rec["assurance"], {v: 0 for v in out})
        tag[rec["verdict"]] += 1
    return {**out, "by_assurance": by}
