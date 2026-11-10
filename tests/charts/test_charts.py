"""Chart checks (SPEC §8): two reads, minimum width, the five checks."""

from fractions import Fraction as F

import pytest
from helpers import num, run, verdict_of

from provecheck import CONTRADICTED, SUSPECT, UNVERIFIED, VERIFIED
from provecheck.charts import Axis, compare, order, read_mark, scale_confusion, total
from provecheck.intervals import Interval, Target


def reading(lo, hi):
    return {"lo": str(lo), "hi": str(hi)}


def mark(label, a, b=None, series=None, printed_label=None):
    out = {"label": label, "read_a": reading(*a), "read_b": reading(*b) if b else None}
    if series:
        out["series"] = series
    if printed_label:
        out["printed_label"] = printed_label
    return out


def chart(marks, axis=(0, 400), scale="linear", kind="bar", **extra):
    out = {"id": "g1", "loc": {"page": 1, "figure": "Figure 1"}, "type": kind, "marks": marks}
    if axis is not None:
        out["y_axis"] = {"min": str(axis[0]), "max": str(axis[1]), "scale": scale, **extra}
    return out


def claim(check, target="t", **extra):
    out = {"id": "c1", "kind": "chart", "check": check, "chart": "g1", "say": "A chart check."}
    if target:
        out["target"] = target
    out.update(extra)
    return out


def judge(printed, the_chart, the_claim=None, page=None, **number_extra):
    """One printed number in the text, one chart, one claim -> the verdict record."""
    page = page or f"The figure is {printed} here."
    numbers = [num("t", printed, quote=page, **number_extra)] if printed else []
    the_claim = the_claim or claim("text_vs_chart", mark={"label": "Q3"})
    return verdict_of(run([page], numbers, [the_claim], charts=[the_chart]))


Q3 = [mark("Q3", (300, 320), (302, 318))]

# --- the two-read protocol ----------------------------------------------------------------


def test_axis_defaults():
    assert Axis.of(chart(Q3)) == Axis(F(0), F(400))
    assert Axis.of(chart(Q3, scale="log", axis=(1, 1000))).log is True
    assert Axis.of(chart(Q3, kind="pie", axis=None)) == Axis(F(0), F(100))
    assert Axis.of(chart(Q3, multiplier="1000")).multiplier == 1000


def test_final_reading_is_the_union_of_both_reads():
    r = read_mark(mark("Q3", (300, 312), (308, 320)), Axis(F(0), F(400)))
    assert r.status == "ok" and r.final == Interval(F(300), F(320))


def test_reads_that_do_not_overlap_are_unstable():
    r = read_mark(mark("Q3", (300, 310), (311, 320)), Axis(F(0), F(400)))
    assert r.status == "unstable" and r.final is None


def test_reads_that_touch_are_stable():
    assert read_mark(mark("Q3", (300, 310), (310, 320)), Axis(F(0), F(400))).status == "ok"


def test_a_single_read_is_not_enough():
    r = read_mark(mark("Q3", (300, 320)), Axis(F(0), F(400)))
    assert r.status == "single-read" and r.final is None


@pytest.mark.parametrize(
    "a, b, axis, expected",
    [
        ((310, 310), (310, 310), (0, 400), (306, 314)),  # a point becomes 2% of 400 = 8 wide
        ((309, 311), (309, 311), (0, 400), (306, 314)),  # 2 wide becomes 8 wide, same centre
        ((300, 320), (302, 318), (0, 400), (300, 320)),  # already wide enough
        ((50, 50), (50, 50), (0, 100), (49, 51)),
        ((490, 490), (490, 490), (400, 550), (F(977, 2), F(983, 2))),  # span 150 -> 3 wide
    ],
)
def test_minimum_width_is_two_percent_of_the_axis_span(a, b, axis, expected):
    r = read_mark(mark("Q3", a, b), Axis(F(axis[0]), F(axis[1])))
    assert r.final == Interval(F(expected[0]), F(expected[1]))


def test_minimum_width_on_a_log_axis_is_measured_in_log_space():
    axis = Axis(F(1), F(10000), log=True)
    r = read_mark(mark("Q3", (100, 100), (100, 100)), axis)
    ratio = float(r.final.hi / r.final.lo)
    assert abs(ratio - 10000**0.02) < 1e-9  # hi/lo spans 2% of four decades
    assert r.final.lo < 100 < r.final.hi
    wide = read_mark(mark("Q3", (50, 200), (60, 180)), axis)
    assert wide.final == Interval(F(50), F(200))  # already wider than 2% in log space


