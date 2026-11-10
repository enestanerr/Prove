from fractions import Fraction as F

import pytest
from helpers import claims_file, const, derived, doc_of, num, op, quick, run, verdict_of

from provecheck import CONTRADICTED, SUSPECT, UNVERIFIED, VERIFIED
from provecheck.intervals import Interval, Target
from provecheck.verdict import check_claims, judge


def test_judge_is_the_three_way_rule():
    target = Target.of(Interval(F(135, 10), F(145, 10)))
    assert judge(target, F(14), Interval(F(13), F(15))) == VERIFIED
    assert judge(target, F(952, 100), Interval(F(465, 100), F(1463, 100))) == SUSPECT
    assert judge(target, F(952, 100), Interval(F(903, 100), F(1002, 100))) == CONTRADICTED


def test_example_claims_expected_verdicts(reference_claims, kestrel_doc):
    """PLAN Phase 1: the reference claims file gives its own expected verdicts."""
    result = check_claims(reference_claims, kestrel_doc)
    got = {r["id"]: r["verdict"] for r in result["claims"]}
    assert got == reference_claims["expected_verdicts"]


def test_kestrel_example_verdicts(kestrel_claims, kestrel_doc):
    result = check_claims(kestrel_claims, kestrel_doc)
    got = {r["id"]: r["verdict"] for r in result["claims"]}
    assert got == {
        "c1": CONTRADICTED, "c2": CONTRADICTED, "c3": VERIFIED, "c4": CONTRADICTED,
        "c5": SUSPECT, "c6": VERIFIED, "c7": VERIFIED, "c8": VERIFIED,
    }  # fmt: skip
    assert result["coverage"]["missed"] == 0


def test_the_computation_is_written_out():
    v = quick(
        "from $2.10M to $2.30M, up 14%",
        {"a": "2.10M", "b": "2.30M", "t": "14%"},
        "t",
        op("pct_change", "a", "b"),
    )
    assert (
        v["sentence"]
        == "2.30M ÷ 2.10M − 1 = 9.52%; possible range 9.03%–10.02%; the document says 14%"
    )
    assert v["computation"] == "2.30M ÷ 2.10M − 1"
    assert v["numbers"] == ["a", "b", "t"]


def test_nested_derivations_are_parenthesised():
    v = quick("1,356 of 1,204 and 3,588 is 28.3%", {"p": "1,356", "a": "1,204", "b": "3,588", "t": "28.3%"}, "t",
              op("pct_of", "p", op("sum", "a", "b")), exact={"p", "a", "b"})  # fmt: skip
    assert v["verdict"] == VERIFIED and v["computation"] == "1,356 ÷ (1,204 + 3,588)"


# --- grounding: an altered number never reaches the arithmetic ----------------------------


def test_altered_number_is_not_grounded():
    """The document says 2.10M. A model that writes 2.20M is stopped here."""
    numbers = [
        num("a", "2.20M", quote="from $2.20M to $2.30M"),
        num("b", "2.30M", quote="from $2.10M to $2.30M"),
        num("t", "14%", quote="up 14%"),
    ]
    v = verdict_of(
        run(
            ["Revenue rose from $2.10M to $2.30M, up 14%."],
            numbers,
            [derived("c1", "t", op("pct_change", "a", "b"))],
        )
    )
    assert v["verdict"] == UNVERIFIED and v["reason"] == "not-grounded"
    assert "not found on page 1" in v["message"]


def test_text_outside_its_quote_is_not_grounded():
    numbers = [
        num("a", "165", quote="from 165"),
        num("b", "186", quote="from 165 to"),
        num("t", "12.7%", quote="up 12.7%"),
    ]
    v = verdict_of(
        run(
            ["from 165 to 186, up 12.7%"], numbers, [derived("c1", "t", op("pct_change", "a", "b"))]
        )
    )
    assert v["reason"] == "not-grounded" and "not inside its quote" in v["message"]


def test_wrong_page_is_not_grounded_and_says_where_the_quote_is():
    numbers = [num("a", "165", page=2), num("b", "186"), num("t", "12.7%")]
    result = run(
        ["from 165 to 186, up 12.7%", "nothing here"],
        numbers,
        [derived("c1", "t", op("pct_change", "a", "b"))],
    )
    v = verdict_of(result)
    assert v["reason"] == "not-grounded" and "it occurs on page 1" in v["message"]


