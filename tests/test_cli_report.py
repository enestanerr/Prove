import json
import shutil

import jsonschema
import pytest

from provecheck.cli import main
from provecheck.report import build_report, card, coverage_line, exit_code, html, md
from provecheck.schema import load_schema
from provecheck.verdict import check_claims


@pytest.fixture()
def workdir(root, tmp_path, monkeypatch):
    """A copy of the Kestrel example with the repo root as the working directory."""
    for name in ("claims.json", "figure2-crop.png"):
        shutil.copy(root / "examples" / "kestrel-q3" / name, tmp_path / name)
    monkeypatch.chdir(root)
    return tmp_path


@pytest.fixture(scope="module")
def report(kestrel_claims, kestrel_doc):
    return build_report(check_claims(kestrel_claims, kestrel_doc))


def test_ingest_check_report_in_sequence(workdir, capsys):
    doc, verdicts = workdir / "doc.json", workdir / "verdicts.json"
    assert main(["ingest", "examples/kestrel-q3/report.md", "-o", str(doc)]) == 0
    assert main(["check", str(workdir / "claims.json"), "--doc", str(doc)]) == 0
    assert verdicts.is_file()
    out = capsys.readouterr().out
    assert "3 contradicted, 1 suspect, 2 unverified, 4 verified" in out
    assert "Numeric statements found: 26   checked: 16   skipped with reason: 10   missed: 0" in out
    code = main(["report", str(verdicts), "--html", "--md", "--json", "--card"])
    assert code == 1  # at least one contradicted claim
    for name in ("prove-report.html", "prove-report.md", "prove-report.json", "prove-card.svg"):
        assert (workdir / name).is_file()


def test_report_defaults_and_fail_on(workdir):
    main(["check", str(workdir / "claims.json"), "--doc", "examples/kestrel-q3/report.md"])
    verdicts = str(workdir / "verdicts.json")
    assert main(["report", verdicts, "--fail-on", "never"]) == 0
    assert main(["report", verdicts, "--fail-on", "suspect"]) == 1
    assert (workdir / "prove-report.html").is_file() and not (workdir / "prove-card.svg").exists()


def test_check_rejects_an_invalid_claims_file(tmp_path, capsys):
    bad = tmp_path / "claims.json"
    bad.write_text(
        json.dumps(
            {
                "schema": "prove.claims.v1",
                "document": {"path": "x"},
                "numbers": [],
                "claims": [{"id": "c1", "kind": "x"}],
            }
        )
    )
    assert main(["check", str(bad)]) == 2
    assert 'claims[0].kind: must be "derived" or "chart"' in capsys.readouterr().err
    assert not (tmp_path / "verdicts.json").exists()