def test_multiplier_converts_axis_units_to_base_units():
    r = read_mark(mark("Q3", (300, 320), (302, 318)), Axis(F(0), F(400), multiplier=F(1000)))
    assert r.final == Interval(F(300000), F(320000))


def test_compare_total_and_order_helpers():
    bar = Interval(F(300), F(320))
    assert compare(Target.of(Interval(F(319), F(321))), bar) == VERIFIED
    assert compare(Target.of(Interval(F(349), F(351))), bar) == CONTRADICTED
    assert total([Interval(F(1), F(2)), Interval(F(3), F(5))]) == Interval(F(4), F(7))
    others = [Interval(F(200), F(220)), Interval(F(310), F(330))]
    assert order("largest", bar, others) == VERIFIED  # 310-330 might be larger, might not
    assert order("largest", bar, [Interval(F(321), F(340))]) == CONTRADICTED
    assert order("smallest", bar, [Interval(F(200), F(220))]) == CONTRADICTED
    assert order("lt", bar, [Interval(F(400), F(420))]) == VERIFIED


def test_scale_confusion_detects_unit_mixups_only():
    target = Target.of(Interval(F(349500), F(350500)))
    assert scale_confusion(target, Interval(F(340), F(360))) == 1000
    assert scale_confusion(target, Interval(F(300), F(320))) is None
    assert (
        scale_confusion(
            Target.of(Interval(F(445, 10), F(455, 10))), Interval(F(44, 100), F(46, 100))
        )
        is None
    )
    share = Target.of(Interval(F(445, 10), F(455, 10)))
    assert scale_confusion(share, Interval(F(44, 100), F(46, 100)), percent=True) == 100
    assert scale_confusion(target, Interval(F(0), F(8))) is None  # touches zero


# --- value checks -------------------------------------------------------------------------


@pytest.mark.parametrize("check", ["label_vs_mark", "text_vs_chart", "table_vs_chart"])
def test_value_checks_share_one_rule(check):
    assert judge("350", chart(Q3), claim(check, mark={"label": "Q3"}))["verdict"] == CONTRADICTED
    assert judge("310", chart(Q3), claim(check, mark={"label": "Q3"}))["verdict"] == VERIFIED


def test_chart_verdicts_are_tagged_read_and_show_both_readings():
    v = judge("350", chart(Q3))
    assert v["assurance"] == "read"
    assert v["sentence"] == (
        "the Q3 bar in Figure 1 reads 300–320 (first reading 300–320, second reading 302–318); "
        "the document says 350"
    )
    assert v["marks"][0] == {
        "label": "Q3", "series": None, "status": "ok",
        "read_a": "300–320", "read_b": "302–318", "final": "300–320",
    }  # fmt: skip


# A planted mismatch of 10% of the axis span or more must be caught. Readings are honest:
# they contain the true value and are 4% of the span wide.
AXES = [(0, 100), (0, 400), (400, 550), (0, 1), (1000, 5000), (-50, 50)]
SHIFTS = [F(10, 100), F(15, 100), F(25, 100), F(-10, 100), F(-25, 100)]


def _honest(axis, where=F(61, 100)):
    span = F(axis[1] - axis[0])
    true = axis[0] + span * where
    a = (true - span * F(2, 100), true + span * F(2, 100))
    b = (true - span * F(1, 100), true + span * F(1, 100))
    return true, span, [mark("Q3", tuple(map(float, a)), tuple(map(float, b)))]


def _print(value: F, span: F) -> str:
    places = 0 if span >= 50 else 2
    return f"{float(value):.{places}f}"


@pytest.mark.parametrize("axis", AXES)
@pytest.mark.parametrize("shift", SHIFTS)
def test_planted_mismatch_of_ten_percent_of_span_is_contradicted(axis, shift):
    true, span, marks = _honest(axis)
    printed = _print(true + span * shift, span)
    assert judge(printed, chart(marks, axis=axis))["verdict"] == CONTRADICTED


@pytest.mark.parametrize("axis", AXES)
def test_a_clean_chart_is_never_contradicted(axis):
    true, span, marks = _honest(axis)
    assert judge(_print(true, span), chart(marks, axis=axis))["verdict"] == VERIFIED


@pytest.mark.parametrize("axis", AXES)
def test_a_printed_number_at_the_edge_of_the_reading_is_not_contradicted(axis):
    true, span, marks = _honest(axis)
    printed = _print(true + span * F(2, 100), span)
    assert judge(printed, chart(marks, axis=axis))["verdict"] == VERIFIED