def test_missing_page_is_not_grounded():
    numbers = [num("a", "165", page=9), num("b", "186"), num("t", "12.7%")]
    v = verdict_of(
        run(
            ["from 165 to 186, up 12.7%"], numbers, [derived("c1", "t", op("pct_change", "a", "b"))]
        )
    )
    assert v["reason"] == "not-grounded" and "page 9 does not exist" in v["message"]


@pytest.mark.parametrize("field, value", [("value", "2200000"), ("decimals", 1)])
def test_value_that_disagrees_with_the_printed_text_is_a_parse_mismatch(field, value):
    a = num("a", "2.10M")
    a[field] = value
    numbers = [a, num("b", "2.30M"), num("t", "14%")]
    v = verdict_of(
        run(
            ["from 2.10M to 2.30M, up 14%"],
            numbers,
            [derived("c1", "t", op("pct_change", "a", "b"))],
        )
    )
    assert v["verdict"] == UNVERIFIED and v["reason"] == "parse-mismatch"


def test_unparseable_text_is_a_parse_error():
    a = {"id": "a", "text": "12 widgets", "value": "12", "loc": {"page": 1, "quote": "12 widgets"}}
    v = verdict_of(
        run(
            ["12 widgets and 6 more is 18"],
            [a, num("b", "6"), num("t", "18")],
            [derived("c1", "t", op("sum", "a", "b"))],
        )
    )
    assert v["verdict"] == UNVERIFIED and v["reason"] == "parse-error"


def test_typography_does_not_break_grounding():
    page = "Revenue rose — from “$2.10M” to **$2.30M**,\n  up 14%."
    numbers = [
        num("a", "2.10M", quote='Revenue rose - from "$2.10M" to $2.30M, up 14%.'),
        num("b", "2.30M", quote="to $2.30M, up 14%."),
        num("t", "14%", quote="up 14%."),
    ]
    v = verdict_of(run([page], numbers, [derived("c1", "t", op("pct_change", "a", "b"))]))
    assert v["verdict"] == CONTRADICTED


def test_table_cells_ground_through_pipes_or_plain_spaces():
    for page in (
        "| North | 1,204 |\n| South | 988 |\n| Total | 2,192 |",
        "North\n1,204\nSouth\n988\nTotal\n2,192",
    ):
        numbers = [
            num("a", "1,204", quote="North | 1,204", exact="count"),
            num("b", "988", quote="South | 988", exact="count"),
            num("t", "2,192", quote="Total | 2,192", exact="count"),
        ]
        v = verdict_of(run([page], numbers, [derived("c1", "t", op("sum", "a", "b"))]))
        assert v["verdict"] == VERIFIED


# --- unverified is never an error ---------------------------------------------------------


def test_percentage_against_plain_number_is_a_unit_mismatch():
    v = quick(
        "1,356 of 4,792 is 28.3%",
        {"p": "1,356", "w": "4,792", "t": "28.3%"},
        "t",
        op("ratio", "p", "w"),
    )
    assert v["verdict"] == UNVERIFIED and v["reason"] == "unit-mismatch"


def test_division_by_a_number_that_could_be_zero():
    v = quick(
        "from 0 to 5, up 500%", {"a": "0", "b": "5", "t": "500%"}, "t", op("pct_change", "a", "b")
    )
    assert v["verdict"] == UNVERIFIED and v["reason"] == "division-by-zero"


def test_thousands_against_millions_is_a_scale_mismatch_not_an_error():
    """Rows printed in thousands, total in millions: the claim forgot the scale."""
    v = quick(
        "rows 1,204 and 3,588, total 4.792M",
        {"a": "1,204", "b": "3,588", "t": "4.792M"},
        "t",
        op("sum", "a", "b"),
    )
    assert v["verdict"] == UNVERIFIED and v["reason"] == "scale-mismatch"
    assert "factor of 1,000" in v["message"]


def test_scale_field_fixes_the_same_claim():
    text = "rows 1,204 and 3,588, total 4.792M"
    v = quick(text, {"a": "1,204", "b": "3,588", "t": "4.792M"}, "t", op("sum", "a", "b"),
              a={"scale": "1000"}, b={"scale": "1000"})  # fmt: skip
    assert v["verdict"] == VERIFIED


def test_unit_field_can_mark_a_bare_number_as_a_percentage():
    v = quick("from 41.2% to 43.7%, a gain of 2.5 points", {"a": "41.2%", "b": "43.7%", "t": "2.5"}, "t",
              op("pp_diff", "b", "a"), t={"unit": "pp"})  # fmt: skip
    assert v["verdict"] == VERIFIED


# --- exactness, hedges, round figures -----------------------------------------------------


