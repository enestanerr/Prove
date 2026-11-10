"""Ingest: turn a document into ``doc.json`` (pages -> text, tables, images).

Text, Markdown, HTML and CSV need only the standard library. PDF needs the
``pdf`` extra and says so when it is missing.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

DOC_SCHEMA = "prove.doc.v1"

_FORMATS = {
    ".txt": "text", ".text": "text",
    ".md": "markdown", ".markdown": "markdown",
    ".html": "html", ".htm": "html",
    ".csv": "csv", ".tsv": "csv",
    ".pdf": "pdf",
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".gif": "image", ".webp": "image",
}  # fmt: skip


class IngestError(Exception):
    """The document could not be read. The message says what to do."""


class MissingExtra(IngestError):
    def __init__(self, feature: str, extra: str, package: str) -> None:
        super().__init__(
            f"{feature} needs the optional package {package}. Install it with: "
            f'pip install "provecheck[{extra}]"   (or: pip install {package})'
        )


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def make_page(n: int, text: str, tables=None, images=None, has_text: bool | None = None) -> dict:
    return {
        "page": n,
        "text": text,
        "tables": tables or [],
        "images": images or [],
        "has_text": bool(text.strip()) if has_text is None else has_text,
    }


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def ingest(
    path: str | Path, render_pages: str | Path | None = None, locale: str | None = None
) -> dict:
    path = Path(path)
    if not path.is_file():
        raise IngestError(f"no such file: {path}")
    fmt = _FORMATS.get(path.suffix.lower())
    if fmt is None:
        known = ", ".join(sorted(_FORMATS))
        raise IngestError(f"unsupported file type {path.suffix!r}; supported: {known}")
    if fmt == "text":
        from provecheck.ingest.text import pages_of_text as reader
    elif fmt == "markdown":
        from provecheck.ingest.markdown import pages_of_markdown as reader
    elif fmt == "html":
        from provecheck.ingest.html import pages_of_html as reader
    elif fmt == "csv":
        from provecheck.ingest.text import pages_of_csv as reader
    if fmt == "pdf":
        from provecheck.ingest.pdf import pages_of_pdf

        pages = pages_of_pdf(path, render_pages)
    elif fmt == "image":
        pages = [
            make_page(1, "", images=[{"path": path.as_posix(), "kind": "page"}], has_text=False)
        ]
    else:
        pages = reader(read_text(path), path)
    return {
        "schema": DOC_SCHEMA,
        "path": path.as_posix(),
        "sha256": sha256_file(path),
        "format": fmt,
        "locale": locale,
        "pages": pages,
    }


def load_doc(path: str | Path) -> dict:
    """Load a ``doc.json``, or ingest the document itself when given one."""
    path = Path(path)
    if path.suffix.lower() == ".json":
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise IngestError(f"cannot read {path}: {exc}") from None
        if not isinstance(doc, dict) or doc.get("schema") != DOC_SCHEMA:
            raise IngestError(f"{path} is not a {DOC_SCHEMA} file (run `provecheck ingest` first)")
        return doc
    return ingest(path)
