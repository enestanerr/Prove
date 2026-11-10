import copy

import jsonschema
import pytest
from helpers import claims_file, const, derived, num, op

from provecheck.relations import REGISTRY
from provecheck.schema import load_schema, validate_claims


def base() -> dict:
    numbers = [num("a", "165"), num("b", "186"), num("t", "12.7%")]
    chart = {
        "id": "g1", "loc": {"page": 1, "figure": "Figure 1"}, "type": "bar",
        "y_axis": {"min": "0", "max": "400", "scale": "linear"},
        "marks": [
            {"label": "Q3", "read_a": {"lo": "300", "hi": "320"}, "read_b": {"lo": "302", "hi": "318"}},
            {"label": "Q2", "read_a": {"lo": "200", "hi": "220"}, "read_b": {"lo": "202", "hi": "218"}},
        ],
    }  # fmt: skip
    claims = [
        derived("c1", "t", op("pct_change", "a", "b")),
        {"id": "c2", "kind": "chart", "check": "text_vs_chart", "target": "a", "chart": "g1",
         "mark": {"label": "Q3"}, "say": "The prose should match the bar."},
    ]  # fmt: skip
    sources = [
        {"id": "s1", "kind": "doi", "value": "10.1000/182", "loc": {"page": 1, "quote": "[1]"}}
    ]
    return claims_file(
        numbers,
        claims,
        charts=[chart],
        sources=sources,
        skipped=[{"text": "2026", "reason": "year"}],
    )


def test_valid_file_has_no_errors():
    assert validate_claims(base()) == []


def test_examples_are_valid(kestrel_claims, reference_claims):
    assert validate_claims(kestrel_claims) == []
    assert validate_claims(reference_claims) == []


def test_examples_also_satisfy_the_json_schema(kestrel_claims, reference_claims):
    schema = load_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    for data in (kestrel_claims, reference_claims, base()):
        jsonschema.validate(data, schema)


def mutate(path: list, value="__delete__"):
    data = base()
    node = data
    for key in path[:-1]:
        node = node[key]
    if value == "__delete__":
        del node[path[-1]]
    else:
        node[path[-1]] = value
    return data


# (path to change, new value, text that must appear in the error)
BAD = [
    (["schema"], "prove.claims.v0", 'schema: must be "prove.claims.v1"'),
    (["document"], "__delete__", "document: is required"),
    (["numbers"], "__delete__", "numbers: is required"),
    (["numbers", 0, "text"], "", "numbers[0].text: must not be empty"),
    (["numbers", 0, "value"], "1,650", "numbers[0].value: must be a plain decimal string"),
    (["numbers", 0, "value"], 165, "numbers[0].value: must be str"),
    (["numbers", 0, "decimals"], -1, "numbers[0].decimals: must be 0 or more"),
    (
        ["numbers", 0, "exact"],
        "sure",
        "numbers[0].exact: must be null or one of count, ledger, defined, cell",
    ),
    (["numbers", 0, "scale"], "lots", "numbers[0].scale"),
    (["numbers", 0, "loc"], "__delete__", "numbers[0].loc: is required"),
    (["numbers", 0, "loc", "page"], 0, "numbers[0].loc.page: pages are numbered from 1"),
    (["numbers", 0, "loc", "quote"], " ", "numbers[0].loc.quote: must not be empty"),
    (["numbers", 1, "id"], "a", "numbers[1].id: duplicate id 'a'"),
    (["claims", 0, "kind"], "guess", 'claims[0].kind: must be "derived" or "chart"'),
    (["claims", 0, "target"], "zz", "claims[0].target: no number with id 'zz'"),
    (["claims", 0, "target"], "__delete__", "claims[0].target: is required"),
    (["claims", 0, "hedge"], "maybe", "claims[0].hedge: must be null or one of"),
    (["claims", 0, "say"], "", "claims[0].say: must be one plain sentence"),
    (["claims", 0, "derivation"], "__delete__", "claims[0].derivation: is required"),
    (["claims", 0, "derivation"], "a + b", "claims[0].derivation: must be"),
    (
        ["claims", 0, "derivation", "op"],
        "average",
        "claims[0].derivation.op: unknown op 'average'; known ops:",
    ),
    (
        ["claims", 0, "derivation", "args"],
        [{"ref": "a"}],
        "pct_change takes exactly 2 arguments, got 1",
    ),
    (
        ["claims", 0, "derivation", "args", 0],
        {"ref": "nope"},
        "claims[0].derivation.args[0].ref: no number with id 'nope'",
    ),
    (
        ["claims", 0, "derivation", "args", 0],
        {"const": "ten"},
        "claims[0].derivation.args[0].const: must be a decimal string",
    ),
    (
        ["claims", 0, "derivation", "args", 0],
        {"ref": "a", "const": "1"},
        'must have exactly one of "ref", "const", "op"',
    ),
    (["claims", 1, "check"], "vibes", "claims[1].check: must be one of label_vs_mark"),
    (["claims", 1, "chart"], "g9", "claims[1].chart: no chart with id 'g9'"),
    (["claims", 1, "mark"], {"label": "Q9"}, "claims[1].mark: chart 'g1' has no mark 'Q9'"),
    (["claims", 1, "target"], "__delete__", "claims[1].target: is required"),
    (["charts", 0, "y_axis"], "__delete__", "charts[0].y_axis: is required"),
    (["charts", 0, "y_axis", "max"], "0", "charts[0].y_axis: min must be less than max"),
    (
        ["charts", 0, "y_axis", "scale"],
        "cubic",
        "charts[0].y_axis.scale: must be one of linear, log",
    ),
    (["charts", 0, "marks", 0, "read_a"], "__delete__", "charts[0].marks[0].read_a: is required"),
    (
        ["charts", 0, "marks", 0, "read_a"],
        {"lo": "320", "hi": "300"},
        "charts[0].marks[0].read_a: lo is greater than hi",
    ),
    (
        ["charts", 0, "marks", 0, "read_b"],
        {"lo": "x", "hi": "1"},
        "charts[0].marks[0].read_b.lo: must be a plain decimal string",
    ),
    (
        ["charts", 0, "marks", 0, "printed_label"],
        "zz",
        "charts[0].marks[0].printed_label: no number with id 'zz'",
    ),
    (["sources", 0, "kind"], "book", "sources[0].kind: must be one of doi, arxiv, url, quote"),
    (["sources", 0, "value"], "__delete__", "sources[0].value: is required"),
    (["skipped", 0, "reason"], "", "skipped[0].reason: must say why"),
    (["skipped", 0, "text"], "__delete__", 'skipped[0]: needs "text", or a "loc.quote"'),
]