def test_exact_total_is_contradicted_where_a_rounded_one_is_suspect():
    rows = [f"{t}" for t in ["105"] + ["106"] * 21 + ["107"] * 23]
    page = " ; ".join(f"row{i} {t}" for i, t in enumerate(rows)) + " ; total 4,812"
    refs = [f"r{i}" for i in range(len(rows))]

    def total(exact):
        numbers = [
            num(r, t, quote=f"row{i} {t}", exact=exact)
            for i, (r, t) in enumerate(zip(refs, rows, strict=True))
        ]
        numbers.append(num("t", "4,812", quote="total 4,812", exact=exact))
        return verdict_of(run([page], numbers, [derived("c1", "t", op("sum", *refs))]))["verdict"]

    assert total(None) == SUSPECT and total("count") == CONTRADICTED


@pytest.mark.parametrize(
    "printed, hedge, verdict",
    [
        (
            "14%",
            "approx",
            SUSPECT,
        ),  # about 14% allows 12.5..15.5; 9.52 is outside, the range reaches it
        ("10%", "approx", VERIFIED),  # about 10% allows 8.5..11.5
        ("9%", "over", VERIFIED),  # 9.52 > 9
        ("10%", "over", SUSPECT),  # true values near the edge could exceed 10
        ("15%", "over", CONTRADICTED),  # nothing in 4.65..14.63 exceeds 15
        ("10%", "under", VERIFIED),
        ("4%", "under", CONTRADICTED),
        ("9%", "at_least", VERIFIED),
        ("15%", "at_least", CONTRADICTED),
        ("10%", "at_most", VERIFIED),
        ("4%", "at_most", CONTRADICTED),
    ],
)
def test_hedges_reshape_what_the_claim_allows(printed, hedge, verdict):
    v = quick(
        f"from 2.1M to 2.3M, {printed}",
        {"a": "2.1M", "b": "2.3M", "t": printed},
        "t",
        op("pct_change", "a", "b"),
        hedge=hedge,
    )
    assert v["verdict"] == verdict


def test_over_is_strict_at_the_printed_point():
    v = quick(
        "1 of 2 is over 50%",
        {"p": "1", "w": "2", "t": "50%"},
        "t",
        op("pct_of", "p", "w"),
        hedge="over",
        exact={"p", "w"},
    )
    assert v["verdict"] == CONTRADICTED
    v = quick(
        "1 of 2 is at least 50%",
        {"p": "1", "w": "2", "t": "50%"},
        "t",
        op("pct_of", "p", "w"),
        hedge="at_least",
        exact={"p", "w"},
    )
    assert v["verdict"] == VERIFIED


def test_hedge_word_appears_in_the_sentence():
    v = quick(
        "from 2.1M to 2.3M, about 10%",
        {"a": "2.1M", "b": "2.3M", "t": "10%"},
        "t",
        op("pct_change", "a", "b"),
        hedge="approx",
    )
    assert v["sentence"].endswith("the document says about 10%")


def test_round_figure_is_suspect_not_contradicted():
    """ "Revenue of $2,300,000" beside a table that says 2,304,112: probably just rounded."""
    v = quick(
        "Revenue of $2,300,000. Table: 2,304,112",
        {"t": "2,300,000", "x": "2,304,112"},
        "t",
        op("eq", "x"),
    )
    assert v["verdict"] == SUSPECT
    assert "2,300,000 may be rounded to the nearest 100,000" in v["notes"][0]


def test_round_figure_marked_exact_is_contradicted():
    v = quick("Total 5,000. Rows 2,396 and 2,396", {"t": "5,000", "a": "2,396", "b": "2,396"}, "t",
              op("sum", "a", "a"), exact={"t", "a", "b"})  # fmt: skip
    assert v["verdict"] == CONTRADICTED


def test_round_figure_far_outside_even_the_wide_reading_is_contradicted():
    v = quick(
        "Revenue of $2,300,000. Table: 3,304,112",
        {"t": "2,300,000", "x": "3,304,112"},
        "t",
        op("eq", "x"),
    )
    assert v["verdict"] == CONTRADICTED


# --- eq: two prints of one quantity -------------------------------------------------------


@pytest.mark.parametrize(
    "target, other, verdict",
    [
        ("2.3M", "2,304,112", VERIFIED),
        ("2,304,112", "2.3M", VERIFIED),  # the order must not matter
        ("2.3M", "2,349,900", VERIFIED),
        ("2.3M", "2,350,001", CONTRADICTED),
        ("2,350,001", "2.3M", CONTRADICTED),
        ("14%", "15%", SUSPECT),  # 14.5 could print as either
        ("14%", "16%", CONTRADICTED),
        ("12.3", "12.34", VERIFIED),
    ],
)
def test_eq_is_symmetric(target, other, verdict):
    v = quick(f"summary {target} ; table {other}", {"t": target, "x": other}, "t", op("eq", "x"))
    assert v["verdict"] == verdict


