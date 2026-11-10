"""Find every numeric token in a document and account for coverage (SPEC §7)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from provecheck.grounding import DocIndex, NumberInfo, find_all, normalize
from provecheck.numbers import normalize_locale

_SUFFIX = (
    r"(?:\s?%|\s?(?:pp|k|K|M|m|mn|B|bn)(?![^\W_])"
    r"|\s(?:thousand|million|billion|trillion|bin|milyon|milyar|trilyon|percent)(?![^\W_]))?"
)
# A word that starts with a letter and runs into digits (Q3, FY2026, COVID-19, v0.1)
# is an identifier, not a quantity. It is consumed and never becomes a token.
_IDENT = r"(?P<ident>[^\W\d_]+-?\d[\w.]*)"
_ORDINAL = r"(?!(?:st|nd|rd|th)(?![^\W_]))"


def _pattern(locale: str) -> re.Pattern[str]:
    thousands, decimal = (",", r"\.") if locale == "en" else (r"\.", ",")
    body = rf"(?:\d{{1,3}}(?:{thousands}\d{{3}})+(?:{decimal}\d+)?|\d+(?:{decimal}\d+)?)"
    return re.compile(rf"{_IDENT}|(?<![^\W_])(?P<num>{body})(?!\d){_ORDINAL}{_SUFFIX}", re.UNICODE)


_PATTERNS = {loc: _pattern(loc) for loc in ("en", "eu")}


@dataclass(frozen=True)
class Token:
    page: int
    start: int
    end: int
    text: str  # the number with its suffix, e.g. "2.10M" or "14%"
    body: str  # digits and separators only
    context: str
    hint: str | None = None

    def as_json(self) -> dict:
        out = {"page": self.page, "text": self.text, "context": self.context}
        if self.hint:
            out["hint"] = self.hint
        return out


def _hint(body: str) -> str | None:
    if body.isdigit() and len(body) == 4 and 1900 <= int(body) <= 2100:
        return "year"
    return None


def scan_text(text: str, page: int = 1, locale: str = "en") -> list[Token]:
    """Tokens of one already-normalised page text."""
    tokens = []
    for m in _PATTERNS[normalize_locale(locale)].finditer(text):
        if m.group("num") is None:
            continue
        start, end = m.start("num"), m.end()
        left = max(0, start - 40)
        context = (
            ("…" if left else "") + text[left : end + 40] + ("…" if end + 40 < len(text) else "")
        )
        tokens.append(
            Token(page, start, end, text[start:end], m.group("num"), context, _hint(m.group("num")))
        )
    return tokens


def scan_doc(index: DocIndex, locale: str = "en") -> list[Token]:
    out: list[Token] = []
    for page in sorted(index.pages):
        out.extend(scan_text(index.pages[page], page, locale))
    return out


def _skip_spans(entry: dict, index: DocIndex) -> tuple[list[tuple[int, int, int]], str | None]:
    """Spans covered by one ``skipped[]`` entry, or the bare text to match on tokens."""
    loc = entry.get("loc") or {}
    quote, text = normalize(loc.get("quote") or ""), normalize(entry.get("text") or "")
    pages = [loc["page"]] if loc.get("page") else sorted(index.pages)
    if not quote:
        return [(p, -1, -1) for p in pages], text
    spans = []
    for page in pages:
        for s in index.occurrences(page, quote):
            if not text:  # the whole quoted passage is skipped (a reference list, a phone block)
                spans.append((page, s, s + len(quote)))
            for t in find_all(quote, text):
                spans.append((page, s + t, s + t + len(text)))
    return spans, None


def coverage(index: DocIndex, numbers: list[NumberInfo], skipped: list[dict], locale: str) -> dict:
    """Every scanned token is checked, skipped with a reason, or missed."""
    tokens = scan_doc(index, locale)
    state = ["missed"] * len(tokens)

    def mark(page: int, start: int, end: int, value: str) -> None:
        for i, tok in enumerate(tokens):
            if tok.page == page and tok.start < end and start < tok.end and state[i] == "missed":
                state[i] = value

    for info in numbers:
        for page, start, end in info.spans:
            mark(page, start, end, "checked")
    for entry in skipped:
        spans, bare = _skip_spans(entry, index)
        if bare is not None:
            pages = {p for p, _, _ in spans}
            for i, tok in enumerate(tokens):
                if tok.page in pages and bare in (tok.text, tok.body) and state[i] == "missed":
                    state[i] = "skipped"
        else:
            for page, start, end in spans:
                mark(page, start, end, "skipped")
    missed = [tok.as_json() for tok, s in zip(tokens, state, strict=True) if s == "missed"]
    return {
        "found": len(tokens),
        "checked": state.count("checked"),
        "skipped": state.count("skipped"),
        "missed": len(missed),
        "missed_tokens": missed,
    }
