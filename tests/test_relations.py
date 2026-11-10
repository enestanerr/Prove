from fractions import Fraction as F

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from provecheck.intervals import Interval
from provecheck.numbers import PERCENT, PLAIN, parse_printed
from provecheck.relations import REGISTRY, RelationError, Value, get


def val(text: str, exact: bool = False) -> Value:
    p = parse_printed(text)
    return Value(p.point, p.interval(exact), p.kind)


def call(name: str, *texts: str, exact: bool = False) -> Value:
    return get(name)([val(t, exact) for t in texts])


def test_every_spec_relation_is_registered():
    spec = {
        "eq",
        "sum",
        "diff",
        "product",
        "ratio",
        "pct_of",
        "pct_change",
        "pp_diff",
        "mean",
        "cagr",
        "max",
        "min",
        "rank",
    }
    assert spec <= set(REGISTRY)


def test_unknown_op_names_the_known_ones():
    with pytest.raises(RelationError) as exc:
        get("average")
    assert "mean" in str(exc.value) and exc.value.reason == "unknown-op"


@pytest.mark.parametrize(
    "name, texts, point",
    [
        ("eq", ["4,812"], F(4812)),
        ("sum", ["1,204", "988", "1,356", "1,244"], F(4792)),
        ("diff", ["2.3M", "2.1M"], F(200000)),
        ("product", ["12", "2.5"], F(30)),
        ("product", ["20%", "500"], F(100)),
        ("product", ["50%", "50%"], F(25)),
        ("ratio", ["186", "62"], F(3)),
        ("ratio", ["100", "20%"], F(500)),
        ("pct_of", ["1,356", "4,792"], F(135600, 4792)),
        ("pct_change", ["165", "186"], F(2100, 165)),
        ("pct_change", ["200", "150"], F(-25)),
        ("pp_diff", ["43.7%", "41.2%"], F(25, 10)),
        ("mean", ["10", "20", "60"], F(30)),
        ("max", ["3", "9", "4"], F(9)),
        ("min", ["3", "9", "4"], F(3)),
    ],
)
def test_point_values(name, texts, point):
    assert call(name, *texts).point == point


@pytest.mark.parametrize(
    "name, texts, kind",
    [
        ("sum", ["33.3%", "33.3%"], PERCENT),
        ("sum", ["1", "2"], PLAIN),
        ("pct_of", ["1", "2"], PERCENT),
        ("pct_change", ["1", "2"], PERCENT),
        ("pp_diff", ["5%", "3%"], PERCENT),
        ("ratio", ["30%", "15%"], PLAIN),
        ("product", ["20%", "500"], PLAIN),
        ("product", ["50%", "50%"], PERCENT),
        ("mean", ["4%", "6%"], PERCENT),
        ("cagr", ["100", "121", "2"], PERCENT),
    ],
)
def test_result_kind(name, texts, kind):
    assert call(name, *texts).kind == kind


def test_pct_change_range_matches_the_spec_example():
    v = call("pct_change", "2.1M", "2.3M")
    assert round(float(v.range.lo), 2) == 4.65 and round(float(v.range.hi), 2) == 14.63
    v = call("pct_change", "2.10M", "2.30M")
    assert round(float(v.range.lo), 2) == 9.03 and round(float(v.range.hi), 2) == 10.02


@pytest.mark.parametrize(
    "name, texts",
    [
        ("sum", ["14%", "3M"]),
        ("diff", ["14%", "3"]),
        ("mean", ["14%", "3"]),
        ("max", ["14%", "3"]),
        ("pct_of", ["14%", "3"]),
        ("pct_change", ["14%", "3"]),
        ("pp_diff", ["14", "3%"]),
        ("pp_diff", ["14", "3"]),
    ],
)
def test_mixing_percentages_and_plain_numbers_is_a_unit_mismatch(name, texts):
    with pytest.raises(RelationError) as exc:
        call(name, *texts)
    assert exc.value.reason == "unit-mismatch"


@pytest.mark.parametrize(
    "name, texts",
    [
        ("ratio", ["5", "0"]),
        ("pct_of", ["5", "0"]),
        ("pct_change", ["0", "5"]),
        ("ratio", ["5", "0.4"]),
    ],
)
def test_divisor_that_could_be_zero(name, texts):
    """0.4 rounds from anything in [0.35, 0.45] - fine. 0 rounds from [-0.5, 0.5] - not fine."""
    if texts[-1] == "0.4":
        assert call(name, *texts).point == F(25, 2)
        return
    with pytest.raises(RelationError) as exc:
        call(name, *texts)
    assert exc.value.reason == "division-by-zero"


def test_cagr_matches_a_hand_computation():
    v = call("cagr", "100", "121", "2", exact=True)
    assert abs(v.point - 10) < F(1, 10**30)
    assert v.range.contains(v.point) and v.range.width < F(1, 10**30)