def test_eq_with_two_arguments_names_the_target_first():
    v = quick(
        "summary 2.3M ; table 2,304,112", {"t": "2.3M", "x": "2,304,112"}, "t", op("eq", "t", "x")
    )
    assert v["verdict"] == VERIFIED
    assert v["sentence"] == "printed as 2,304,112 elsewhere; the document says 2.3M"


# --- rank, constants ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "item, position, verdict",
    [("c", "1", VERIFIED), ("a", "1", CONTRADICTED), ("d", "2", VERIFIED), ("b", "-1", VERIFIED)],
)
def test_rank_claims_need_no_printed_target(item, position, verdict):
    numbers = {"a": "1,204", "b": "988", "c": "1,356", "d": "1,244"}
    others = [k for k in numbers if k != item]
    text = "North 1,204 South 988 East 1,356 West 1,244"
    entries = [num(k, t, quote=text, exact="count") for k, t in numbers.items()]
    claim = derived("c1", None, op("rank", item, *others, const(position)))
    assert verdict_of(run([text], entries, [claim]))["verdict"] == verdict


def test_rank_between_rounded_neighbours_is_suspect():
    text = "A 2.1M B 2.1M C 1.0M"
    entries = [
        num("a", "2.1M", quote="A 2.1M"),
        num("b", "2.1M", quote="B 2.1M"),
        num("c", "1.0M", quote="C 1.0M"),
    ]
    v = verdict_of(
        run([text], entries, [derived("c1", None, op("rank", "a", "b", "c", const("2")))])
    )
    assert v["verdict"] == SUSPECT


def test_constants_can_be_percentages():
    v = quick(
        "East 28.3%, everyone else 71.7%",
        {"e": "28.3%", "t": "71.7%"},
        "t",
        op("diff", const("100%"), "e"),
    )
    assert v["verdict"] == VERIFIED


def test_mean_and_cagr_end_to_end():
    v = quick(
        "10, 20 and 60 average 30",
        {"a": "10", "b": "20", "c": "60", "t": "30"},
        "t",
        op("mean", "a", "b", "c"),
        exact={"a", "b", "c"},
    )
    assert v["verdict"] == VERIFIED
    v = quick("from 100 to 121 in 2 years is 10.0% a year", {"s": "100", "e": "121", "t": "10.0%"}, "t",
              op("cagr", "s", "e", const("2")), exact={"s", "e"})  # fmt: skip
    assert v["verdict"] == VERIFIED


# --- assurance, ambiguity, bookkeeping ----------------------------------------------------


def test_numbers_from_a_page_without_text_cannot_be_contradicted():
    numbers = [
        num("a", "2.10M", quote="from 2.10M to 2.30M"),
        num("b", "2.30M", quote="from 2.10M to 2.30M"),
        num("t", "14%", quote="up 14%"),
    ]
    doc = doc_of("", textless=(1,))
    v = verdict_of(run(None, numbers, [derived("c1", "t", op("pct_change", "a", "b"))], doc=doc))
    assert v["verdict"] == SUSPECT and v["assurance"] == "read"
    assert "image" in v["notes"][0]


def test_without_a_document_nothing_is_contradicted():
    numbers = [num("a", "2.10M"), num("b", "2.30M"), num("t", "14%")]
    data = claims_file(numbers, [derived("c1", "t", op("pct_change", "a", "b"))])
    result = check_claims(data, None)
    assert verdict_of(result)["verdict"] == SUSPECT and result["coverage"] is None
    assert "could not be grounded" in result["warnings"][0]


def test_ambiguous_number_format_is_never_reported_as_an_error():
    """1,234 is 1234 in an English document, but here it only makes sense as 1.234."""
    text = "1,234 plus 0.766 is 2.000"
    v = quick(text, {"a": "1,234", "b": "0.766", "t": "2.000"}, "t", op("sum", "a", "b"))
    assert v["verdict"] == UNVERIFIED and v["reason"] == "ambiguous-format"
    assert "1,234" in v["message"]
    fixed = quick(
        text,
        {"a": "1,234", "b": "0.766", "t": "2.000"},
        "t",
        op("sum", "a", "b"),
        a={"locale": "tr"},
    )
    assert fixed["verdict"] == VERIFIED


