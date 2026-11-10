"""Source resolvers, run offline against recorded answers (no network in tests)."""

import json

import pytest

from provecheck import CONTRADICTED, UNVERIFIED, VERIFIED
from provecheck.cli import main
from provecheck.sources import Outcome, compare_title, resolve_all, similarity
from provecheck.sources.client import Client
from provecheck.sources.quote import closest, page_text


@pytest.fixture(scope="module")
def recorded(root):
    """Every source of the fixture file, resolved from the recorded registry answers."""
    folder = root / "tests" / "fixtures" / "sources"
    claims = json.loads((folder / "claims.json").read_text(encoding="utf-8"))
    result = resolve_all(claims["sources"], offline=True, cache_dir=folder / "cache")
    return {rec["id"]: rec for rec in result["sources"]}


@pytest.mark.parametrize(
    "source, verdict, words",
    [
        ("doi-real", VERIFIED, "matching the cited title"),
        ("doi-short-title", VERIFIED, "resolves to “The GRIM Test”"),
        ("doi-missing", CONTRADICTED, "does not resolve"),
        ("doi-other-work", CONTRADICTED, "resolves to a different work"),
        ("doi-datacite", VERIFIED, "Attention Is All You Need"),
        ("arxiv-real", VERIFIED, "arXiv 1706.03762 resolves"),
        ("arxiv-missing", CONTRADICTED, "arXiv has no paper with this id"),
        ("url-ok", VERIFIED, "The page loads (200)"),
        ("url-missing", CONTRADICTED, "404 Not Found"),
        ("quote-ok", VERIFIED, "The quoted words appear on the source page"),
        ("quote-altered", CONTRADICTED, "without prior coordination with us"),
        ("quote-absent", UNVERIFIED, "nothing like the quotation was found"),
    ],
)
def test_recorded_answers(recorded, source, verdict, words):
    rec = recorded[source]
    assert rec["verdict"] == verdict and words in rec["message"]
    assert rec["assurance"] == "resolved"


def test_wording_is_factual(recorded):
    for rec in recorded.values():
        assert "fabricat" not in rec["message"].lower() and "fake" not in rec["message"].lower()


def test_an_altered_quotation_shows_the_closest_real_passage(recorded):
    rec = recorded["quote-altered"]
    assert rec["found"]["similarity"] >= 0.75
    assert rec["found"]["closest"].startswith("these domains may be used as illustrative examples")


def test_offline_without_a_cached_answer_is_unverified(tmp_path):
    sources = [
        {"id": "s1", "kind": "doi", "value": "10.1000/182"},
        {"id": "s2", "kind": "arxiv", "value": "1706.03762"},
        {"id": "s3", "kind": "url", "value": "https://example.org/"},
        {"id": "s4", "kind": "quote", "value": "https://example.org/", "quote": "words"},
    ]
    result = resolve_all(sources, offline=True, cache_dir=tmp_path)
    assert [(r["verdict"], r["reason"]) for r in result["sources"]] == [(UNVERIFIED, "offline")] * 4


def fake(cache, url: str, status: int, body: str = "") -> None:
    """Put one answer in a cache folder, as the client itself would have stored it."""
    client = Client(cache)
    cache.mkdir(parents=True, exist_ok=True)
    record = {"url": url, "status": status, "body": body}
    client._path(url).write_text(json.dumps(record), encoding="utf-8")


def resolve_one(cache, source: dict) -> dict:
    return resolve_all([{"id": "s1", **source}], offline=True, cache_dir=cache)["sources"][0]


@pytest.mark.parametrize("status, words", [(403, "access is refused"), (401, "needs a login"), (500, "answered with an error"), (429, "too many requests")])  # fmt: skip
def test_anything_short_of_a_clear_answer_is_unverified(tmp_path, status, words):
    fake(tmp_path, "https://example.org/report", status)
    rec = resolve_one(tmp_path, {"kind": "url", "value": "https://example.org/report"})
    assert (
        rec["verdict"] == UNVERIFIED and rec["reason"] == "unreachable" and words in rec["message"]
    )