@pytest.mark.parametrize(
    "argv, message",
    [
        (["check", "missing.json"], "cannot read"),
        (["ingest", "missing.pdf"], "no such file"),
        (["report", "missing.json"], "cannot read"),
        (["crop", "--doc", "x.png", "--box", "1,2,3", "-o", "o.png"], "--box takes four numbers"),
        (["logic", "claims.json"], "arrives in v0.2"),
    ],
)
def test_usage_errors_exit_2_with_a_plain_message(argv, message, capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(argv) == 2
    assert message in capsys.readouterr().err


def test_no_command_prints_help(capsys):
    assert main([]) == 2
    assert "ingest" in capsys.readouterr().out


def test_scan_lists_tokens(root, capsys, monkeypatch):
    monkeypatch.chdir(root)
    assert main(["scan", "examples/kestrel-q3/report.md"]) == 0
    out = capsys.readouterr().out
    assert "p1  2.10M" in out and "26 numeric tokens" in out
    assert main(["scan", "examples/kestrel-q3/report.md", "--json"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 26


def test_relations_lists_every_op(capsys):
    assert main(["relations"]) == 0
    out = capsys.readouterr().out
    assert "pct_change" in out and "rank" in out


def test_crop_command(root, tmp_path, capsys):
    out = tmp_path / "crop.png"
    source = str(root / "examples" / "kestrel-q3" / "figure2.png")
    assert (
        main(["crop", "--doc", source, "--box", "0.5,0,1,1", "--upscale", "2", "-o", str(out)]) == 0
    )
    assert out.is_file() and "px" in capsys.readouterr().out


def test_crop_pdf_page(root, tmp_path):
    pytest.importorskip("pymupdf")
    out = tmp_path / "crop.png"
    source = str(root / "examples" / "kestrel-q3" / "report.pdf")
    assert main(["crop", "--doc", source, "--page", "3", "--box", "0,0,1,0.6", "-o", str(out)]) == 0
    assert out.stat().st_size > 1000
    assert main(["crop", "--doc", source, "--page", "9", "--box", "0,0,1,1", "-o", str(out)]) == 2


# --- report rendering ---------------------------------------------------------------------


def test_report_groups_claims_worst_first(report):
    verdicts = [r["verdict"] for r in report["claims"]]
    assert verdicts == sorted(
        verdicts, key=["contradicted", "suspect", "unverified", "verified"].index
    )
    assert report["schema"] == "prove.report.v1"
    jsonschema.validate(report, load_schema("report.v1.schema.json"))


def test_every_claim_carries_fixed_wording_for_its_verdict(report):
    by_id = {r["id"]: r for r in report["claims"]}
    assert by_id["c1"]["meaning"] == "No rounding of the printed numbers can produce this figure."
    assert (
        by_id["c5"]["meaning"] == "Possible only if the inputs sit at the edge of their rounding."
    )
    assert (
        by_id["c4"]["meaning"] == "The chart reading and the printed number cannot both be right."
    )
    assert report["sources"][0]["meaning"].startswith("Sources were not checked")


def test_markdown_report(report):
    text = md.render(report)
    assert "**3 contradicted · 1 suspect · 2 unverified · 4 verified**" in text
    assert "`2.30M ÷ 2.10M − 1 = 9.52%; possible range 9.03%–10.02%; the document says 14%`" in text
    assert (
        text.index("## Contradicted")
        < text.index("## Suspect")
        < text.index("## Unverified")
        < text.index("## Verified")
    )
    assert "A clean report means the checked claims passed." in text


def test_html_report_is_self_contained(report, root):
    page = html.render(report, root / "examples" / "kestrel-q3")
    assert "<script" not in page and "http://" not in page and "https://" not in page
    assert 'src="data:image/png;base64,' in page  # the chart crop is embedded
    assert page.count('class="card"') == 10  # eight claims and two sources
    assert "2.30M ÷ 2.10M − 1 = 9.52%" in page and "First reading" in page
    assert "A clean report means the checked claims passed." in page


def test_html_escapes_document_text(report):
    hostile = json.loads(json.dumps(report))
    hostile["claims"][0]["say"] = "<script>alert(1)</script>"
    hostile["claims"][0]["target"]["quote"] = '"><img src=x onerror=alert(1)>'
    page = html.render(hostile)
    assert "<script>alert(1)</script>" not in page and "<img src=x" not in page


def test_card_has_counts_and_no_document_content(report):
    svg = card.render(report)
    assert svg.startswith("<svg") and ">3<" in svg and "contradicted" in svg
    assert "Kestrel" not in svg and "report.md" not in svg


def test_missed_numbers_are_shown(kestrel_claims, kestrel_doc):
    claims = {**kestrel_claims, "skipped": []}
    rep = build_report(check_claims(claims, kestrel_doc))
    assert rep["coverage"]["missed"] == 10
    assert "## Missed (10)" in md.render(rep) and "Missed (10)" in html.render(rep)


def test_sources_file_replaces_the_placeholders(kestrel_claims, kestrel_doc):
    resolved = {"sources": [{"id": "s1", "kind": "doi", "value": "10.1234/example.2021.001", "verdict": "contradicted",
                             "assurance": "resolved", "reason": None, "message": "DOI does not resolve."}]}  # fmt: skip
    rep = build_report(check_claims(kestrel_claims, kestrel_doc), resolved)
    assert rep["summary"]["contradicted"] == 4 and rep["summary"]["unverified"] == 1
    assert rep["sources"][0]["id"] == "s1" and rep["sources"][0]["meaning"]


def test_coverage_line_and_exit_codes():
    assert "not available" in coverage_line(None)
    clean = {"contradicted": 0, "suspect": 2, "unverified": 1, "verified": 5}
    assert exit_code(clean) == 0 and exit_code(clean, "suspect") == 1
    assert (
        exit_code({**clean, "contradicted": 1}) == 1
        and exit_code({**clean, "contradicted": 1}, "never") == 0
    )


def test_text_prints_each_page_for_copying_quotes(root, capsys, monkeypatch):
    monkeypatch.chdir(root)
    assert main(["text", "examples/kestrel-q3/report.md", "--page", "2"]) == 0
    out = capsys.readouterr().out
    assert "===== page 2 =====" in out and "North | 1,204" in out and "page 1" not in out
    assert main(["text", "examples/kestrel-q3/report.md", "--page", "9"]) == 2
