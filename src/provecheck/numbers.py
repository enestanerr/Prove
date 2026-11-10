"""Parse numbers exactly as printed (SPEC §3). Deterministic, stdlib only.

A printed number is a rounded view of a true value: ``2.1M`` means the true
value lies in ``[2.05M, 2.15M]``. Parsing keeps what the print implies: the
point value, how many decimals were shown, the scale, and whether it is a
percentage.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from fractions import Fraction

from provecheck.intervals import Interval

PLAIN = "plain"
PERCENT = "percent"

# Single letters are case-sensitive, words are matched in lower case.
_LETTER_SCALES = {"k": 10**3, "K": 10**3, "m": 10**6, "M": 10**6, "b": 10**9, "B": 10**9}
_WORD_SCALES = {
    "thousand": 10**3,
    "bin": 10**3,
    "mn": 10**6,
    "million": 10**6,
    "milyon": 10**6,
    "bn": 10**9,
    "billion": 10**9,
    "milyar": 10**9,
    "tn": 10**12,
    "trillion": 10**12,
    "trilyon": 10**12,
}
_PERCENT_WORDS = {"%", "percent", "pct"}
_PP_WORDS = {"pp", "ppt", "ppts"}
_PERCENT_PREFIX_WORDS = {"%", "yüzde"}
_CURRENCY_SYMBOLS = set("$€£₺¥₹")
_CURRENCY_CODES = {
    "usd", "eur", "gbp", "try", "tl", "jpy", "chf", "cad", "aud", "cny", "inr", "us$",
}  # fmt: skip
_APPROX_MARKS = set("~≈")
_GROUP_SEPARATORS = " '"

_BODY = re.compile(r"\d(?:[\d.,' ]*\d)?")
_TOKEN = re.compile(r"[^\W\d_]+\$?|%|\S", re.UNICODE)

LOCALES = ("en", "eu")
_EU_ALIASES = {"tr", "de", "fr", "es", "it", "pt", "nl", "pl", "ru", "da", "sv", "nb", "fi"}


class NumberParseError(ValueError):
    """The text is not a number this parser understands."""


def normalize_locale(locale: str | None) -> str:
    """``en`` -> ``1,234.5``; ``eu`` (tr, de, fr, es, it, ...) -> ``1.234,5``."""
    if not locale:
        return "en"
    base = locale.strip().lower().replace("_", "-").split("-")[0]
    if base in _EU_ALIASES or base == "eu":
        return "eu"
    return "en"


@dataclass(frozen=True)
class Printed:
    """A number exactly as printed, plus what the print implies."""

    text: str
    point: Fraction
    decimals: int
    scale: Fraction
    kind: str = PLAIN
    suffix: str = ""
    round_zeros: int = 0
    alt: tuple[Fraction, int] | None = None  # (point, decimals) under the other locale

    @property
    def half_unit(self) -> Fraction:
        """Half of the last printed digit, in base units (SPEC §2)."""
        return self.scale / (2 * 10**self.decimals)

    @property
    def unit(self) -> Fraction:
        return 2 * self.half_unit

    def interval(self, exact: bool = False) -> Interval:
        if exact:
            return Interval.point(self.point)
        return Interval(self.point - self.half_unit, self.point + self.half_unit)

    def round_interval(self) -> Interval | None:
        """The wider reading of a round figure such as ``2,300,000`` (SPEC §3.2).

        A whole number ending in two or more zeros may have been rounded to its
        last non-zero digit. Percentages are not treated this way.
        """
        if self.kind != PLAIN or self.decimals != 0 or self.round_zeros < 2:
            return None
        half = self.scale * 10**self.round_zeros / 2
        return Interval(self.point - half, self.point + half)

    def flipped(self) -> Printed | None:
        """The same text read under the other locale, when that reading is valid."""
        if self.alt is None:
            return None
        point, decimals = self.alt
        return Printed(self.text, point, decimals, self.scale, self.kind, self.suffix, 0, None)


def _mantissa(body: str, locale: str) -> tuple[int, int, int]:
    """Digits of ``body`` under ``locale`` -> (integer of all digits, decimals, round zeros)."""
    thousands, decimal = (",", ".") if locale == "en" else (".", ",")
    if body.count(decimal) > 1:
        raise NumberParseError(f"more than one decimal separator in {body!r}")
    whole, _, frac = body.partition(decimal)
    if decimal in body and not frac:
        raise NumberParseError(f"nothing after the decimal separator in {body!r}")
    if frac and not frac.isdigit():
        raise NumberParseError(f"separator inside the decimal part of {body!r}")
    separators = {ch for ch in whole if not ch.isdigit()}
    if separators:
        if len(separators) > 1:
            raise NumberParseError(f"mixed digit separators in {body!r}")
        sep = separators.pop()
        if sep != thousands and sep not in _GROUP_SEPARATORS:
            raise NumberParseError(f"{sep!r} is not a thousands separator in locale {locale}")
        groups = whole.split(sep)
        if not (1 <= len(groups[0]) <= 3) or any(len(g) != 3 for g in groups[1:]):
            raise NumberParseError(f"digit groups in {body!r} are not thousands groups")
        if groups[0].isdigit() and int(groups[0]) == 0:  # 0.766 is not "766" with a zero group
            raise NumberParseError(f"{body!r} starts with a zero group")
        whole = "".join(groups)
    if not whole.isdigit():
        raise NumberParseError(f"not a number: {body!r}")
    zeros = len(whole) - len(whole.rstrip("0")) if (not frac and int(whole) != 0) else 0
    return int(whole + frac), len(frac), zeros


def _classify(tokens: list[str], *, before: bool) -> tuple[Fraction, str, str, bool]:
    """Words around the number -> (scale, kind, suffix, negative)."""
    scale, kind, suffix, negative = Fraction(1), PLAIN, "", False
    for tok in tokens:
        low = tok.lower()
        if tok in "+-" and before:
            if tok == "-":
                negative = not negative
        elif tok in _CURRENCY_SYMBOLS or low in _CURRENCY_CODES or tok in _APPROX_MARKS:
            continue
        elif (before and low in _PERCENT_PREFIX_WORDS) or (not before and low in _PERCENT_WORDS):
            if kind == PERCENT:
                raise NumberParseError("percent given twice")
            kind, suffix = PERCENT, "%"
        elif not before and low in _PP_WORDS:
            kind, suffix = PERCENT, "pp"
        elif not before and (tok in _LETTER_SCALES or low in _WORD_SCALES):
            if scale != 1:
                raise NumberParseError("two scale suffixes")
            scale = Fraction(_LETTER_SCALES.get(tok) or _WORD_SCALES[low])
            suffix = tok
        else:
            where = "before" if before else "after"
            raise NumberParseError(f"unknown text {tok!r} {where} the number")
    return scale, kind, suffix, negative


def parse_printed(text: str, locale: str = "en", scale: Fraction | int | str = 1) -> Printed:
    """Parse one printed number.

    ``scale`` is a multiplier taken from context, for a table headed
    "USD thousands" or an axis labelled "$M".
    """
    locale = normalize_locale(locale)
    s = unicodedata.normalize("NFKC", text).replace("−", "-").strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative, s = True, s[1:-1].strip()
    m = _BODY.search(s)
    if not m:
        raise NumberParseError(f"not a number: {text!r}")
    before = _TOKEN.findall(s[: m.start()])
    after = _TOKEN.findall(s[m.end() :])
    pre_scale, pre_kind, _, pre_neg = _classify(before, before=True)
    post_scale, post_kind, suffix, _ = _classify(after, before=False)
    del pre_scale
    if pre_kind == PERCENT and post_kind == PERCENT:
        raise NumberParseError("percent given twice")
    kind = PERCENT if PERCENT in (pre_kind, post_kind) else PLAIN
    if kind == PERCENT and post_scale != 1:
        raise NumberParseError("a percentage cannot carry a scale suffix")
    if kind == PERCENT and not suffix:
        suffix = "%"
    negative ^= pre_neg

    digits, decimals, zeros = _mantissa(m.group(), locale)
    total_scale = post_scale * Fraction(scale)
    if total_scale <= 0:
        raise NumberParseError("scale must be positive")
    sign = -1 if negative else 1
    point = sign * Fraction(digits, 10**decimals) * total_scale

    alt = None
    try:
        other = "eu" if locale == "en" else "en"
        a_digits, a_decimals, _ = _mantissa(m.group(), other)
        a_point = sign * Fraction(a_digits, 10**a_decimals) * total_scale
        if a_point != point:
            alt = (a_point, a_decimals)
    except NumberParseError:
        pass
    return Printed(text, point, decimals, total_scale, kind, suffix, zeros, alt)


def parse_scale(value: str | int | None) -> Fraction:
    """A context multiplier: a decimal string ("1000") or a scale word ("million")."""
    if value is None:
        return Fraction(1)
    if isinstance(value, int) and not isinstance(value, bool):
        return Fraction(value)
    s = str(value).strip()
    if s in _LETTER_SCALES:
        return Fraction(_LETTER_SCALES[s])
    if s.lower() in _WORD_SCALES:
        return Fraction(_WORD_SCALES[s.lower()])
    try:
        out = parse_decimal(s)
    except NumberParseError:
        raise NumberParseError(f"scale must be a number or a scale word, got {value!r}") from None
    if out <= 0:
        raise NumberParseError("scale must be positive")
    return out


_DECIMAL = re.compile(r"^[+-]?\d+(\.\d+)?$")


def parse_decimal(s: str) -> Fraction:
    """A plain decimal string such as ``"2100000"`` or ``"-28.3"`` (no separators)."""
    if not isinstance(s, str) or not _DECIMAL.match(s.strip()):
        raise NumberParseError(f"expected a plain decimal string, got {s!r}")
    return Fraction(s.strip())


def parse_const(s: str) -> tuple[Fraction, str]:
    """A constant in a derivation: ``"12"`` or ``"100%"`` -> (value, kind). Always exact."""
    s = str(s).strip()
    if s.endswith("%"):
        return parse_decimal(s[:-1]), PERCENT
    return parse_decimal(s), PLAIN
