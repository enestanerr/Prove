"""HTML: visible text, tables as cells, images. One page."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from provecheck.ingest import make_page

_SKIP = {"script", "style", "head", "template", "noscript", "svg"}
_BLOCK = {
    "p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article",
    "header", "footer", "blockquote", "pre", "figure", "figcaption", "table", "hr", "dd", "dt",
}  # fmt: skip


class _Reader(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.tables: list[dict] = []
        self.images: list[dict] = []
        self._skip = 0
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP:
            self._skip += 1
        elif tag == "table":
            self.tables.append({"rows": []})
        elif tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._cell = []
        elif tag == "img":
            a = dict(attrs)
            self.images.append(
                {"path": a.get("src") or "", "alt": a.get("alt") or "", "kind": "figure"}
            )
            if a.get("alt"):
                self.handle_data(a["alt"])
        if tag in _BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in _SKIP:
            self._skip = max(0, self._skip - 1)
        elif tag in ("td", "th") and self._cell is not None:
            if self._row is not None:
                self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self.tables:
                self.tables[-1]["rows"].append(self._row)
            self.parts.append(" | ".join(self._row) + "\n")
            self._row = None
        if tag in _BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._skip:
            return
        if self._cell is not None:
            self._cell.append(data)
        else:
            self.parts.append(data)


def pages_of_html(text: str, path: Path | None = None) -> list[dict]:
    reader = _Reader()
    reader.feed(text)
    reader.close()
    lines = [" ".join(line.split()) for line in "".join(reader.parts).split("\n")]
    body = "\n".join(line for line in lines if line)
    return [make_page(1, body, tables=reader.tables, images=reader.images)]