def test_unstable_reading_ends_unverified():
    v = judge("350", chart([mark("Q3", (300, 310), (330, 340))]))
    assert v["verdict"] == UNVERIFIED and v["reason"] == "unstable-reading"
    assert "'Q3'" in v["message"]


def test_single_reading_ends_unverified():
    v = judge("350", chart([mark("Q3", (300, 320))]))
    assert v["verdict"] == UNVERIFIED and v["reason"] == "single-read"


def test_ungrounded_printed_number_ends_unverified():
    page = "The figure is 350 here."
    numbers = [num("t", "360", quote=page)]
    the_claim = claim("text_vs_chart", mark={"label": "Q3"})
    v = verdict_of(run([page], numbers, [the_claim], charts=[chart(Q3)]))
    assert v["verdict"] == UNVERIFIED and v["reason"] == "not-grounded"


def test_thousands_axis_against_a_full_number_is_a_scale_mismatch():
    v = judge("310,000", chart(Q3))
    assert v["verdict"] == UNVERIFIED and v["reason"] == "scale-mismatch"
    assert "factor of 1,000" in v["message"]


def test_multiplier_makes_the_same_comparison_work():
    assert judge("310,000", chart(Q3, multiplier="1000"))["verdict"] == VERIFIED
    assert judge("350,000", chart(Q3, multiplier="1000"))["verdict"] == CONTRADICTED


def test_share_axis_against_a_percentage_is_a_scale_mismatch():
    marks = [mark("Q3", (0.44, 0.46), (0.44, 0.46))]
    v = judge("45%", chart(marks, axis=(0, 1)))
    assert v["verdict"] == UNVERIFIED and v["reason"] == "scale-mismatch"


def test_round_figure_in_the_text_is_suspect_not_contradicted():
    """ "About 300" style round numbers: 300 may stand for anything from 250 to 350."""
    v = judge("300", chart([mark("Q3", (318, 330), (320, 328))]))
    assert v["verdict"] == SUSPECT and "nearest 100" in v["notes"][0]
    assert judge("300", chart([mark("Q3", (360, 380), (362, 378))]))["verdict"] == CONTRADICTED


@pytest.mark.parametrize("hedge, printed, verdict", [("approx", "330", VERIFIED), ("over", "300", VERIFIED), ("over", "330", CONTRADICTED), ("at_most", "290", CONTRADICTED)])  # fmt: skip
def test_hedges_apply_to_chart_claims(hedge, printed, verdict):
    the_claim = claim("text_vs_chart", mark={"label": "Q3"}, hedge=hedge)
    assert judge(printed, chart(Q3), the_claim)["verdict"] == verdict


def test_value_label_inside_the_figure_is_read_not_grounded():
    page = "Figure 1 shows spend by quarter."
    label = num("t", "350", quote="350")
    label["loc"]["image"] = True
    the_claim = claim("label_vs_mark", mark={"label": "Q3"})
    v = verdict_of(run([page], [label], [the_claim], charts=[chart(Q3)]))
    assert v["verdict"] == CONTRADICTED and v["assurance"] == "read"


def test_log_axis_reading():
    marks = [mark("Q3", (800, 1200), (900, 1100))]
    assert judge("1,000", chart(marks, axis=(1, 100000), scale="log"))["verdict"] == VERIFIED
    assert judge("5,000", chart(marks, axis=(1, 100000), scale="log"))["verdict"] == CONTRADICTED


def test_series_selects_the_right_mark():
    marks = [
        mark("Q3", (300, 320), (302, 318), series="Revenue"),
        mark("Q3", (100, 120), (102, 118), series="Cost"),
    ]
    rev = claim("text_vs_chart", mark={"label": "Q3", "series": "Revenue"})
    cost = claim("text_vs_chart", mark={"label": "Q3", "series": "Cost"})
    assert judge("310", chart(marks, kind="grouped_bar"), rev)["verdict"] == VERIFIED
    assert judge("310", chart(marks, kind="grouped_bar"), cost)["verdict"] == CONTRADICTED


# --- parts_sum ----------------------------------------------------------------------------

PIE = [mark("A", (39, 43), (40, 42)), mark("B", (25, 29), (26, 28)), mark("C", (30, 34), (31, 33))]


def test_pie_slices_add_up_to_the_stated_whole():
    v = judge("100%", chart(PIE, kind="pie", axis=None), claim("parts_sum"))
    assert v["verdict"] == VERIFIED
    assert v["sentence"] == "the 3 slices in Figure 1 add up to 94–106; the document says 100%"


