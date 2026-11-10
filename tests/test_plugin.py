"""The plugin folder follows the constraints recorded in CLAUDE.md and docs/SKILL-DRAFT.md."""

import json
import re
import subprocess
import sys

import provecheck

# Frontmatter keys that claude.ai skill uploads accept (Agent Skills spec).
PORTABLE_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def test_versions_agree(root):
    manifest = json.loads((root / "plugin" / ".claude-plugin" / "plugin.json").read_text("utf-8"))
    pyproject = (root / "pyproject.toml").read_text("utf-8")
    declared = re.search(r'^version = "([^"]+)"', pyproject, re.M).group(1)
    assert manifest["version"] == declared == provecheck.__version__
    assert manifest["name"] == "prove"


def test_marketplace_points_at_the_plugin_folder(root):
    market = json.loads((root / ".claude-plugin" / "marketplace.json").read_text("utf-8"))
    (entry,) = market["plugins"]
    assert entry["name"] == "prove" and entry["source"] == "./plugin"
    assert market["name"] == "enestanerr"


def test_plugin_layout_constraints(root):
    plugin = root / "plugin"
    assert [p.name for p in (plugin / ".claude-plugin").iterdir()] == ["plugin.json"]
    assert not (plugin / "bin").exists(), "claude.ai and Cowork refuse plugins with a bin/ folder"
    assert not (plugin / "CLAUDE.md").exists(), "a CLAUDE.md at a plugin root fails validation"


def test_skill_frontmatter_is_portable(root):
    text = (root / "plugin" / "skills" / "prove" / "SKILL.md").read_text("utf-8")
    assert text.startswith("---\n")
    front, body = text[4:].split("\n---\n", 1)
    keys = set(re.findall(r"^([A-Za-z_-]+):", front, re.M))
    assert keys <= PORTABLE_KEYS and {"name", "description"} <= keys
    assert len(body.splitlines()) < 150, "keep SKILL.md short; detail belongs in reference/"
    for ref in ("claims-schema.md", "charts.md", "examples.md"):
        assert ref in body
        assert (root / "plugin" / "skills" / "prove" / "reference" / ref).is_file()


def test_skill_examples_are_valid_claims_files(root):
    """The JSON examples the model learns from must pass the validator themselves."""
    from provecheck.schema import validate_claims

    path = root / "plugin" / "skills" / "prove" / "reference" / "examples.md"
    blocks = re.findall(r"```json\n(.*?)```", path.read_text("utf-8"), re.S)
    assert len(blocks) == 2
    for block in blocks:
        assert validate_claims(json.loads(block)) == []


def test_committed_zipapp_is_fresh_and_runs(root, tmp_path):
    builder = str(root / "tools" / "build_pyz.py")
    check = subprocess.run([sys.executable, builder, "--check"], capture_output=True, text=True)
    assert check.returncode == 0, check.stderr
    pyz = root / "plugin" / "skills" / "prove" / "scripts" / "provecheck.pyz"
    # -I isolates Python from the environment: the zipapp must need nothing installed.
    args = ["check", "examples/kestrel-q3/claims.json", "--doc", "examples/kestrel-q3/report.md"]
    run = subprocess.run(
        [sys.executable, "-I", str(pyz), *args, "-o", str(tmp_path / "verdicts.json")],
        capture_output=True,
        text=True,
        cwd=root,
        encoding="utf-8",
    )
    assert run.returncode == 0, run.stderr
    assert "3 contradicted, 1 suspect, 2 unverified, 4 verified" in run.stdout
