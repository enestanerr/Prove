"""The README carries no number that a script in the repo did not produce."""

import subprocess
import sys


def test_measured_block_matches_the_result_files(root):
    tool = str(root / "tools" / "readme_table.py")
    run = subprocess.run([sys.executable, tool, "--check"], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr


def test_report_excerpts_are_what_provecheck_printed(root):
    readme = (root / "README.md").read_text(encoding="utf-8")
    report = (root / "examples" / "kestrel-q3" / "prove-report.md").read_text(encoding="utf-8")
    quoted = [line.strip("> `") for line in readme.splitlines() if line.startswith("> `")]
    assert len(quoted) == 4
    for sentence in quoted:
        assert f"`{sentence}`" in report, sentence


def test_readme_links_point_at_files_that_exist(root):
    import re

    readme = (root / "README.md").read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)#]+)\)", readme):
        if not target.startswith("http"):
            assert (root / target).exists(), target


def test_prove_audits_its_own_readme(root, monkeypatch):
    """Dogfood: the README's own figures and citations pass a Prove audit."""
    import json

    from provecheck.ingest import ingest
    from provecheck.schema import validate_claims
    from provecheck.sources import resolve_all
    from provecheck.verdict import check_claims

    monkeypatch.chdir(root)
    claims = json.loads((root / "docs" / "readme-audit" / "claims.json").read_text("utf-8"))
    assert validate_claims(claims) == []
    result = check_claims(claims, ingest("README.md"))
    assert {r["id"]: r["verdict"] for r in result["claims"]} == dict.fromkeys(
        ["c1", "c2", "c3", "c4", "c5"], "verified"
    )
    cache = root / "tests" / "fixtures" / "sources" / "cache"
    sources = resolve_all(claims["sources"], offline=True, cache_dir=cache)
    assert [s["verdict"] for s in sources["sources"]] == ["verified", "verified"]
