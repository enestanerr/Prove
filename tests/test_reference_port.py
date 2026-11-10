"""The ten cases of reference/test_reference.py, run through the product code.

The reference is a specification by example. These must stay 10/10.
"""

from fractions import Fraction as F

from helpers import derived, doc_of, num, op, quick, run, verdict_of

from provecheck import CONTRADICTED, SUSPECT, VERIFIED
from provecheck.numbers import parse_printed


def test_01_one_decimal_operands_are_only_suspect():
    v = quick(
        "from 2.1M to 2.3M, up 14%",
        {"a": "2.1M", "b": "2.3M", "t": "14%"},
        "t",
        op("pct_change", "a", "b"),
    )
    assert v["verdict"] == SUSPECT
    assert v["display"] == {"point": "9.52%", "range": "4.65%–14.63%", "printed": "14%"}


def test_02_two_decimal_operands_leave_no_room():
    v = quick(
        "from 2.10M to 2.30M, up 14%",
        {"a": "2.10M", "b": "2.30M", "t": "14%"},
        "t",
        op("pct_change", "a", "b"),
    )
    assert v["verdict"] == CONTRADICTED
    assert v["display"]["range"] == "9.03%–10.02%"


def test_03_correct_claim_is_verified():
    v = quick(
        "from 165 to 186, up 12.7%",
        {"a": "165", "b": "186", "t": "12.7%"},
        "t",
        op("pct_change", "a", "b"),
    )
    assert v["verdict"] == VERIFIED
    assert v["display"]["point"] == "12.73%"


def test_04_exact_rows_do_not_sum_to_the_total():
    rows = {"a": "1,204", "b": "988", "c": "1,356", "d": "1,244", "t": "4,812"}
    text = "North 1,204 South 988 East 1,356 West 1,244 Total 4,812"
    v = quick(text, rows, "t", op("sum", "a", "b", "c", "d"), exact=set(rows))
    assert v["verdict"] == CONTRADICTED and v["point"] == "4792" and v["display"]["range"] is None


def _rows(texts: list[str], total: str):
    page = " ; ".join(f"row{i} {t}" for i, t in enumerate(texts)) + f" ; total {total}"
    numbers = [num(f"r{i}", t, quote=f"row{i} {t}") for i, t in enumerate(texts)]
    numbers.append(num("t", total, quote=f"total {total}"))
    claim = derived("c1", "t", op("sum", *[f"r{i}" for i in range(len(texts))]))
    return verdict_of(run([page], numbers, [claim]))


def test_05_twenty_rounded_rows_cannot_drift_by_twenty():
    v = _rows(["240"] * 19 + ["232"], "4,812")
    assert v["verdict"] == CONTRADICTED and v["range"] == ["4782", "4802"]


def test_06_forty_five_rounded_rows_can():
    v = _rows(["105"] + ["106"] * 21 + ["107"] * 23, "4,812")
    assert v["verdict"] == SUSPECT and v["point"] == "4792" and v["range"] == ["9539/2", "9629/2"]


def test_07_three_rounded_shares_make_a_hundred_percent():
    text = "A 33.3% B 33.3% C 33.3% total 100%"
    numbers = [num(i, "33.3%", quote=f"{i} 33.3%") for i in "ABC"] + [
        num("t", "100%", quote="total 100%")
    ]
    v = verdict_of(run([text], numbers, [derived("c1", "t", op("sum", "A", "B", "C"))]))
    assert v["verdict"] == VERIFIED and v["point"] == "999/10"


def test_08_share_of_total():
    v = quick(
        "1,356 of 4,792 is 28.3%",
        {"p": "1,356", "w": "4,792", "t": "28.3%"},
        "t",
        op("pct_of", "p", "w"),
        exact={"p", "w"},
    )
    assert v["verdict"] == VERIFIED and v["display"]["point"] == "28.30%"


def test_09_turkish_format_equals_english_format():
    assert (
        parse_printed("1.234,5", "eu").point == parse_printed("1,234.5", "en").point == F(12345, 10)
    )


def test_10_chart_label_against_two_readings_of_the_bar():
    chart = {
        "id": "g1", "loc": {"page": 1, "figure": "Figure 1"}, "type": "bar",
        "y_axis": {"min": "0", "max": "400", "scale": "linear"},
        "marks": [{"label": "Q3", "read_a": {"lo": "300", "hi": "320"}, "read_b": {"lo": "300", "hi": "320"}}],
    }  # fmt: skip
    claim = {"id": "c1", "kind": "chart", "check": "label_vs_mark", "target": "t", "chart": "g1",
             "mark": {"label": "Q3"}, "say": "The label should match the bar."}  # fmt: skip
    result = run(
        None, [num("t", "350", quote="350")], [claim], charts=[chart], doc=doc_of("label 350")
    )
    assert verdict_of(result)["verdict"] == CONTRADICTED
    assert verdict_of(result)["assurance"] == "read"