@pytest.mark.parametrize("path, value, message", BAD)
def test_error_messages_name_the_exact_path(path, value, message):
    errors = validate_claims(mutate(path, value))
    assert any(message in e for e in errors), errors


def test_not_an_object():
    assert validate_claims([]) == ["claims file: must be a JSON object"]


def test_log_axis_cannot_start_at_zero():
    data = mutate(["charts", 0, "y_axis", "scale"], "log")
    assert any("log axis cannot start at 0" in e for e in validate_claims(data))


def test_pie_needs_no_axis():
    data = mutate(["charts", 0, "type"], "pie")
    del data["charts"][0]["y_axis"]
    assert validate_claims(data) == []


def test_rank_needs_no_target():
    data = base()
    data["claims"][0] = derived("c1", None, op("rank", "a", "b", const("1")))
    assert validate_claims(data) == []


def test_eq_with_two_arguments_must_start_with_the_target():
    data = base()
    data["claims"][0] = derived("c1", "t", op("eq", "a", "b"))
    assert any("eq's first must be the claim's target" in e for e in validate_claims(data))


def test_order_claim_needs_a_relation_and_sometimes_a_second_mark():
    data = base()
    claim = {
        "id": "c2",
        "kind": "chart",
        "check": "order",
        "chart": "g1",
        "mark": {"label": "Q3"},
        "say": "Tallest.",
    }
    data["claims"][1] = claim
    assert any("claims[1].relation" in e for e in validate_claims(data))
    claim["relation"] = "gt"
    assert any("claims[1].than" in e for e in validate_claims(data))
    claim["than"] = {"label": "Q2"}
    assert validate_claims(data) == []


def test_quote_source_needs_the_quoted_words():
    data = base()
    data["sources"][0] = {"id": "s1", "kind": "quote", "value": "https://example.org"}
    assert any("sources[0].quote" in e for e in validate_claims(data))


def test_deeply_nested_derivation_is_rejected():
    node = {"ref": "a"}
    for _ in range(30):
        node = {"op": "sum", "args": [node]}
    data = base()
    data["claims"][0]["derivation"] = node
    assert any("nested deeper" in e for e in validate_claims(data))


def test_every_error_is_reported_at_once():
    data = base()
    data["numbers"][0]["value"] = "x"
    data["claims"][0]["target"] = "zz"
    data["sources"][0]["kind"] = "book"
    assert len(validate_claims(data)) == 3


def test_validator_and_json_schema_agree_on_a_broken_file():
    broken = copy.deepcopy(base())
    broken["numbers"][0]["value"] = "1,650"
    assert validate_claims(broken)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(broken, load_schema())


def test_every_registered_relation_documents_itself():
    for name, rel in REGISTRY.items():
        assert rel.summary and rel.min_args >= 1, name