def test_cagr_range_covers_rounding_of_operands():
    v = get("cagr")([val("2.1M"), val("2.3M"), Value.exact(3)])
    lo = ((2.25 / 2.15) ** (1 / 3) - 1) * 100
    hi = ((2.35 / 2.05) ** (1 / 3) - 1) * 100
    assert abs(float(v.range.lo) - lo) < 1e-9 and abs(float(v.range.hi) - hi) < 1e-9


@pytest.mark.parametrize("texts", [["0", "5", "2"], ["-3", "5", "2"], ["4", "5", "0"]])
def test_cagr_rejects_values_it_cannot_take_a_root_of(texts):
    with pytest.raises(RelationError):
        call("cagr", *texts, exact=True)


def rank(item, others, position):
    args = [val(item, True), *[val(o, True) for o in others], Value.exact(position)]
    return get("rank")(args)


@pytest.mark.parametrize(
    "item, others, position, point",
    [
        ("1,356", ["1,204", "988", "1,244"], 1, 1),
        ("988", ["1,204", "1,356", "1,244"], 1, 4),
        ("1,244", ["1,204", "988", "1,356"], 2, 2),
        ("988", ["1,204", "1,356", "1,244"], -1, -1),
        ("1,204", ["988", "1,356", "1,244"], -2, -2),
        ("5", ["5", "3"], 1, 1),  # a tie for first is still first
    ],
)
def test_rank(item, others, position, point):
    assert rank(item, others, position).point == point


def test_rank_range_reflects_rounding():
    args = [val("2.1M"), val("2.1M"), val("1.0M"), Value.exact(1)]
    v = get("rank")(args)
    assert v.point == 1 and v.range == Interval(F(1), F(2))  # the other 2.1M could be larger


@pytest.mark.parametrize("position", [0, 5, F(3, 2)])
def test_rank_position_must_be_a_usable_whole_number(position):
    with pytest.raises(RelationError):
        rank("5", ["4", "3"], position)


@pytest.mark.parametrize(
    "name, parts, text",
    [
        ("pct_change", ["2.10M", "2.30M"], "2.30M ÷ 2.10M − 1"),
        ("sum", ["1", "2", "3"], "1 + 2 + 3"),
        ("pct_of", ["1,356", "4,792"], "1,356 ÷ 4,792"),
        ("mean", ["1", "2"], "(1 + 2) ÷ 2"),
        ("diff", ["5", "3"], "5 − 3"),
        ("max", ["5", "3"], "max(5, 3)"),
        ("rank", ["9", "5", "3", "1"], "place of 9 among 3 values"),
        ("sum", [str(i) for i in range(12)], "0 + 1 + 2 + … + 10 + 11 (12 values)"),
    ],
)
def test_explain(name, parts, text):
    assert get(name).explain(parts) == text


# --- properties from docs/ARCHITECTURE.md -------------------------------------------------

RATIONAL = ["sum", "diff", "product", "ratio", "pct_of", "pct_change", "mean", "max", "min"]
positive = st.fractions(min_value=F(1, 100), max_value=10**6, max_denominator=1000)


@st.composite
def operand(draw):
    point = draw(positive)
    half = point * draw(st.fractions(min_value=0, max_value=F(1, 4), max_denominator=100))
    return Value(point, Interval(point - half, point + half))


def args_for(name: str, values: list[Value]) -> list[Value]:
    rel = REGISTRY[name]
    return values[: rel.max_args] if rel.max_args else values


@pytest.mark.parametrize("name", RATIONAL)
@given(st.lists(operand(), min_size=2, max_size=5))
def test_the_point_is_always_inside_the_range(name, values):
    out = get(name)(args_for(name, values))
    assert out.range.contains(out.point)


@pytest.mark.parametrize("name", RATIONAL)
@given(st.lists(operand(), min_size=2, max_size=5), st.fractions(min_value=0, max_value=F(1, 200)))
def test_widening_an_operand_never_shrinks_the_range(name, values, extra):
    args = args_for(name, values)
    assume(all(a.range.lo - extra > 0 for a in args))
    narrow = get(name)(args)
    wider = [Value(args[0].point, args[0].range.widen(extra)), *args[1:]]
    assert get(name)(wider).range.contains_interval(narrow.range)


@pytest.mark.parametrize("name", RATIONAL)
@given(st.lists(positive, min_size=2, max_size=5))
def test_exact_operands_give_a_zero_width_range(name, points):
    out = get(name)(args_for(name, [Value.exact(p) for p in points]))
    assert out.range.is_point and out.range.lo == out.point


@given(operand(), operand(), st.integers(min_value=1, max_value=30))
def test_cagr_point_is_inside_its_range(start, end, years):
    out = get("cagr")([start, end, Value.exact(years)])
    assert out.range.contains(out.point)