def test_pie_slices_that_cannot_reach_the_stated_whole():
    small = [
        mark("A", (30, 34), (31, 33)),
        mark("B", (25, 29), (26, 28)),
        mark("C", (20, 24), (21, 23)),
    ]
    v = judge("100%", chart(small, kind="pie", axis=None), claim("parts_sum"))
    assert v["verdict"] == CONTRADICTED


def test_parts_sum_can_name_its_marks():
    the_claim = claim("parts_sum", marks=[{"label": "A"}, {"label": "B"}])
    assert judge("68", chart(PIE, kind="pie", axis=None), the_claim)["verdict"] == VERIFIED
    assert judge("90", chart(PIE, kind="pie", axis=None), the_claim)["verdict"] == CONTRADICTED


def test_stacked_segments_against_their_total():
    segments = [
        mark("Q3", (118, 126), (120, 124), series="Online"),
        mark("Q3", (76, 84), (78, 82), series="Stores"),
    ]
    v = judge("200", chart(segments, kind="stacked_bar"), claim("parts_sum"))
    assert v["verdict"] == VERIFIED and "2 segments" in v["sentence"]
    assert (
        judge("260", chart(segments, kind="stacked_bar"), claim("parts_sum"))["verdict"]
        == CONTRADICTED
    )


def test_parts_sum_with_one_unstable_slice_is_unverified():
    bad = [*PIE[:2], mark("C", (30, 32), (36, 38))]
    v = judge("100%", chart(bad, kind="pie", axis=None), claim("parts_sum"))
    assert v["verdict"] == UNVERIFIED and v["reason"] == "unstable-reading"


# --- order --------------------------------------------------------------------------------

BARS = [
    mark("Q1", (230, 250), (235, 245)),
    mark("Q2", (265, 285), (270, 280)),
    mark("Q3", (300, 320), (302, 318)),
]


@pytest.mark.parametrize(
    "label, relation, verdict",
    [
        ("Q3", "largest", VERIFIED),
        ("Q1", "largest", CONTRADICTED),
        ("Q1", "smallest", VERIFIED),
        ("Q3", "smallest", CONTRADICTED),
    ],
)
def test_order_largest_and_smallest(label, relation, verdict):
    the_claim = claim("order", target=None, mark={"label": label}, relation=relation)
    assert judge(None, chart(BARS), the_claim, page="No numbers.")["verdict"] == verdict


@pytest.mark.parametrize(
    "a, relation, b, verdict",
    [("Q3", "gt", "Q1", VERIFIED), ("Q1", "gt", "Q3", CONTRADICTED), ("Q1", "lt", "Q2", VERIFIED), ("Q3", "lt", "Q2", CONTRADICTED)],
)  # fmt: skip
def test_order_between_two_marks(a, relation, b, verdict):
    the_claim = claim("order", target=None, mark={"label": a}, relation=relation, than={"label": b})
    v = judge(None, chart(BARS), the_claim, page="No numbers.")
    assert v["verdict"] == verdict
    assert f"{a} bar in Figure 1 reads" in v["sentence"]


def test_order_too_close_to_call_is_not_contradicted():
    close = [mark("Q2", (300, 320), (302, 318)), mark("Q3", (305, 325), (307, 323))]
    the_claim = claim("order", target=None, mark={"label": "Q2"}, relation="largest")
    assert judge(None, chart(close), the_claim, page="No numbers.")["verdict"] == VERIFIED


def test_order_is_judged_within_one_series():
    marks = [
        mark("Q2", (100, 120), (102, 118), series="Cost"),
        mark("Q3", (130, 150), (132, 148), series="Cost"),
        mark("Q3", (300, 320), (302, 318), series="Revenue"),
    ]
    the_claim = claim(
        "order", target=None, mark={"label": "Q3", "series": "Cost"}, relation="largest"
    )
    v = judge(None, chart(marks, kind="grouped_bar"), the_claim, page="No numbers.")
    assert v["verdict"] == VERIFIED and len(v["marks"]) == 2


def test_order_with_an_unstable_neighbour_is_unverified():
    marks = [mark("Q2", (200, 210), (240, 250)), mark("Q3", (300, 320), (302, 318))]
    the_claim = claim("order", target=None, mark={"label": "Q3"}, relation="largest")
    assert judge(None, chart(marks), the_claim, page="No numbers.")["verdict"] == UNVERIFIED


def test_chart_notes_are_carried_to_the_record_not_turned_into_verdicts():
    with_note = {**chart(Q3, axis=(250, 400)), "notes": ["The bar axis starts at 250, not zero."]}
    v = judge("310", with_note)
    assert v["verdict"] == VERIFIED and v["chart"]["notes"] == [
        "The bar axis starts at 250, not zero."
    ]
