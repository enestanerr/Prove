"""Golden test: the whole pipeline on the Kestrel example reproduces the committed report.

If a deliberate change to report wording or layout breaks this, rebuild the
expected files with ``uv run python tools/build_examples.py --reports`` and
review the diff.
"""

import shutil

import pytest

from provecheck.cli import main

EXPECTED = ("prove-report.json", "prove-report.md", "prove-report.html", "prove-card.svg")


@pytest.fixture(scope="module")
def produced(root, tmp_path_factory):
    out = tmp_path_factory.mktemp("kestrel")
    example = root / "examples" / "kestrel-q3"
    for name in ("claims.json", "figure2-crop.png"):
        shutil.copy(example / name, out / name)
    with pytest.MonkeyPatch.context() as mp:
        mp.chdir(root)
        assert main(["ingest", "examples/kestrel-q3/report.md", "-o", str(out / "doc.json")]) == 0
        assert main(["check", str(out / "claims.json"), "--doc", str(out / "doc.json")]) == 0
        code = main(["report", str(out / "verdicts.json"), "--html", "--md", "--json", "--card"])
    return out, code


def test_exit_code_is_1_because_claims_are_contradicted(produced):
    assert produced[1] == 1


@pytest.mark.parametrize("name", EXPECTED)
def test_report_is_byte_stable(produced, root, name):
    expected = (root / "examples" / "kestrel-q3" / name).read_bytes()
    assert (produced[0] / name).read_bytes() == expected, (
        f"{name} differs from the committed one; run tools/build_examples.py --reports"
    )


def test_html_shows_the_planted_errors(root):
    page = (root / "examples" / "kestrel-q3" / "prove-report.html").read_text(encoding="utf-8")
    for claim, verdict in (
        ("c1", "contradicted"),
        ("c2", "contradicted"),
        ("c3", "verified"),
        ("c4", "contradicted"),
        ("c5", "suspect"),
    ):
        card = page[page.index(f'id="{claim}"') - 80 : page.index(f'id="{claim}"') + 200]
        assert f'<span class="verdict">{verdict}</span>' in card


def test_pdf_and_markdown_versions_get_the_same_verdicts(root, tmp_path, monkeypatch):
    pytest.importorskip("pymupdf")
    import json

    from provecheck.ingest import ingest
    from provecheck.verdict import check_claims

    monkeypatch.chdir(root)
    claims = json.loads(
        (root / "examples" / "kestrel-q3" / "claims.json").read_text(encoding="utf-8")
    )
    as_md = check_claims(claims, ingest("examples/kestrel-q3/report.md"))
    as_pdf = check_claims(claims, ingest("examples/kestrel-q3/report.pdf"))
    assert [(r["id"], r["verdict"]) for r in as_pdf["claims"]] == [
        (r["id"], r["verdict"]) for r in as_md["claims"]
    ]
    assert as_pdf["coverage"] == as_md["coverage"]
