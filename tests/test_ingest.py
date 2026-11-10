import json

import pytest

from provecheck.ingest import IngestError, ingest, load_doc
from provecheck.ingest.html import pages_of_html
from provecheck.ingest.markdown import pages_of_markdown
from provecheck.ingest.text import pages_of_csv, pages_of_text

MD = """---
title: front matter is dropped
---
# Report **2026**

Revenue rose to [$2.30M](https://example.org/x), up 14%.

| Region | Orders |
| :----- | -----: |
| North  | 1,204  |
| Total  | 4,812  |

---

## Charts

![Figure 2: Spend](figure2.png)
"""


def test_markdown_pages_tables_images():
    pages = pages_of_markdown(MD)
    assert [p["page"] for p in pages] == [1, 2]
    first, second = pages
    assert "front matter" not in first["text"] and first["text"].startswith("Report **2026**")
    assert "Revenue rose to $2.30M, up 14%." in first["text"]  # the link target is dropped
    assert "North | 1,204" in first["text"]
    assert first["tables"] == [
        {"rows": [["Region", "Orders"], ["North", "1,204"], ["Total", "4,812"]]}
    ]
    assert second["images"] == [{"path": "figure2.png", "alt": "Figure 2: Spend", "kind": "figure"}]
    assert "Figure 2: Spend" in second["text"]


def test_markdown_without_breaks_is_one_page():
    assert len(pages_of_markdown("# Title\n\nJust 1 page.")) == 1


@pytest.mark.parametrize("marker", ["---", "***", "<!-- pagebreak -->", "<!-- page-break -->"])
def test_markdown_page_break_markers(marker):
    assert len(pages_of_markdown(f"one\n\n{marker}\n\ntwo")) == 2


def test_text_pages_split_on_form_feed():
    pages = pages_of_text("page one 1\fpage two 2")
    assert [p["text"] for p in pages] == ["page one 1", "page two 2"]


def test_csv_becomes_one_table():
    (page,) = pages_of_csv('Region,Orders\nNorth,"1,204"\n')
    assert page["tables"] == [{"rows": [["Region", "Orders"], ["North", "1,204"]]}]
    assert "North | 1,204" in page["text"]


def test_html_text_tables_and_hidden_parts():
    html = """<html><head><title>T</title><style>p{color:red}</style></head><body>
    <h1>Report</h1><p>Revenue rose <b>14%</b>.</p><script>var x = 99;</script>
    <table><tr><th>Region</th><th>Orders</th></tr><tr><td>North</td><td>1,204</td></tr></table>
    <img src="fig.png" alt="Figure 1"></body></html>"""
    (page,) = pages_of_html(html)
    assert (
        "Revenue rose 14%." in page["text"]
        and "99" not in page["text"]
        and "color" not in page["text"]
    )
    assert page["tables"] == [{"rows": [["Region", "Orders"], ["North", "1,204"]]}]
    assert "North | 1,204" in page["text"]
    assert page["images"][0]["alt"] == "Figure 1"


def test_ingest_writes_the_doc_structure(root):
    doc = ingest(root / "examples" / "kestrel-q3" / "report.md")
    assert (
        doc["schema"] == "prove.doc.v1" and doc["format"] == "markdown" and len(doc["sha256"]) == 64
    )
    assert [p["page"] for p in doc["pages"]] == [1, 2, 3, 4]
    assert all(p["has_text"] for p in doc["pages"])


def test_ingest_pdf_matches_markdown_page_for_page(root):
    pytest.importorskip("pymupdf")
    doc = ingest(root / "examples" / "kestrel-q3" / "report.pdf")
    assert doc["format"] == "pdf" and len(doc["pages"]) == 4
    assert "Revenue rose from $2.10M in Q2 to $2.30M in Q3, up 14%." in doc["pages"][0]["text"]
    assert ["Total", "4,812"] in doc["pages"][1]["tables"][0]["rows"]


def test_ingest_pdf_can_render_pages(root, tmp_path):
    pytest.importorskip("pymupdf")
    doc = ingest(root / "examples" / "kestrel-q3" / "report.pdf", render_pages=tmp_path)
    assert (tmp_path / "page-003.png").is_file()
    assert doc["pages"][2]["images"][0]["kind"] == "page"


def test_image_is_a_page_without_text(root):
    doc = ingest(root / "examples" / "kestrel-q3" / "figure2.png")
    assert doc["pages"][0]["has_text"] is False


def test_unknown_type_and_missing_file(tmp_path):
    odd = tmp_path / "report.xyz"
    odd.write_text("x")
    with pytest.raises(IngestError, match="unsupported file type"):
        ingest(odd)
    with pytest.raises(IngestError, match="no such file"):
        ingest(tmp_path / "nope.md")


def test_load_doc_accepts_doc_json_or_the_document(root, tmp_path):
    source = root / "examples" / "kestrel-q3" / "report.md"
    saved = tmp_path / "doc.json"
    saved.write_text(json.dumps(ingest(source)), encoding="utf-8")
    assert load_doc(saved)["sha256"] == load_doc(source)["sha256"]
    other = tmp_path / "other.json"
    other.write_text("{}", encoding="utf-8")
    with pytest.raises(IngestError, match="not a prove.doc.v1 file"):
        load_doc(other)


def test_png_crop_without_pymupdf(root, tmp_path):
    from provecheck.ingest import png

    source = root / "examples" / "kestrel-q3" / "figure2.png"
    width, height = png.size(source)
    out = tmp_path / "crop.png"
    png.crop(source, (0, 0, width // 2, height // 2), 2, out)
    assert png.size(out) == (width // 2 * 2, height // 2 * 2)
    # The crop decodes again, so it is a valid PNG, and upscaling doubled each pixel.
    _, _, _, bpp, _, _, rows = png._read(out)
    assert rows[0] == rows[1] and rows[0][:bpp] == rows[0][bpp : 2 * bpp]
