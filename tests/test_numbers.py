from fractions import Fraction as F

import pytest
from hypothesis import given
from hypothesis import strategies as st

from provecheck.intervals import Interval
from provecheck.numbers import (
    PERCENT,
    PLAIN,
    NumberParseError,
    normalize_locale,
    parse_const,
    parse_decimal,
    parse_printed,
    parse_scale,
)

# text, locale, point, decimals, kind
PARSE_CASES = [
    ("2.1M", "en", F(2100000), 1, PLAIN),
    ("2.10M", "en", F(2100000), 2, PLAIN),
    ("$2.30M", "en", F(2300000), 2, PLAIN),
    ("4,812", "en", F(4812), 0, PLAIN),
    ("1,234.5", "en", F(12345, 10), 1, PLAIN),
    ("1,234,567", "en", F(1234567), 0, PLAIN),
    ("14%", "en", F(14), 0, PERCENT),
    ("12.7%", "en", F(127, 10), 1, PERCENT),
    ("14 %", "en", F(14), 0, PERCENT),
    ("14 percent", "en", F(14), 0, PERCENT),
    ("5 pp", "en", F(5), 0, PERCENT),
    ("350k", "en", F(350000), 0, PLAIN),
    ("350K", "en", F(350000), 0, PLAIN),
    ("3.2bn", "en", F(3200000000), 1, PLAIN),
    ("3.2B", "en", F(3200000000), 1, PLAIN),
    ("£2.1m", "en", F(2100000), 1, PLAIN),
    ("4.5 million", "en", F(4500000), 1, PLAIN),
    ("7 billion", "en", F(7 * 10**9), 0, PLAIN),
    ("1.5 trillion", "en", F(15 * 10**11), 1, PLAIN),
    ("12 thousand", "en", F(12000), 0, PLAIN),
    ("USD 250", "en", F(250), 0, PLAIN),
    ("250 USD", "en", F(250), 0, PLAIN),
    ("€99.50", "en", F(995, 10), 2, PLAIN),
    ("-5%", "en", F(-5), 0, PERCENT),
    ("−5%", "en", F(-5), 0, PERCENT),  # U+2212 minus
    ("+3.2%", "en", F(32, 10), 1, PERCENT),
    ("(1,234)", "en", F(-1234), 0, PLAIN),  # accounting negative
    ("-$40", "en", F(-40), 0, PLAIN),
    ("~120", "en", F(120), 0, PLAIN),
    ("0.05", "en", F(5, 100), 2, PLAIN),
    ("007", "en", F(7), 0, PLAIN),
    ("1 234 567", "en", F(1234567), 0, PLAIN),  # space groups
    ("1 234", "en", F(1234), 0, PLAIN),  # no-break space
    ("1'234", "en", F(1234), 0, PLAIN),  # Swiss apostrophe
    # European / Turkish formats
    ("1.234,5", "eu", F(12345, 10), 1, PLAIN),
    ("1.234.567", "eu", F(1234567), 0, PLAIN),
    ("2,1 milyon", "tr", F(2100000), 1, PLAIN),
    ("3,5 milyar", "tr", F(35 * 10**8), 1, PLAIN),
    ("12 bin", "tr", F(12000), 0, PLAIN),
    ("%14", "tr", F(14), 0, PERCENT),
    ("% 14", "tr", F(14), 0, PERCENT),
    ("%12,7", "tr", F(127, 10), 1, PERCENT),
    ("yüzde 14", "tr", F(14), 0, PERCENT),
    ("₺1.250,75", "tr", F(125075, 100), 2, PLAIN),
    ("1.250,75 TL", "tr", F(125075, 100), 2, PLAIN),
    ("14,5%", "de", F(145, 10), 1, PERCENT),
    ("2,5 trilyon", "tr", F(25 * 10**11), 1, PLAIN),
]


@pytest.mark.parametrize("text, locale, point, decimals, kind", PARSE_CASES)
def test_parse_printed(text, locale, point, decimals, kind):
    p = parse_printed(text, locale)
    assert (p.point, p.decimals, p.kind) == (point, decimals, kind)


@pytest.mark.parametrize(
    "text, locale",
    [
        ("abc", "en"),
        ("", "en"),
        ("12 widgets", "en"),  # unknown suffix
        ("5 kg", "en"),
        ("1,23", "en"),  # comma cannot be a thousands separator here
        ("1.2.3", "en"),
        ("1,2345", "en"),
        ("12,34,567", "en"),
        ("1.23", "eu"),  # dot cannot be a thousands separator here
        ("1,2,3", "eu"),
        ("5M%", "en"),  # scale and percent together
        ("%14%", "en"),
        ("2.1 to 2.3", "en"),  # two numbers
        ("1,234 567", "en"),  # mixed separators
        ("12 mm", "en"),
    ],
)
def test_parse_errors(text, locale):
    with pytest.raises(NumberParseError):
        parse_printed(text, locale)


