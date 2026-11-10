"""Render the small Markdown subset used by the examples and the eval corpus to PDF.

Development tool (needs PyMuPDF). Supported: headings, paragraphs, pipe tables,
images, bullet lists, bold/italic, and ``---`` as a page break.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

CSS = """
body { font-family: sans-serif; font-size: 11pt; line-height: 1.45; color: #111; }
h1 { font-size: 20pt; margin: 0 0 10pt 0; }
h2 { font-size: 14pt; margin: 14pt 0 6pt 0; }
p { margin: 0 0 8pt 0; }
table { border-collapse: collapse; margin: 4pt 0 10pt 0; }
td, th { border: 1px solid #999; padding: 3pt 8pt; font-size: 10.5pt; }
th { background-color: #eee; }
img { width: 420px; }
"""
_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_BREAK = re.compile(r"^\s*-{3,}\s*$")


def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)


def to_html(md: str) -> str:
    out, lines, i, para = [], md.replace("\r\n", "\n").split("\n"), 0, []

    def flush() -> None:
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            flush()
        elif _BREAK.match(line):
            flush()
            out.append('<div style="page-break-before: always"></div>')
        elif line.startswith("#"):
            flush()
            level = len(line) - len(line.lstrip("#"))
            out.append(f"<h{level}>{_inline(line[level:].strip())}</h{level}>")
        elif m := re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line.strip()):
            flush()
            out.append(f'<p><img src="{m.group(2)}"><br><i>{_inline(m.group(1))}</i></p>')
        elif "|" in line and i + 1 < len(lines) and _SEP.match(lines[i + 1]):
            flush()
            rows = [line]
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(lines[i])
                i += 1
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            body = "".join(
                "<tr>"
                + "".join(
                    f"<{'th' if n == 0 else 'td'}>{_inline(c)}</{'th' if n == 0 else 'td'}>"
                    for c in row
                )
                + "</tr>"
                for n, row in enumerate(cells)
            )
            out.append(f"<table>{body}</table>")
            continue
        elif line.lstrip().startswith(("- ", "* ")):
            flush()
            out.append("<p>• " + _inline(line.lstrip()[2:]) + "</p>")
        else:
            para.append(line.strip())
        i += 1
    flush()
    return "\n".join(out)


def render(md_path: Path, pdf_path: Path) -> None:
    import pymupdf as fitz

    story = fitz.Story(
        html=to_html(md_path.read_text(encoding="utf-8")),
        user_css=CSS,
        archive=fitz.Archive(str(md_path.parent)),
    )
    page_rect = fitz.paper_rect("a4")
    content = page_rect + (56, 56, -56, -56)
    writer = fitz.DocumentWriter(str(pdf_path))
    more = True
    while more:
        device = writer.begin_page(page_rect)
        more, _ = story.place(content)
        story.draw(device)
        writer.end_page()
    writer.close()
    # Story embeds whole fonts; subset them so example PDFs stay small.
    doc = fitz.open(str(pdf_path))
    doc.subset_fonts()
    data = doc.tobytes(garbage=4, deflate=True, no_new_id=True)
    doc.close()
    pdf_path.write_bytes(data)
