"""Grounding: every number must be found, as printed, where the model says it is (SPEC §6).

This is what stops a model from "fixing" a number on the way in. The checks are
string checks on the extracted page text, after a normalisation that forgives
typography (spaces, curly quotes, dash variants, table pipes, Markdown
emphasis) and never forgives a digit.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from provecheck.numbers import (
    PERCENT,
    NumberParseError,
    Printed,
    normalize_locale,
    parse_decimal,
    parse_printed,
    parse_scale,
)

_TRANSLATE = str.maketrans(
    {
        "‘": "'", "’": "'", "‚": "'", "‛": "'",
        "“": '"', "”": '"', "„": '"', "‟": '"',
        "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "―": "-", "−": "-",
        "|": " ", "*": "", "`": "", "­": "", "​": "",
    }
)  # fmt: skip
_WS = re.compile(r"\s+")

EXACT_REASONS = ("count", "ledger", "defined", "cell")
_PERCENT_UNITS = {"%", "percent", "pct", "pp", "ppt", "ppts", "percentage points"}


def normalize(text: str) -> str:
    """NFKC, typographic variants unified, whitespace collapsed. Case is kept."""
    text = unicodedata.normalize("NFKC", text).translate(_TRANSLATE)
    return _WS.sub(" ", text).strip()


def find_all(haystack: str, needle: str) -> list[int]:
    out, start = [], 0
    while needle and (i := haystack.find(needle, start)) != -1:
        out.append(i)
        start = i + 1
    return out


class DocIndex:
    """Normalised page texts of a ``doc.json``."""

    def __init__(self, doc: dict | None) -> None:
        self.doc = doc
        self.pages: dict[int, str] = {}
        self.textless: set[int] = set()
        for page in (doc or {}).get("pages", []):
            n = page["page"]
            self.pages[n] = normalize(page.get("text") or "")
            if not page.get("has_text", bool(self.pages[n])):
                self.textless.add(n)

    @property
    def available(self) -> bool:
        return self.doc is not None

    def occurrences(self, page: int, quote: str) -> list[int]:
        return find_all(self.pages.get(page, ""), quote)

    def pages_with(self, quote: str) -> list[int]:
        return [n for n, text in sorted(self.pages.items()) if quote in text]


@dataclass
class NumberInfo:
    """One ``numbers[]`` entry after grounding and parsing."""

    entry: dict
    printed: Printed | None = None
    exact: bool = False
    kind: str = "plain"
    assurance: str = "computed"
    problem: tuple[str, str] | None = None  # (reason, message)
    spans: list[tuple[int, int, int]] = field(default_factory=list)  # (page, start, end)

    @property
    def id(self) -> str:
        return self.entry["id"]

    @property
    def text(self) -> str:
        return self.entry["text"]


def ground_number(entry: dict, index: DocIndex, doc_locale: str) -> NumberInfo:
    info = NumberInfo(entry)
    loc = entry.get("loc") or {}
    page, quote, text = loc.get("page"), normalize(loc.get("quote") or ""), normalize(entry["text"])

    # 1 and 2: the quote is on the page, the number is in the quote.
    if text not in quote:
        info.problem = ("not-grounded", f"the text {entry['text']!r} is not inside its quote")
    elif not index.available or page in index.textless:
        # No text layer to check against: the number was read from an image.
        info.assurance = "read"
    elif page not in index.pages:
        info.problem = (
            "not-grounded",
            f"page {page} does not exist (the document has {len(index.pages)} pages)",
        )
    else:
        starts = index.occurrences(page, quote)
        if not starts:
            elsewhere = [n for n in index.pages_with(quote) if n != page]
            hint = f" (it occurs on page {elsewhere[0]})" if elsewhere else ""
            info.problem = ("not-grounded", f"the quote was not found on page {page}{hint}")
        for s in starts:
            for t in find_all(quote, text):
                info.spans.append((page, s + t, s + t + len(text)))

    # 3: provecheck's own reading of the text agrees with the model's value.
    locale = normalize_locale(entry.get("locale") or doc_locale)
    try:
        printed = parse_printed(entry["text"], locale, parse_scale(entry.get("scale")))
        value = parse_decimal(str(entry["value"]))
    except NumberParseError as exc:
        if info.problem is None:
            info.problem = ("parse-error", str(exc))
        return info
    info.printed = printed
    info.exact = entry.get("exact") in EXACT_REASONS
    unit = str(entry.get("unit") or "").strip().lower()
    info.kind = PERCENT if printed.kind == PERCENT or unit in _PERCENT_UNITS else "plain"
    decimals = entry.get("decimals")
    if info.problem is None and (
        value != printed.point or (decimals is not None and decimals != printed.decimals)
    ):
        info.problem = (
            "parse-mismatch",
            f"provecheck reads {entry['text']!r} as {_plain(printed.point)} with "
            f"{printed.decimals} decimals; the claims file says value {entry['value']}"
            + (f", decimals {decimals}" if decimals is not None else ""),
        )
    return info


def _plain(x) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{float(x):g}"