@pytest.mark.parametrize(
    "text, half_unit",
    [
        ("2.1M", F(50000)),
        ("2.10M", F(5000)),
        ("14%", F(1, 2)),
        ("28.3%", F(1, 20)),
        ("4,812", F(1, 2)),
        ("350k", F(500)),
    ],
)
def test_half_unit(text, half_unit):
    assert parse_printed(text).half_unit == half_unit


def test_interval_rounded_and_exact():
    p = parse_printed("2.1M")
    assert p.interval() == Interval(F(2050000), F(2150000))
    assert p.interval(exact=True) == Interval.point(2100000)


@pytest.mark.parametrize(
    "text, zeros, wide",
    [
        ("2,300,000", 5, Interval(F(2250000), F(2350000))),
        ("500", 2, Interval(F(450), F(550))),
        ("200M", 2, Interval(F(150 * 10**6), F(250 * 10**6))),
        ("240", 1, None),  # one trailing zero is not treated as a round figure
        ("4,812", 0, None),
        ("2.0M", 0, None),  # a printed decimal is significant
        ("100%", 2, None),  # percentages are never treated as round figures
        ("0", 0, None),
    ],
)
def test_round_figures(text, zeros, wide):
    p = parse_printed(text)
    assert p.round_zeros == zeros
    assert p.round_interval() == wide


@pytest.mark.parametrize(
    "text, locale, alt_point",
    [
        ("1,234", "en", F(1234, 1000)),
        ("1,234", "eu", F(1234)),
        ("12.345", "en", F(12345)),
        ("1.5", "en", None),
        ("1,234,567", "en", None),
        ("2.10M", "en", None),
        ("4812", "en", None),
    ],
)
def test_locale_ambiguity_is_detected(text, locale, alt_point):
    p = parse_printed(text, locale)
    assert (p.alt[0] if p.alt else None) == alt_point
    if alt_point is not None:
        assert p.flipped().point == alt_point


def test_context_scale_multiplies_value_and_half_unit():
    p = parse_printed("1,204", scale=1000)
    assert p.point == 1204000 and p.half_unit == 500


@pytest.mark.parametrize(
    "locale, expected",
    [("tr", "eu"), ("de-DE", "eu"), ("fr_FR", "eu"), ("en-US", "en"), (None, "en"), ("ja", "en")],
)
def test_normalize_locale(locale, expected):
    assert normalize_locale(locale) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, F(1)),
        ("1000", F(1000)),
        (1000, F(1000)),
        ("million", F(10**6)),
        ("k", F(1000)),
        ("0.001", F(1, 1000)),
    ],
)
def test_parse_scale(value, expected):
    assert parse_scale(value) == expected


@pytest.mark.parametrize("bad", ["0", "-5", "lots", "1,000"])
def test_parse_scale_errors(bad):
    with pytest.raises(NumberParseError):
        parse_scale(bad)


@pytest.mark.parametrize("bad", ["1,234", "1e6", "abc", "", "1.2.3", " "])
def test_parse_decimal_rejects_anything_but_plain_decimals(bad):
    with pytest.raises(NumberParseError):
        parse_decimal(bad)


def test_parse_const():
    assert parse_const("12") == (F(12), PLAIN)
    assert parse_const("100%") == (F(100), PERCENT)
    assert parse_const("-0.5") == (F(-1, 2), PLAIN)


@given(st.integers(min_value=0, max_value=10**15))
def test_grouped_integers_round_trip_in_both_locales(n):
    assert parse_printed(f"{n:,}", "en").point == n
    assert parse_printed(f"{n:,}".replace(",", "."), "eu").point == n


@given(st.integers(min_value=0, max_value=10**9), st.integers(min_value=1, max_value=6), st.data())
def test_decimals_round_trip(whole, places, data):
    frac = data.draw(st.integers(min_value=0, max_value=10**places - 1))
    text = f"{whole:,}.{frac:0{places}d}"
    p = parse_printed(text, "en")
    assert p.point == whole + F(frac, 10**places) and p.decimals == places
    eu = text.replace(",", "#").replace(".", ",").replace("#", ".")
    assert parse_printed(eu, "eu").point == p.point


@given(st.integers(min_value=1, max_value=10**6), st.integers(min_value=0, max_value=4))
def test_true_value_lies_inside_the_printed_interval(n, places):
    """Whatever rounds to the print is inside the print's interval."""
    printed = parse_printed(f"{n / 10**places:.{places}f}", "en")
    for true_value in (
        printed.point - printed.half_unit,
        printed.point,
        printed.point + printed.half_unit,
    ):
        assert printed.interval().contains(true_value)
