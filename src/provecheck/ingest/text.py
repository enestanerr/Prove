"""Plain text and CSV. A form feed starts a new page."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from provecheck.ingest import make_page


def pages_of_text(text: str, path: Path | None = None) -> list[dict]:
    return [make_page(i, chunk) for i, chunk in enumerate(text.split("\f"), start=1)]


def pages_of_csv(text: str, path: Path | None = None) -> list[dict]:
    delimiter = "\t" if path is not None and path.suffix.lower() == ".tsv" else ","
    rows = [
        [cell.strip() for cell in row] for row in csv.reader(io.StringIO(text), delimiter=delimiter)
    ]
    rows = [row for row in rows if any(row)]
    body = "\n".join(" | ".join(row) for row in rows)
    return [make_page(1, body, tables=[{"rows": rows}])]