def test_a_consistent_reading_is_not_flagged_as_ambiguous():
    v = quick(
        "1,234 plus 766 is 2,000",
        {"a": "1,234", "b": "766", "t": "2,000"},
        "t",
        op("sum", "a", "b"),
        exact={"a", "b", "t"},
    )
    assert v["verdict"] == VERIFIED and v["notes"] == []


def test_number_can_override_the_document_locale():
    v = quick("1.234,5 plus 765,5 is 2,000", {"a": "1.234,5", "b": "765,5", "t": "2,000"}, "t", op("sum", "a", "b"),
              a={"locale": "tr"}, b={"locale": "tr"}, exact={"a", "b", "t"})  # fmt: skip
    assert v["verdict"] == VERIFIED


def test_turkish_document_end_to_end():
    text = "Gelir 2,10 milyon TL'den 2,30 milyon TL'ye çıktı, artış %14."
    numbers = [
        num(i, t, quote=text, locale="tr")
        for i, t in {"a": "2,10 milyon", "b": "2,30 milyon", "t": "%14"}.items()
    ]
    v = verdict_of(
        run([text], numbers, [derived("c1", "t", op("pct_change", "a", "b"))], locale="tr")
    )
    assert v["verdict"] == CONTRADICTED
    assert (
        v["sentence"]
        == "2,30 milyon ÷ 2,10 milyon − 1 = 9.52%; possible range 9.03%–10.02%; the document says %14"
    )


def test_numbers_without_a_claim_are_listed_not_judged():
    numbers = [num("a", "165"), num("b", "186"), num("t", "12.7%"), num("lonely", "42")]
    result = run(
        ["from 165 to 186, up 12.7%, with 42 stores"],
        numbers,
        [derived("c1", "t", op("pct_change", "a", "b"))],
    )
    assert [(n["id"], n["reason"]) for n in result["unchecked_numbers"]] == [
        ("lonely", "no-derivation")
    ]


def test_summary_counts_by_verdict_and_assurance(kestrel_claims, kestrel_doc):
    s = check_claims(kestrel_claims, kestrel_doc)["summary"]
    assert (s["contradicted"], s["suspect"], s["unverified"], s["verified"]) == (3, 1, 2, 4)
    assert s["by_assurance"]["computed"]["contradicted"] == 2
    assert s["by_assurance"]["read"] == {
        "contradicted": 1,
        "suspect": 0,
        "unverified": 0,
        "verified": 1,
    }
    assert s["by_assurance"]["resolved"]["unverified"] == 2


def test_sha_mismatch_is_a_warning(kestrel_claims, kestrel_doc):
    claims = {**kestrel_claims, "document": {**kestrel_claims["document"], "sha256": "ab" * 32}}
    assert "different version" in check_claims(claims, kestrel_doc)["warnings"][0]


def test_same_input_same_output(kestrel_claims, kestrel_doc):
    assert check_claims(kestrel_claims, kestrel_doc) == check_claims(kestrel_claims, kestrel_doc)


def test_knock_on_effect_of_a_contradicted_total_is_noted():
    """A share computed from a wrong printed total: flagged, with the likely cause named."""
    text = "North 1,204 South 3,588 Total 4,812. North is 25.1% of the total."
    entries = [
        num("a", "1,204", quote=text, exact="count"),
        num("b", "3,588", quote=text, exact="count"),
        num("t", "4,812", quote=text, exact="count"),
        num("s", "25.1%", quote=text),
    ]
    claims = [derived("c1", "t", op("sum", "a", "b")), derived("c2", "s", op("pct_of", "a", "t"))]
    result = run([text], entries, claims)
    share = verdict_of(result, "c2")
    assert (
        verdict_of(result, "c1")["verdict"] == CONTRADICTED
        and verdict_of(result, "c1")["notes"] == []
    )
    assert share["verdict"] == CONTRADICTED
    assert "uses 4,812, which claim c1 contradicts" in share["notes"][0]


def test_a_target_of_zero_is_not_mistaken_for_a_scale_mix_up():
    v = quick(
        "120 minus 100 leaves 0",
        {"a": "120", "b": "100", "t": "0"},
        "t",
        op("diff", "a", "b"),
        exact={"a", "b", "t"},
    )
    assert v["verdict"] == CONTRADICTED
    v = quick(
        "120 minus 120 leaves 0",
        {"a": "120", "t": "0"},
        "t",
        op("diff", "a", "a"),
        exact={"a", "t"},
    )
    assert v["verdict"] == VERIFIED
