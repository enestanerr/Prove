"""Compact Markdown report, for pasting into chat or a pull request."""

from __future__ import annotations

from provecheck.report import ASSURANCE_LABEL, ORDER


def headline(summary: dict) -> str:
    return " · ".join(f"{summary[v]} {v}" for v in ORDER)


def by_assurance(summary: dict) -> list[str]:
    lines = []
    for tag, counts in summary["by_assurance"].items():
        parts = ", ".join(f"{counts[v]} {v}" for v in ORDER if counts[v])
        lines.append(f"{ASSURANCE_LABEL.get(tag, tag)}: {parts}")
    return lines


def where(rec: dict) -> str:
    target, chart = rec.get("target") or {}, rec.get("chart") or {}
    page = target.get("page") or chart.get("page") or rec.get("page")
    bits = [rec["id"], ASSURANCE_LABEL.get(rec["assurance"], rec["assurance"])]
    if chart.get("figure"):
        bits.append(chart["figure"])
    if page:
        bits.append(f"page {page}")
    return " · ".join(bits)


def _claim(rec: dict) -> list[str]:
    out = [f"**{where(rec)}**"]
    quote = (rec.get("target") or {}).get("quote")
    if quote:
        out.append(f"> {quote}")
    if rec.get("say"):
        out.append(rec["say"])
    if rec.get("sentence"):
        out.append(f"`{rec['sentence']}`")
    if rec.get("meaning"):
        out.append(rec["meaning"])
    out.extend(f"Note: {note}" for note in rec.get("notes") or [])
    out.extend(f"Chart note: {note}" for note in (rec.get("chart") or {}).get("notes") or [])
    return out + [""]


def _source(rec: dict) -> list[str]:
    title = f" — {rec['cited_title']}" if rec.get("cited_title") else ""
    out = [f"**{where(rec)}** `{rec['kind']}: {rec['value']}`{title}"]
    if rec.get("meaning"):
        out.append(rec["meaning"])
    return out + [""]


def render(report: dict) -> str:
    doc, summary = report["document"], report["summary"]
    lines = [
        f"# Prove report — {doc.get('path') or 'document'}",
        "",
        f"**{headline(summary)}**",
        "",
    ]
    lines += [f"- {line}" for line in by_assurance(summary)]
    lines += ["", report["coverage_line"], ""]
    lines += [f"> Warning: {w}" for w in report["warnings"]]
    for verdict in ORDER:
        claims = [r for r in report["claims"] if r["verdict"] == verdict]
        sources = [r for r in report["sources"] if r["verdict"] == verdict]
        if not claims and not sources:
            continue
        lines += [f"## {verdict.capitalize()} ({len(claims) + len(sources)})", ""]
        for rec in claims:
            lines += _claim(rec)
        for rec in sources:
            lines += _source(rec)
    missed = (report.get("coverage") or {}).get("missed_tokens") or []
    if missed:
        lines += [
            f"## Missed ({len(missed)})",
            "",
            "Numbers in the document that were neither checked nor skipped:",
            "",
        ]
        lines += [f"- page {t['page']}: `{t['text']}` in “{t['context']}”" for t in missed[:50]]
        if len(missed) > 50:
            lines.append(f"- … and {len(missed) - 50} more")
        lines.append("")
    unchecked = report.get("unchecked_numbers") or []
    if unchecked:
        shown = ", ".join(f"`{n['text']}` (p. {n['page']})" for n in unchecked[:40])
        more = f" and {len(unchecked) - 40} more" if len(unchecked) > 40 else ""
        lines += [f"Recorded without a check ({len(unchecked)}): {shown}{more}", ""]
    lines += [
        "---",
        report["footer"],
        "",
        f"Verdicts computed by provecheck {report['provecheck']}.",
    ]
    return "\n".join(lines) + "\n"
