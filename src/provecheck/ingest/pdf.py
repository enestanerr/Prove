"""PDF: text per page, tables, page images. Needs the ``pdf`` extra (PyMuPDF)."""

from __future__ import annotations

from pathlib import Path

from provecheck.ingest import IngestError, MissingExtra, make_page

RENDER_DPI = 150


def fitz_module():
    try:
        import pymupdf as fitz  # PyMuPDF >= 1.24
    except ImportError:
        try:
            import fitz
        except ImportError:
            raise MissingExtra("PDF support", "pdf", "pymupdf") from None
    return fitz


def pages_of_pdf(path: Path, render_pages: str | Path | None = None) -> list[dict]:
    fitz = fitz_module()
    try:
        doc = fitz.open(path)
    except Exception as exc:  # PyMuPDF raises its own error types
        raise IngestError(f"cannot open {path}: {exc}") from None
    out_dir = Path(render_pages) if render_pages else None
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    with doc:
        for n, page in enumerate(doc, start=1):
            text = page.get_text("text")
            tables = []
            try:
                for table in page.find_tables().tables:
                    # Read each cell from its own box: table.extract() can reorder glyphs.
                    rows = [
                        [
                            " ".join(page.get_text("text", clip=cell).split()) if cell else ""
                            for cell in row.cells
                        ]
                        for row in table.rows
                    ]
                    tables.append({"rows": rows})
            except Exception:  # table detection is best effort
                tables = []
            images = []
            if out_dir is not None:
                target = out_dir / f"page-{n:03d}.png"
                page.get_pixmap(dpi=RENDER_DPI).save(target)
                images.append({"path": target.as_posix(), "kind": "page"})
            pages.append(make_page(n, text, tables=tables, images=images))
    return pages


def _box(spec: tuple[float, float, float, float], width: float, height: float):
    """Fractions of the page (0..1) or absolute units -> absolute (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = spec
    if max(spec) <= 1:
        x0, x1, y0, y1 = x0 * width, x1 * width, y0 * height, y1 * height
    x0, x1 = sorted((max(0.0, x0), min(width, x1)))
    y0, y1 = sorted((max(0.0, y0), min(height, y1)))
    if x1 - x0 < 1 or y1 - y0 < 1:
        raise IngestError("the crop box is empty; give x0,y0,x1,y1 with x0 < x1 and y0 < y1")
    return x0, y0, x1, y1


def crop(
    source: Path, page: int, box: tuple[float, float, float, float], upscale: int, out: Path
) -> dict:
    """Cut a region out of a PDF page or an image and enlarge it."""
    is_pdf = source.suffix.lower() == ".pdf"
    try:
        fitz = fitz_module()
    except MissingExtra:
        if is_pdf or source.suffix.lower() != ".png":
            raise
        from provecheck.ingest import png

        width, height = png.size(source)
        x0, y0, x1, y1 = (round(v) for v in _box(box, width, height))
        png.crop(source, (x0, y0, x1, y1), upscale, out)
        return {"out": out.as_posix(), "width": (x1 - x0) * upscale, "height": (y1 - y0) * upscale}
    with fitz.open(source) as doc:
        if not 1 <= page <= len(doc):
            raise IngestError(f"page {page} does not exist (the document has {len(doc)} pages)")
        pg = doc[page - 1]
        x0, y0, x1, y1 = _box(box, pg.rect.width, pg.rect.height)
        zoom = upscale * (RENDER_DPI / 72 if is_pdf else 1)
        pix = pg.get_pixmap(clip=fitz.Rect(x0, y0, x1, y1), matrix=fitz.Matrix(zoom, zoom))
        out.parent.mkdir(parents=True, exist_ok=True)
        pix.save(out)
        return {"out": out.as_posix(), "width": pix.width, "height": pix.height}
