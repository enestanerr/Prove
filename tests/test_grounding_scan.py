import pytest
from helpers import doc_of, num

from provecheck.grounding import DocIndex, ground_number, normalize
from provecheck.scan import coverage, scan_text


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("a b\n\n c", "a b c"),
        ("“quoted” ‘single’", "\"quoted\" 'single'"),
        ("2020–2021 — up −5%", "2020-2021 - up -5%"),
        ("| North | 1,204 |", "North 1,204"),
        ("**bold** and `code`", "bold and code"),
        ("ﬁnance", "finance"),  # NFKC unfolds the ligature
        ("soft­hyphen", "softhyphen"),
    ],
)
def test_normalize(raw, expected):
    assert normalize(raw) == expected


def test_normalize_keeps_case_and_digits():
    assert normalize("Revenue 2.10M") != normalize("revenue 2.10M")
    assert normalize("2.10M") != normalize("2.20M")


def test_ground_number_records_where_the_number_sits():
    index = DocIndex(doc_of("Revenue rose from $2.10M to $2.30M."))
    info = ground_number(num("a", "2.30M", quote="from $2.10M to $2.30M"), index, "en")
    assert info.problem is None and info.assurance == "computed"
    page, start, end = info.spans[0]
    assert index.pages[page][start:end] == "2.30M"


def test_ground_number_covers_every_occurrence_of_a_repeated_quote():
    index = DocIndex(doc_of("Total | 4,812 ... Total | 4,812"))
    info = ground_number(num("a", "4,812", quote="Total | 4,812"), index, "en")
    assert len(info.spans) == 2


# text -> tokens the scanner must find
SCAN_CASES = [
    ("Revenue rose from $2.10M in Q2 to $2.30M in Q3, up 14%.", ["2.10M", "2.30M", "14%"]),
    ("Kestrel Outdoor Co. - Q3 2026 report", ["2026"]),
    ("North 1,204 South 988", ["1,204", "988"]),
    ("In FY2026 the H1 result beat COVID-19 lows on v0.1 of the plan", []),
    ("the 1st, 2nd, 3rd and 14th places", []),
    ("a total of 4,812 orders.", ["4,812"]),
    ("spend reached 350k", ["350k"]),
    ("about 4.5 million users and 3 billion views", ["4.5 million", "3 billion"]),
    ("margins of 41.2% and 43.7 %", ["41.2%", "43.7 %"]),
    ("a gain of 2.5 pp", ["2.5 pp"]),
    ("ranges 10-20 and 2025,2026", ["10", "20", "2025", "2026"]),
    ("values (1,234) and [5]", ["1,234", "5"]),
    ("12/31/2026 at 10:30", ["12", "31", "2026", "10", "30"]),
    ("no numbers here", []),
    ("1,234,567.89 exactly", ["1,234,567.89"]),
]


@pytest.mark.parametrize("text, expected", SCAN_CASES)
def test_scan_text(text, expected):
    assert [t.text for t in scan_text(normalize(text))] == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Gelir 2,10 milyon TL, artış %14 oldu", ["2,10 milyon", "14"]),
        ("toplam 1.234,5 ve 12 bin kişi", ["1.234,5", "12 bin"]),
        ("3,5 milyar", ["3,5 milyar"]),
    ],
)
def test_scan_text_european(text, expected):
    assert [t.text for t in scan_text(normalize(text), locale="tr")] == expected


def test_scan_hints_years():
    tokens = scan_text("In 2026 revenue was 2,026 units")
    assert [(t.text, t.hint) for t in tokens] == [("2026", "year"), ("2,026", None)]


def test_scan_tokens_carry_context():
    (token,) = scan_text("Revenue rose 14% last year")
    assert "rose 14% last" in token.context


def _coverage(page: str, numbers, skipped):
    index = DocIndex(doc_of(page))
    infos = [ground_number(n, index, "en") for n in numbers]
    return coverage(index, infos, skipped, "en")


def test_coverage_counts_checked_skipped_and_missed():
    page = "Q3 2026 report. Revenue rose from $2.10M to $2.30M, up 14%, across 12 stores."
    numbers = [num("a", "2.10M"), num("b", "2.30M"), num("t", "14%")]
    cov = _coverage(
        page,
        numbers,
        [{"text": "2026", "loc": {"page": 1, "quote": "Q3 2026 report"}, "reason": "year"}],
    )
    assert (cov["found"], cov["checked"], cov["skipped"], cov["missed"]) == (5, 3, 1, 1)
    assert cov["missed_tokens"][0]["text"] == "12"


def test_skip_without_a_quote_covers_every_occurrence():
    cov = _coverage("In 2026 and again in 2026, 7 things", [], [{"text": "2026", "reason": "year"}])
    assert (cov["skipped"], cov["missed"]) == (2, 1)


def test_skip_can_be_limited_to_a_page():
    index = DocIndex(doc_of("2026", "2026"))
    cov = coverage(index, [], [{"text": "2026", "loc": {"page": 2}, "reason": "year"}], "en")
    assert (cov["skipped"], cov["missed"]) == (1, 1)


def test_skip_of_a_whole_passage():
    page = "Results up 5%. [1] Smith (2021). Journal 12(3), 45-67. doi:10.1000/182"
    skip = {
        "loc": {"page": 1, "quote": "[1] Smith (2021). Journal 12(3), 45-67. doi:10.1000/182"},
        "reason": "reference list",
    }
    cov = _coverage(page, [num("t", "5%")], [skip])
    assert cov["missed"] == 0 and cov["checked"] == 1 and cov["skipped"] >= 5


def test_a_number_is_never_counted_twice():
    page = "up 14%"
    cov = _coverage(page, [num("t", "14%")], [{"text": "14%", "reason": "duplicate"}])
    assert (cov["checked"], cov["skipped"]) == (1, 0)


def test_ungrounded_numbers_do_not_count_as_checked():
    cov = _coverage("up 14%", [num("t", "15%")], [])
    assert (cov["checked"], cov["missed"]) == (0, 1)
