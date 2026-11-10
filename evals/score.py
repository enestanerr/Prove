"""Score one audit against the truth of its document (docs/EVALS.md).

``truth.json`` records what was planted in a document and what was laid as a
trap. A claim is matched to a truth item by *where its target number sits* in
the document text, not by ids, so a model-written claims file and a gold one
are scored the same way.
"""

from __future__ import annotations

from fractions import Fraction

from provecheck import charts as chartlib
from provecheck.grounding import DocIndex, find_all, ground_number, normalize
from provecheck.numbers import normalize_locale

CONTRADICTED, SUSPECT = "contradicted", "suspect"


def _spans(index: DocIndex, item: dict) -> set[tuple[int, int, int]]:
    """Where a truth item sits: every occurrence of its text inside its quote on its page."""
    quote, text = normalize(item.get("quote") or item["text"]), normalize(item["text"])
    out = set()
    for start in index.occurrences(item["page"], quote):
        for offset in find_all(quote, text):
            out.add((item["page"], start + offset, start + offset + len(text)))
    return out


def _overlap(a: set, b: set) -> bool:
    return any(pa == pb and sa < eb and sb < ea for pa, sa, ea in a for pb, sb, eb in b)


class Matcher:
    """Which truth item, if any, a claim's target number is."""

    def __init__(self, truth: dict, claims: dict, doc: dict) -> None:
        self.index = DocIndex(doc)
        locale = normalize_locale((claims.get("document") or {}).get("locale"))
        self.numbers = {n["id"]: n for n in claims.get("numbers") or []}
        self.spans = {
            n["id"]: set(ground_number(n, self.index, locale).spans) for n in self.numbers.values()
        }
        self.items = [
            {**item, "kind": kind, "spans": _spans(self.index, item)}
            for kind in ("planted", "traps")
            for item in truth.get(kind) or []
        ]

    def hits(self, number_id: str | None, kind: str) -> list[dict]:
        entry = self.numbers.get(number_id)
        if entry is None:
            return []
        out = []
        for item in self.items:
            if item["kind"] != kind:
                continue
            if item.get("image"):  # a label inside a figure: no text position to compare
                loc = entry.get("loc") or {}
                same = normalize(entry["text"]) == normalize(item["text"])
                if same and loc.get("page") == item["page"] and loc.get("image"):
                    out.append(item)
            elif _overlap(self.spans[number_id], item["spans"]):
                out.append(item)
        return out


def score_claims(truth: dict, claims: dict, verdicts: dict, doc: dict) -> dict:
    """Recall on planted errors, false alarms, and what happened at each trap."""
    m = Matcher(truth, claims, doc)
    found: dict[str, list[str]] = {item["id"]: [] for item in m.items}
    alarms = []
    for rec in verdicts["claims"]:
        target = (rec.get("target") or {}).get("id")
        planted, traps = m.hits(target, "planted"), m.hits(target, "traps")
        for item in planted + traps:
            found[item["id"]].append(rec["verdict"])
        if rec["verdict"] == CONTRADICTED and not planted:
            # A contradiction that leans on a planted number is a knock-on effect, not a
            # false alarm about a clean number. It is still reported, separately.
            inputs = [n for n in rec.get("numbers") or [] if n != target]
            cascade = any(m.hits(n, "planted") for n in inputs)
            kind = "trap" if traps else "cascade" if cascade else "clean"
            alarms.append({"claim": rec["id"], "kind": kind, "sentence": rec.get("sentence")})

    def outcome(verdicts_at: list[str]) -> str:
        if CONTRADICTED in verdicts_at:
            return CONTRADICTED
        if SUSPECT in verdicts_at:
            return SUSPECT
        return "not-flagged" if verdicts_at else "no-claim"

    planted = [
        {"id": i["id"], "type": i["type"], "outcome": outcome(found[i["id"]])}
        for i in m.items
        if i["kind"] == "planted"
    ]
    traps = [
        {"id": i["id"], "type": i["type"], "outcome": outcome(found[i["id"]])}
        for i in m.items
        if i["kind"] == "traps"
    ]
    summary = verdicts["summary"]
    return {
        "planted": planted,
        "traps": traps,
        "planted_total": len(planted),
        "caught": sum(p["outcome"] == CONTRADICTED for p in planted),
        "caught_as_suspect": sum(p["outcome"] == SUSPECT for p in planted),
        "false_alarms": [a for a in alarms if a["kind"] != "cascade"],
        "cascades": [a for a in alarms if a["kind"] == "cascade"],
        "trap_total": len(traps),
        "traps_flagged": sum(t["outcome"] == CONTRADICTED for t in traps),
        "claims": len(verdicts["claims"]),
        "verdicts": {k: summary[k] for k in ("contradicted", "suspect", "unverified", "verified")},
        "coverage": {
            k: (verdicts.get("coverage") or {}).get(k)
            for k in ("found", "checked", "skipped", "missed")
        },
    }


def _same(a: str | None, b: str | None) -> bool:
    return normalize(a or "").casefold() == normalize(b or "").casefold()


def score_charts(truth: dict, claims: dict) -> list[dict]:
    """Reading error per mark: |midpoint − true| as a share of the axis span."""
    out = []
    for true_chart in truth.get("charts") or []:
        lo, hi = (Fraction(str(v)) for v in true_chart["axis"])
        read = next(
            (
                g
                for g in claims.get("charts") or []
                if _same((g.get("loc") or {}).get("figure"), true_chart["figure"])
                or (g.get("loc") or {}).get("page") == true_chart["page"]
            ),
            None,
        )
        for label, value in true_chart["marks"].items():
            row = {
                "figure": true_chart["figure"],
                "label": label,
                "true": value,
                "status": "not-read",
            }
            mark = next(
                (k for k in (read or {}).get("marks") or [] if _same(k.get("label"), label)), None
            )
            if mark is not None:
                try:
                    reading = chartlib.read_mark(mark, chartlib.Axis.of(read))
                except (KeyError, ValueError):
                    reading = None
                if reading is not None:
                    row["status"] = reading.status
                    final = reading.final or reading.a
                    true = Fraction(str(value)) * chartlib.Axis.of(read).multiplier
                    if reading.final is None:
                        final = final.scale(chartlib.Axis.of(read).multiplier)
                    row["error_share_of_span"] = round(float(abs(final.mid - true) / (hi - lo)), 4)
                    row["contains_true_value"] = final.contains(true)
            out.append(row)
    return out
