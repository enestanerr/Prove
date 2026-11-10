from fractions import Fraction as F

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from provecheck.intervals import Interval, Target, outward, to_decimal

fractions = st.fractions(min_value=-(10**6), max_value=10**6, max_denominator=10**4)


@st.composite
def intervals(draw):
    a, b = draw(fractions), draw(fractions)
    return Interval(min(a, b), max(a, b))


@st.composite
def interval_with_member(draw):
    iv = draw(intervals())
    t = draw(st.fractions(min_value=0, max_value=1, max_denominator=100))
    return iv, iv.lo + (iv.hi - iv.lo) * t


def test_empty_interval_is_rejected():
    with pytest.raises(ValueError):
        Interval(F(2), F(1))


def test_point_interval():
    p = Interval.point(5)
    assert p.is_point and p.width == 0 and p.mid == 5 and p.contains(5)


def test_basic_arithmetic():
    a, b = Interval(F(1), F(2)), Interval(F(3), F(5))
    assert a + b == Interval(F(4), F(7))
    assert b - a == Interval(F(1), F(4))
    assert a * b == Interval(F(3), F(10))
    assert b / a == Interval(F(3, 2), F(5))
    assert -a == Interval(F(-2), F(-1))


def test_multiplication_handles_signs():
    assert Interval(F(-2), F(3)) * Interval(F(-1), F(4)) == Interval(F(-8), F(12))


@pytest.mark.parametrize(
    "divisor",
    [Interval(F(-1), F(1)), Interval(F(0), F(2)), Interval(F(-3), F(0)), Interval.point(0)],
)
def test_division_by_interval_containing_zero_is_an_error(divisor):
    with pytest.raises(ZeroDivisionError):
        Interval(F(1), F(2)) / divisor


def test_contains_and_overlaps_are_closed():
    a = Interval(F(1), F(2))
    assert a.contains(1) and a.contains(2) and not a.contains(F(201, 100))
    assert a.overlaps(Interval(F(2), F(3)))  # touching counts
    assert not a.overlaps(Interval(F(201, 100), F(3)))
    assert a.contains_interval(Interval(F(5, 4), F(7, 4)))


def test_widen_and_hull_and_scale():
    a = Interval(F(1), F(2))
    assert a.widen(F(1, 2)) == Interval(F(1, 2), F(5, 2))
    assert a.hull(Interval(F(5), F(6))) == Interval(F(1), F(6))
    assert a.scale(-2) == Interval(F(-4), F(-2))
    with pytest.raises(ValueError):
        a.widen(-1)


@given(interval_with_member(), interval_with_member())
def test_sum_difference_product_contain_every_member(am, bm):
    (a, x), (b, y) = am, bm
    assert (a + b).contains(x + y)
    assert (a - b).contains(x - y)
    assert (a * b).contains(x * y)


@given(interval_with_member(), interval_with_member())
def test_quotient_contains_every_member(am, bm):
    (a, x), (b, y) = am, bm
    assume(not b.contains(0))
    assert (a / b).contains(x / y)


@given(intervals(), intervals())
def test_overlaps_is_symmetric(a, b):
    assert a.overlaps(b) == b.overlaps(a)


@given(intervals(), st.fractions(min_value=0, max_value=100))
def test_widen_never_shrinks(a, amount):
    assert a.widen(amount).contains_interval(a)


@given(intervals(), intervals())
def test_hull_contains_both(a, b):
    h = a.hull(b)
    assert h.contains_interval(a) and h.contains_interval(b)


def test_target_of_interval_behaves_like_it():
    t = Target.of(Interval(F(1), F(2)))
    assert t.contains(1) and t.contains(2) and not t.contains(3)
    assert t.overlaps(Interval(F(2), F(9))) and not t.overlaps(Interval(F(3), F(9)))


@pytest.mark.parametrize(
    "target, inside, outside",
    [
        (Target(F(50), None, lo_open=True), F(51), F(50)),  # over 50
        (Target(None, F(50), hi_open=True), F(49), F(50)),  # under 50
        (Target(F(50), None), F(50), F(49)),  # at least 50
        (Target(None, F(50)), F(50), F(51)),  # at most 50
    ],
)
def test_one_sided_targets(target, inside, outside):
    assert target.contains(inside) and not target.contains(outside)
    assert target.overlaps(Interval.point(inside)) and not target.overlaps(Interval.point(outside))


def test_open_bound_excludes_a_touching_interval():
    over = Target(F(50), None, lo_open=True)
    assert not over.overlaps(Interval(F(40), F(50)))
    assert over.overlaps(Interval(F(40), F(501, 10)))


def test_decimal_conversion_is_outward_safe():
    third = F(1, 3)
    wide = outward(to_decimal(third), to_decimal(third))
    assert wide.lo < third < wide.hi
    assert wide.width < F(1, 10**40)
