"""Small builders so tests read like the documents they describe."""

from __future__ import annotations

from fractions import Fraction

from provecheck.numbers import parse_printed
from provecheck.schema import validate_claims
from provecheck.verdict import check_claims


def dec(x: Fraction) -> str:
    """A terminating fraction as a plain decimal string."""
    sign, x = ("-" if x < 0 else ""), abs(x)
    places = 0
    while (x * 10**places).denominator != 1:
        places += 1
    digits = str(int(x * 10**places)).rjust(places + 1, "0")
    return sign + (digits[:-places] + "." + digits[-places:] if places else digits)


def doc_of(*pages: str, textless: tuple[int, ...] = ()) -> dict:
    return {
        "schema": "prove.doc.v1",
        "path": "test.md",
        "sha256": "f" * 64,
        "format": "text",
        "locale": None,
        "pages": [
            {"page": i, "text": text, "tables": [], "images": [], "has_text": i not in textless}
            for i, text in enumerate(pages, start=1)
        ],
    }


def num(
    id: str, text: str, quote: str | None = None, page: int = 1, exact=None, locale="en", **extra
) -> dict:
    """A numbers[] entry whose value and decimals are what provecheck itself would read."""
    printed = parse_printed(text, extra.get("locale", locale), extra.get("scale", 1))
    entry = {
        "id": id,
        "text": text,
        "value": dec(printed.point),
        "decimals": printed.decimals,
        "exact": exact,
        "loc": {"page": page, "quote": quote if quote is not None else text},
    }
    if locale != "en":
        entry["locale"] = locale
    entry.update(extra)
    return entry


def ref(id: str) -> dict:
    return {"ref": id}


def const(value: str) -> dict:
    return {"const": value}


def op(name: str, *args) -> dict:
    return {"op": name, "args": [ref(a) if isinstance(a, str) else a for a in args]}


def derived(id: str, target: str | None, derivation: dict, hedge=None) -> dict:
    claim = {
        "id": id,
        "kind": "derived",
        "hedge": hedge,
        "derivation": derivation,
        "say": "A check.",
    }
    if target is not None:
        claim["target"] = target
    return claim


def claims_file(numbers, claims, charts=(), sources=(), skipped=(), locale="en") -> dict:
    return {
        "schema": "prove.claims.v1",
        "document": {"path": "test.md", "locale": locale},
        "numbers": list(numbers),
        "claims": list(claims),
        "charts": list(charts),
        "sources": list(sources),
        "skipped": list(skipped),
    }


def run(pages, numbers, claims, **kw) -> dict:
    """Check a small claims file against page texts -> full verdicts dict."""
    doc = kw.pop("doc", None) or (doc_of(*pages) if pages is not None else None)
    data = claims_file(numbers, claims, **kw)
    assert validate_claims(data) == [], validate_claims(data)
    return check_claims(data, doc)


def verdict_of(result: dict, claim_id: str = "c1") -> dict:
    return next(r for r in result["claims"] if r["id"] == claim_id)


def quick(
    text: str, numbers: dict[str, str], target: str, derivation: dict, hedge=None, exact=(), **kw
) -> dict:
    """One page, one claim. ``numbers`` maps id -> printed text found in ``text``."""
    entries = [
        num(i, t, quote=text, exact="count" if i in exact else None, **kw.pop(i, {}))
        for i, t in numbers.items()
    ]
    result = run([text], entries, [derived("c1", target, derivation, hedge)], **kw)
    return verdict_of(result)
