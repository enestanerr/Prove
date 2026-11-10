"""The eval scorer, checked on the examples: gold claims must score perfectly."""

import copy
import json
import sys

import pytest

from provecheck.ingest import ingest
from provecheck.verdict import check_claims

EXAMPLES = ("kestrel-q3", "larkspur-survey", "anadolu-kargo")


@pytest.fixture(scope="module")
def scoring(root):
    sys.path.insert(0, str(root / "evals"))
    import score

    return score


def load(root, name):
    folder = root / "examples" / name
    claims = json.loads((folder / "claims.json").read_text(encoding="utf-8"))
    truth = json.loads((folder / "truth.json").read_text(encoding="utf-8"))
    return claims, truth, ingest(folder / "report.md")


@pytest.mark.parametrize("name", EXAMPLES)
def test_gold_claims_catch_every_planted_error_with_no_false_alarm(root, scoring, name):
    claims, truth, doc = load(root, name)
    s = scoring.score_claims(truth, claims, check_claims(claims, doc), doc)
    assert s["caught"] == s["planted_total"] == len(truth["planted"])
    assert s["false_alarms"] == [] and s["cascades"] == [] and s["traps_flagged"] == 0
    assert all(t["outcome"] != "no-claim" for t in s["traps"]), "every trap is exercised"


@pytest.mark.parametrize("name", EXAMPLES)
def test_gold_chart_readings_contain_the_true_values(root, scoring, name):
    claims, truth, _ = load(root, name)
    marks = scoring.score_charts(truth, claims)
    assert marks and all(m["contains_true_value"] for m in marks)
    assert max(m["error_share_of_span"] for m in marks) < 0.02


def test_a_missing_claim_is_scored_as_no_claim(root, scoring):
    claims, truth, doc = load(root, "kestrel-q3")
    claims = copy.deepcopy(claims)
    claims["claims"] = [c for c in claims["claims"] if c["id"] != "c2"]
    s = scoring.score_claims(truth, claims, check_claims(claims, doc), doc)
    assert s["caught"] == 2
    assert {p["id"]: p["outcome"] for p in s["planted"]}["e2"] == "no-claim"


def test_a_contradiction_on_a_clean_number_is_a_false_alarm(root, scoring):
    """Marking the rounded subscriber figures exact turns the trap into a false alarm."""
    claims, truth, doc = load(root, "kestrel-q3")
    claims = copy.deepcopy(claims)
    for n in claims["numbers"]:
        if n["id"] in ("n11", "n12"):
            n["exact"] = "count"
    s = scoring.score_claims(truth, claims, check_claims(claims, doc), doc)
    assert [a["kind"] for a in s["false_alarms"]] == ["trap"] and s["traps_flagged"] == 1


def test_a_claim_built_on_a_planted_number_is_a_cascade_not_a_false_alarm(root, scoring):
    """East's share against the wrong printed total: a knock-on effect of the planted error."""
    claims, truth, doc = load(root, "kestrel-q3")
    claims = copy.deepcopy(claims)
    share = next(c for c in claims["claims"] if c["id"] == "c3")
    share["derivation"] = {"op": "pct_of", "args": [{"ref": "n6"}, {"ref": "n8"}]}
    s = scoring.score_claims(truth, claims, check_claims(claims, doc), doc)
    assert s["false_alarms"] == [] and [a["claim"] for a in s["cascades"]] == ["c3"]


def test_unread_chart_marks_are_reported(root, scoring):
    claims, truth, _ = load(root, "kestrel-q3")
    claims = {**claims, "charts": []}
    assert {m["status"] for m in scoring.score_charts(truth, claims)} == {"not-read"}
