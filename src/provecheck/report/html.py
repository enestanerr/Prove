"""One self-contained HTML report. No scripts, no external requests."""

from __future__ import annotations

import base64
from html import escape
from pathlib import Path

from provecheck.report import ASSURANCE_LABEL, ORDER
from provecheck.report.md import by_assurance, where

_CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#16202c;--mute:#5a6573;--line:#dfe3e9;
--contradicted:#c62828;--suspect:#b26a00;--unverified:#5f6b7a;--verified:#2e7d32;--code:#f0f2f5}
@media(prefers-color-scheme:dark){:root{--bg:#12161c;--card:#1b212a;--ink:#e8ecf1;--mute:#9aa5b3;
--line:#2c3540;--contradicted:#ef7070;--suspect:#e0a030;--unverified:#9aa5b3;--verified:#6cc070;--code:#232b36}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
main{max-width:860px;margin:0 auto;padding:32px 16px 56px}
h1{font-size:24px;margin:0 0 4px}h2{font-size:17px;margin:34px 0 12px;display:flex;align-items:center;gap:8px}
.sub{color:var(--mute);margin:0 0 22px;word-break:break-all}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.tile{background:var(--card);border:1px solid var(--line);border-top:4px solid var(--c);border-radius:10px;padding:12px 14px}
.tile b{display:block;font-size:30px;line-height:1.1;color:var(--c)}.tile span{color:var(--mute);font-size:13px}
.split{color:var(--mute);font-size:13px;margin:12px 0 0;padding:0;list-style:none}
.cov{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:11px 14px;margin:16px 0 0;
font-variant-numeric:tabular-nums}
.cov.miss{border-color:var(--suspect)}.warn{border-left:4px solid var(--suspect);padding:8px 12px;margin:12px 0 0;
background:var(--card);border-radius:6px}
.dot{width:10px;height:10px;border-radius:50%;background:var(--c);display:inline-block}
.card{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--c);border-radius:10px;
padding:14px 16px;margin:0 0 12px}
.meta{font-size:12.5px;color:var(--mute);display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px}
.tag{border:1px solid var(--line);border-radius:999px;padding:1px 9px}.verdict{color:var(--c);font-weight:700;
text-transform:uppercase;letter-spacing:.04em;font-size:12px}
blockquote{margin:0 0 8px;padding:2px 0 2px 12px;border-left:3px solid var(--line);color:var(--mute)}
.say{margin:0 0 8px}.calc{background:var(--code);border-radius:6px;padding:8px 10px;margin:0 0 8px;
font:13.5px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace;overflow-wrap:anywhere}
.mean{margin:0;font-weight:600}.note{margin:6px 0 0;color:var(--mute);font-size:13.5px}
.fig{display:block;max-width:100%;max-height:340px;border:1px solid var(--line);border-radius:6px;
margin:0 0 8px;background:#fff}
table{border-collapse:collapse;font-size:13px;margin:0 0 8px}td,th{border:1px solid var(--line);padding:3px 9px;text-align:left}
ul.plain{margin:0;padding-left:20px}details{margin:0 0 12px}summary{cursor:pointer;color:var(--mute)}
footer{margin-top:36px;padding-top:14px;border-top:1px solid var(--line);color:var(--mute);font-size:13px}
@media(max-width:560px){.tiles{grid-template-columns:repeat(2,1fr)}}
"""


def _image(path: str | None, base: Path) -> str:
    if not path:
        return ""
    for candidate in (Path(path), base / path):
        if candidate.is_file() and candidate.suffix.lower() in (".png", ".jpg", ".jpeg"):
            mime = "image/png" if candidate.suffix.lower() == ".png" else "image/jpeg"
            data = base64.b64encode(candidate.read_bytes()).decode("ascii")
            return f'<img class="fig" alt="chart crop" src="data:{mime};base64,{data}">'
    return ""


def _marks(rec: dict) -> str:
    marks = rec.get("marks") or []
    if not marks:
        return ""
    unit = (rec.get("chart") or {}).get("unit")
    head = (
        "<tr><th>Mark</th><th>First reading</th><th>Second reading (2× crop)</th><th>Used</th></tr>"
    )
    rows = []
    for m in marks:
        name = escape(m["label"]) + (f" / {escape(m['series'])}" if m.get("series") else "")
        used = escape(m["final"]) if m.get("final") else escape(m["status"])
        rows.append(
            f"<tr><td>{name}</td><td>{escape(m['read_a'])}</td>"
            f"<td>{escape(m['read_b'] or '—')}</td><td>{used}</td></tr>"
        )
    caption = f'<p class="note">Readings are in axis units ({escape(unit)}).</p>' if unit else ""
    return f"<table>{head}{''.join(rows)}</table>{caption}"


def _card(rec: dict, base: Path) -> str:
    parts = [
        f'<div class="card" style="--c:var(--{rec["verdict"]})" id="{escape(rec["id"])}">',
        f'<div class="meta"><span class="verdict">{rec["verdict"]}</span>'
        f'<span class="tag">{escape(ASSURANCE_LABEL.get(rec["assurance"], rec["assurance"]))}</span>'
        f"<span>{escape(where(rec, assurance=False))}</span></div>",
    ]
    quote = (rec.get("target") or {}).get("quote")
    if quote:
        parts.append(f"<blockquote>{escape(quote)}</blockquote>")
    if rec.get("kind") in ("doi", "arxiv", "url", "quote"):
        title = f" — {escape(rec['cited_title'])}" if rec.get("cited_title") else ""
        parts.append(f'<p class="calc">{escape(rec["kind"])}: {escape(rec["value"])}{title}</p>')
    if rec.get("say"):
        parts.append(f'<p class="say">{escape(rec["say"])}</p>')
    if rec.get("kind") == "chart":
        parts.append(_image(rec["chart"].get("image"), base))
        parts.append(_marks(rec))
    if rec.get("sentence"):
        parts.append(f'<p class="calc">{escape(rec["sentence"])}</p>')
    if rec.get("meaning"):
        parts.append(f'<p class="mean">{escape(rec["meaning"])}</p>')
    for note in rec.get("notes") or []:
        parts.append(f'<p class="note">{escape(note)}</p>')
    for note in (rec.get("chart") or {}).get("notes") or []:
        parts.append(f'<p class="note">Chart note: {escape(note)}</p>')
    parts.append("</div>")
    return "\n".join(p for p in parts if p)


def render(report: dict, base: Path | None = None) -> str:
    base = base or Path(".")
    doc, summary, cov = report["document"], report["summary"], report.get("coverage")
    out = [
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f"<title>Prove report — {escape(str(doc.get('path') or 'document'))}</title>",
        f"<style>{_CSS}</style></head><body><main>",
        "<h1>Prove report</h1>",
        f'<p class="sub">{escape(str(doc.get("path") or "document"))}</p>',
        '<div class="tiles">',
    ]
    for verdict in ORDER:
        out.append(
            f'<div class="tile" style="--c:var(--{verdict})"><b>{summary[verdict]}</b>'
            f"<span>{verdict}</span></div>"
        )
    out.append("</div>")
    out.append(
        '<ul class="split">'
        + "".join(f"<li>{escape(s)}</li>" for s in by_assurance(summary))
        + "</ul>"
    )
    missed = (cov or {}).get("missed_tokens") or []
    line = escape(report["coverage_line"]).replace("   ", " &nbsp;·&nbsp; ")
    out.append(f'<p class="cov{" miss" if missed else ""}">{line}</p>')
    out.extend(f'<p class="warn">{escape(w)}</p>' for w in report["warnings"])

    for verdict in ORDER:
        recs = [r for r in [*report["claims"], *report["sources"]] if r["verdict"] == verdict]
        if not recs:
            continue
        out.append(
            f'<h2 style="--c:var(--{verdict})"><span class="dot"></span>'
            f"{verdict.capitalize()} ({len(recs)})</h2>"
        )
        out.extend(_card(rec, base) for rec in recs)

    if missed:
        out.append(
            f'<h2 style="--c:var(--suspect)"><span class="dot"></span>Missed ({len(missed)})</h2>'
        )
        out.append(
            "<p>Numbers in the document that were neither checked nor skipped with a reason:</p>"
        )
        items = "".join(
            f"<li>page {t['page']}: <b>{escape(t['text'])}</b> in “{escape(t['context'])}”</li>"
            for t in missed[:200]
        )
        out.append(f'<ul class="plain">{items}</ul>')
    unchecked = report.get("unchecked_numbers") or []
    if unchecked:
        items = "".join(
            f"<li><b>{escape(n['text'])}</b> (page {n['page']}): {escape(n['reason'])}</li>"
            for n in unchecked
        )
        out.append(
            f"<details><summary>Numbers recorded without a check ({len(unchecked)})</summary>"
            f'<ul class="plain">{items}</ul></details>'
        )
    skipped = report.get("skipped") or []
    if skipped:
        items = "".join(
            f"<li><b>{escape(s['text'])}</b>: {escape(s['reason'])}</li>" for s in skipped
        )
        out.append(
            f"<details><summary>Skipped with a reason ({len(skipped)} entries)</summary>"
            f'<ul class="plain">{items}</ul></details>'
        )
    out.append(
        f"<footer><p>{escape(report['footer'])}</p>"
        f"<p>Verdicts computed by provecheck {escape(str(report['provecheck']))}. "
        "The model proposed the checks; code decided every verdict.</p></footer>"
    )
    out.append("</main></body></html>")
    return "\n".join(out) + "\n"
