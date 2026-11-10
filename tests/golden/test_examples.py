"""Golden tests for the other example documents, and PDF/Markdown agreement for all."""

import json
import shutil

import pytest

from provecheck.cli import main
from provecheck.ingest import ingest
from provecheck.verdict import check_claims

EXPECTED = ("prove-report.json", "prove-report.md", "prove-report.html", "prove-card.svg")
EXAMPLES = ("kestrel-q3", "larkspur-survey", "anadolu-kargo")

# The planted errors of each example, and the traps that must not be flagged.
PLANTED = {
    "kestrel-q3": {"c1", "c2", "c4"},
    "larkspur-survey": {"c2", "c12"},
    "anadolu-kargo": {"c2", "c6", "c7"},
}
TRAPS = {
    "kestrel-q3": {"c5": "suspect"},  # 2.1M -> 2.3M "up 14%" is possible within rounding
    "larkspur-survey": {"c3": "verified", "c13": "verified", "c14": "suspect"},
    "anadolu-kargo": {"c8": "verified", "c9": "verified", "c5": "verified"},
}


def gold(root, name):
    return json.loads((root / "examples" / name / "claims.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", EXAMPLES)
def test_contradicted_claims_are_exactly_the_planted_errors(root, name, monkeypatch):
    monkeypatch.chdir(root)
    result = check_claims(gold(root, name), ingest(f"examples/{name}/report.md"))
    verdicts = {r["id"]: r["verdict"] for r in result["claims"]}
    assert {i for i, v in verdicts.items() if v == "contradicted"} == PLANTED[name]
    for claim, expected in TRAPS[name].items():
        assert verdicts[claim] == expected
    assert result["coverage"]["missed"] == 0


@pytest.mark.parametrize("name", EXAMPLES)
def test_pdf_and_markdown_versions_agree(root, name, monkeypatch):
    pytest.importorskip("pymupdf")
    monkeypatch.chdir(root)
    claims = gold(root, name)
    as_md = check_claims(claims, ingest(f"examples/{name}/report.md"))
    as_pdf = check_claims(claims, ingest(f"examples/{name}/report.pdf"))
    assert [(r["id"], r["verdict"]) for r in as_pdf["claims"]] == [
        (r["id"], r["verdict"]) for r in as_md["claims"]
    ]
    assert as_pdf["coverage"] == as_md["coverage"]


@pytest.mark.parametrize("name", EXAMPLES[1:])
def test_reports_are_byte_stable(root, name, tmp_path, monkeypatch):
    example = root / "examples" / name
    shutil.copy(example / "claims.json", tmp_path / "claims.json")
    for crop in example.glob("*-crop.png"):
        shutil.copy(crop, tmp_path / crop.name)
    monkeypatch.chdir(root)
    doc = f"examples/{name}/report.md"
    assert main(["check", str(tmp_path / "claims.json"), "--doc", doc]) == 0
    flags = ["--html", "--md", "--json", "--card"]
    assert main(["report", str(tmp_path / "verdicts.json"), *flags]) == 1
    for file in EXPECTED:
        assert (tmp_path / file).read_bytes() == (example / file).read_bytes(), (
            f"{name}/{file} differs from the committed one; run tools/build_examples.py --reports"
        )


def test_value_label_inside_a_figure_is_tagged_read(root, monkeypatch):
    monkeypatch.chdir(root)
    doc = ingest("examples/larkspur-survey/report.md")
    result = check_claims(gold(root, "larkspur-survey"), doc)
    label_check = next(r for r in result["claims"] if r["id"] == "c12")
    assert label_check["assurance"] == "read" and label_check["verdict"] == "contradicted"
    assert "68" in label_check["sentence"]
