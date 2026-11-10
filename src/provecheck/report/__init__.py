"""Reports: ``verdicts.json`` -> JSON, Markdown, HTML and an SVG card (SPEC §11).

``build_report`` makes the one canonical structure (schema ``prove.report.v1``).
The renderers only lay it out. Nothing here computes or changes a verdict.
"""

from __future__ import annotations

import json
from pathlib import Path

from provecheck import CONTRADICTED, SUSPECT, UNVERIFIED, VERIFIED, __version__
from provecheck.verdict import summarize

REPORT_SCHEMA = "prove.report.v1"
ORDER = (CONTRADICTED, SUSPECT, UNVERIFIED, VERIFIED)
FOOTER = (
    "A clean report means the checked claims passed. It does not mean the document is right: "
    "see the coverage line for how many numeric statements were checked. Prove does not judge "
    "opinions, forecasts or strategy, and it does not know whether a source is correct, only "
    "whether it exists and says what is quoted."
)

# What each verdict means, by how it was reached. Fixed wording: the model never writes these.
MEANING = {
    ("computed", CONTRADICTED): "No rounding of the printed numbers can produce this figure.",
    ("computed", SUSPECT): "Possible only if the inputs sit at the edge of their rounding.",
    ("computed", VERIFIED): "Recomputing from the printed numbers gives the printed figure.",
    ("read", CONTRADICTED): "The chart reading and the printed number cannot both be right.",
    ("read", SUSPECT): "Not ruled out, but the reading and the printed number barely meet.",
    ("read", VERIFIED): "The chart reading agrees with the printed number.",
    ("resolved", CONTRADICTED): "The source could not be matched to what the document cites.",
    ("resolved", VERIFIED): "The source exists and matches what the document cites.",
    ("proved", CONTRADICTED): "The rules allow a case where the conclusion is false.",
    ("proved", VERIFIED): "The conclusion follows from the stated rules.",
}
REASONS = {
    "not-grounded": "a number was not found in the document where the claims file says it is",
    "parse-mismatch": "the claims file gives a different value than the printed text",
    "parse-error": "a number could not be parsed as printed",
    "unit-mismatch": "a percentage was compared with a plain number",
    "scale-mismatch": "the two sides differ by a unit scale such as thousands vs millions",
    "division-by-zero": "the divisor could be zero within its rounding",
    "bad-args": "the derivation's arguments are not usable",
    "unstable-reading": "two readings of the chart mark disagree",
    "single-read": "the chart mark was read only once",
    "no-derivation": "no way to recompute this number was given",
    "not-run": "sources were not checked",
    "offline": "source checks were skipped (offline)",
}
ASSURANCE_LABEL = {
    "computed": "computed",
    "read": "read from a chart or image",
    "resolved": "source lookup",
    "proved": "proved",
}


def coverage_line(cov: dict | None) -> str:
    if not cov:
        return "Coverage: not available (no document text was given)."
    return (
        f"Numeric statements found: {cov['found']}   checked: {cov['checked']}   "
        f"skipped with reason: {cov['skipped']}   missed: {cov['missed']}"
    )


ORDER_MEANING = {
    CONTRADICTED: "The chart readings rule out the stated order.",
    VERIFIED: "The chart readings do not contradict the stated order.",
}
RANK_MEANING = {
    CONTRADICTED: "No rounding of the printed numbers can give this ranking.",
    SUSPECT: "The ranking holds only if the inputs sit at the edge of their rounding.",
    VERIFIED: "The printed numbers give this ranking.",
}


def meaning(rec: dict) -> str:
    verdict = rec["verdict"]
    if rec["assurance"] == "resolved" and rec.get("message"):
        return rec["message"]  # what the registry or the page answered, in plain words
    if verdict == UNVERIFIED:
        why = rec.get("message") or REASONS.get(
            rec.get("reason"), rec.get("reason") or "no reason given"
        )
        return f"Not checked: {why}"
    if rec.get("check") == "order" and verdict in ORDER_MEANING:
        return ORDER_MEANING[verdict]
    if rec.get("kind") == "derived" and (rec.get("computation") or "").startswith("place of "):
        return RANK_MEANING[verdict]
    return MEANING.get((rec["assurance"], verdict), "")


def build_report(verdicts: dict, sources: dict | None = None) -> dict:
    """The canonical report. ``sources`` is the output of ``provecheck sources``, if it ran."""
    resolved = {s["id"]: s for s in (sources or {}).get("sources", [])}
    source_recs = [resolved.get(s["id"], s) for s in verdicts.get("sources", [])]
    rank = {v: i for i, v in enumerate(ORDER)}
    claims = sorted(verdicts["claims"], key=lambda r: rank[r["verdict"]])
    source_recs = sorted(source_recs, key=lambda r: rank[r["verdict"]])
    for rec in [*claims, *source_recs]:
        rec["meaning"] = meaning(rec)
    return {
        "schema": REPORT_SCHEMA,
        "provecheck": verdicts.get("provecheck", __version__),
        "document": verdicts["document"],
        "summary": summarize(claims, source_recs),
        "coverage": verdicts.get("coverage"),
        "coverage_line": coverage_line(verdicts.get("coverage")),
        "claims": claims,
        "sources": source_recs,
        "unchecked_numbers": verdicts.get("unchecked_numbers", []),
        "skipped": verdicts.get("skipped", []),
        "warnings": verdicts.get("warnings", []),
        "footer": FOOTER,
    }


def exit_code(summary: dict, fail_on: str = CONTRADICTED) -> int:
    """0 nothing contradicted, 1 at least one contradicted. ``suspect`` tightens it for CI."""
    if fail_on == "never":
        return 0
    if summary[CONTRADICTED] or (fail_on == SUSPECT and summary[SUSPECT]):
        return 1
    return 0


def dumps(obj: dict) -> str:
    """Stable JSON: same input, same bytes."""
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def write_reports(
    report: dict, out_dir: Path, formats: list[str], base: Path | None = None
) -> list[Path]:
    from provecheck.report import card, html, md

    out_dir.mkdir(parents=True, exist_ok=True)
    renderers = {
        "json": ("prove-report.json", lambda: dumps(report)),
        "md": ("prove-report.md", lambda: md.render(report)),
        "html": ("prove-report.html", lambda: html.render(report, base or out_dir)),
        "card": ("prove-card.svg", lambda: card.render(report)),
    }
    written = []
    for fmt in formats:
        name, render = renderers[fmt]
        path = out_dir / name
        path.write_text(render(), encoding="utf-8", newline="\n")
        written.append(path)
    return written