def test_gone_is_as_clear_as_not_found(tmp_path):
    fake(tmp_path, "https://example.org/old", 410)
    rec = resolve_one(tmp_path, {"kind": "url", "value": "https://example.org/old"})
    assert rec["verdict"] == CONTRADICTED and "410 Gone" in rec["message"]


def test_a_registry_error_never_becomes_a_missing_doi(tmp_path):
    fake(tmp_path, "https://api.crossref.org/works/10.1000/182", 503)
    rec = resolve_one(tmp_path, {"kind": "doi", "value": "10.1000/182", "cited_title": "A title"})
    assert rec["verdict"] == UNVERIFIED and "Crossref answered 503" in rec["message"]


def test_doi_known_only_to_the_handle_registry(tmp_path):
    fake(tmp_path, "https://api.crossref.org/works/10.5555/abc", 404)
    fake(tmp_path, "https://api.datacite.org/dois/10.5555/abc", 404)
    fake(tmp_path, "https://doi.org/api/handles/10.5555/abc", 200, '{"responseCode": 1}')
    with_title = resolve_one(tmp_path, {"kind": "doi", "value": "10.5555/abc", "cited_title": "T"})
    assert with_title["verdict"] == UNVERIFIED and with_title["reason"] == "no-title"
    assert resolve_one(tmp_path, {"kind": "doi", "value": "10.5555/abc"})["verdict"] == VERIFIED


def test_similar_but_not_identical_title_is_unverified(tmp_path):
    body = json.dumps({"message": {"title": ["Rounding errors in annual company reports"]}})
    fake(tmp_path, "https://api.crossref.org/works/10.5555/xyz", 200, body)
    rec = resolve_one(
        tmp_path,
        {
            "kind": "doi",
            "value": "10.5555/xyz",
            "cited_title": "Rounding errors in quarterly company filings",
        },
    )
    assert rec["verdict"] == UNVERIFIED and rec["reason"] == "title-differs"


@pytest.mark.parametrize("value", ["not-an-id", "17.03762", "1706.03762; DROP"])
def test_malformed_arxiv_id_never_reaches_the_network(tmp_path, value):
    rec = resolve_one(tmp_path, {"kind": "arxiv", "value": value})
    assert rec["verdict"] == CONTRADICTED and "not a valid arXiv identifier" in rec["message"]


def test_quote_on_a_page_with_almost_no_text_is_unverified(tmp_path):
    fake(
        tmp_path, "https://example.org/app", 200, "<html><body><div id='root'></div></body></html>"
    )
    rec = resolve_one(
        tmp_path,
        {"kind": "quote", "value": "https://example.org/app", "quote": "Some quoted words here."},
    )
    assert rec["verdict"] == UNVERIFIED and rec["reason"] == "no-text"


def test_quote_from_a_missing_page_is_unverified_not_contradicted(tmp_path):
    fake(tmp_path, "https://example.org/gone", 404)
    rec = resolve_one(
        tmp_path, {"kind": "quote", "value": "https://example.org/gone", "quote": "Some words."}
    )
    assert rec["verdict"] == UNVERIFIED and rec["reason"] == "source-missing"


def test_quote_matching_ignores_case_punctuation_and_markup(tmp_path):
    page = (
        "<p>The committee found that <b>costs rose</b> by a third &mdash; “far more” than planned.</p>"
        + "<p>filler text</p>" * 60
    )
    fake(tmp_path, "https://example.org/a", 200, page)
    rec = resolve_one(
        tmp_path,
        {
            "kind": "quote",
            "value": "https://example.org/a",
            "quote": 'costs rose by a third - "far more" than planned',
        },
    )
    assert rec["verdict"] == VERIFIED


def test_non_web_sources_are_unverified(tmp_path):
    assert (
        resolve_one(tmp_path, {"kind": "url", "value": "ftp://example.org/x"})["reason"]
        == "not-a-url"
    )
    assert (
        resolve_one(tmp_path, {"kind": "quote", "value": "Annual report, p. 4", "quote": "words"})[
            "reason"
        ]
        == "not-a-url"
    )


