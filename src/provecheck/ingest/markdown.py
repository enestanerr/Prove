"""Markdown: pages, tables as cells, images.

Markdown has no pages, so a thematic break (``---``), a form feed or an
``<!-- pagebreak -->`` comment starts a new one. A document with none of them
is one page.
"""

from __future__ import annotations

import re
from pathlib import Path

from provecheck.ingest import make_page

_BREAK = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,}|<!--\s*page-?break\s*-->|\f)\s*$", re.I)
_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)[^)]*\)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)[^)]*\)")
_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _page(lines: list[str], n: int, base: Path | None) -> dict:
    out, tables, images, i = [], [], [], 0
    while i < len(lines):
        line = lines[i]
        if "|" in line and i + 1 < len(lines) and _SEPARATOR.match(lines[i + 1]):
            rows = [_cells(line)]
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(_cells(lines[i]))
                i += 1
            tables.append({"rows": rows})
            out.extend(" | ".join(row) for row in rows)
            continue
        for alt, src in _IMAGE.findall(line):
            target = (
                (base.parent / src).as_posix() if base is not None and "://" not in src else src
            )
            images.append({"path": target, "alt": alt, "kind": "figure"})
        line = _IMAGE.sub(r"\1", line)
        line = _LINK.sub(r"\1", line)
        out.append(_HEADING.sub("", line))
        i += 1
    return make_page(n, "\n".join(out).strip(), tables=tables, images=images)


def pages_of_markdown(text: str, path: Path | None = None) -> list[dict]:
    lines = text.replace("\r\n", "\n").split("\n")
    if lines and lines[0].strip() == "---":  # YAML front matter
        for j in range(1, len(lines)):
            if lines[j].strip() in ("---", "..."):
                lines = lines[j + 1 :]
                break
    chunks: list[list[str]] = [[]]
    for line in lines:
        if _BREAK.match(line):
            chunks.append([])
        else:
            chunks[-1].append(line)
    chunks = [c for c in chunks if any(s.strip() for s in c)] or [[]]
    return [_page(chunk, n, path) for n, chunk in enumerate(chunks, start=1)]