@pytest.mark.parametrize(
    "cited, real, match",
    [
        ("The GRIM Test", "The GRIM Test: A Simple Technique Detects Numerous Anomalies", True),
        ("Attention is all you need", "Attention Is All You Need", True),
        ("Attention Is All You Need.", "Attention is all you need", True),
        (
            "Deep learning",
            "Deep learning for image segmentation: a survey",
            False,
        ),  # two words: too little
        ("A survey of image segmentation", "The prevalence of statistical reporting errors", False),
    ],
)
def test_title_similarity(cited, real, match):
    assert (similarity(cited, real) >= 0.85) is match


def test_compare_title_without_a_cited_title_checks_existence_only():
    out = compare_title(None, "Some Real Title", 2020, "DOI 10.1/x")
    assert isinstance(out, Outcome) and out.verdict == VERIFIED


def test_page_text_strips_markup_and_scripts():
    text = page_text("<html><body><script>var a = 1;</script><p>Visible   words</p></body></html>")
    assert text == "Visible words"


def test_closest_passage_finds_an_altered_sentence():
    text = "Intro words here. The quick brown fox jumps over the lazy dog every single morning. Closing words."
    score, passage = closest(
        "The quick brown fox leaps over the lazy cat every single morning", text
    )
    assert score > 0.8 and passage.startswith("the quick brown fox jumps")


def test_answers_are_cached_and_reused(tmp_path):
    fake(tmp_path, "https://example.org/x", 200, "hello")
    client = Client(tmp_path, offline=True)
    assert client.get("https://example.org/x").body == "hello"
    assert client.get("https://example.org/y").error == "offline"


def test_default_user_agent_names_the_project():
    assert (
        "provecheck/" in Client().user_agent
        and "github.com/enestanerr/prove" in Client().user_agent
    )


def test_sources_command_and_report_merge(root, tmp_path, capsys, monkeypatch):
    """`provecheck sources` then `report`: the resolved verdicts replace the placeholders."""
    import shutil

    shutil.copy(root / "examples" / "kestrel-q3" / "claims.json", tmp_path / "claims.json")
    monkeypatch.chdir(root)
    cache = str(root / "tests" / "fixtures" / "sources" / "cache")
    claims = str(tmp_path / "claims.json")
    assert main(["check", claims, "--doc", "examples/kestrel-q3/report.md"]) == 0
    assert main(["sources", claims, "--offline", "--cache", cache]) == 0
    out = capsys.readouterr().out
    assert "contradicted s1 doi: 10.1234/example.2021.001" in out and "verified     s2" in out
    assert main(["report", str(tmp_path / "verdicts.json"), "--md"]) == 1
    report = (tmp_path / "prove-report.md").read_text(encoding="utf-8")
    assert "**4 contradicted · 1 suspect · 0 unverified · 5 verified**" in report
    assert "does not resolve: Crossref, DataCite and doi.org answer “not found”" in report


@pytest.mark.parametrize(
    "address, public",
    [
        ("https://example.org/report", True),
        ("http://93.184.216.34/x", True),
        ("http://localhost:8080/admin", False),
        ("http://127.0.0.1/", False),
        ("http://192.168.1.1/router", False),
        ("http://169.254.169.254/latest/meta-data", False),
        ("http://[::1]/", False),
        ("http://intranet.local/wiki", False),
        ("file:///etc/passwd", False),
        ("ftp://example.org/x", False),
    ],
)
def test_only_public_web_addresses_are_fetched(address, public, tmp_path):
    from provecheck.sources.client import is_public_web_address

    assert is_public_web_address(address) is public
    if not public:
        rec = resolve_one(tmp_path, {"kind": "quote", "value": address, "quote": "some words"})
        assert rec["verdict"] == UNVERIFIED and rec["reason"] == "not-a-url"
