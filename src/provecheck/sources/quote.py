"""Quotation: fetch the source, normalise, search for the quoted words.

``contradicted`` needs evidence, not absence: the page must load with real text
on it *and* contain a passage that is close to the quote but not the same. A
page that loads without anything like the quote is ``unverified``, because the
text may be loaded by script or sit behind a login.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from provecheck import CONTRADICTED, UNVERIFIED, VERIFIED
from provecheck.grounding import normalize
from provecheck.sources import Outcome, unreachable
from provecheck.sources.client import Client, is_public_web_address

MIN_PAGE_CHARS = 500  # less than this is a stub, a login wall or a script shell
NEAR = 0.75  # at or above: the same passage, altered
MAX_SEARCH_CHARS = 300_000


def page_text(body: str) -> str:
    if "<" in body and re.search(r"<(html|body|p|div)\b", body, re.I):
        from provecheck.ingest.html import pages_of_html

        body = pages_of_html(body)[0]["text"]
    return normalize(body)


def _words(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", normalize(text).casefold()).split())


def closest(quote: str, text: str) -> tuple[float, str]:
    """The passage of ``text`` most like ``quote``: (similarity, passage)."""
    q, words = _words(quote).split(), _words(text[:MAX_SEARCH_CHARS]).split()
    if not q or len(words) < len(q):
        return 0.0, ""
    best, best_at, anchor = 0.0, 0, set(q)
    step = max(1, len(q) // 4)
    for start in range(0, len(words) - len(q) + 1, step):
        window = words[start : start + len(q)]
        if len(anchor.intersection(window)) < len(anchor) * 0.5:
            continue  # too few shared words to be the passage
        score = SequenceMatcher(None, " ".join(q), " ".join(window)).ratio()
        if score > best:
            best, best_at = score, start
    lo = max(0, best_at - step)
    for start in range(lo, min(len(words) - len(q), best_at + step) + 1):  # refine around the best
        score = SequenceMatcher(None, " ".join(q), " ".join(words[start : start + len(q)])).ratio()
        if score > best:
            best, best_at = score, start
    return best, " ".join(words[best_at : best_at + len(q)])


def resolve(source: dict, client: Client) -> Outcome:
    address, quote = source["value"].strip(), source.get("quote") or ""
    if not is_public_web_address(address):
        return Outcome(
            UNVERIFIED, "The source of the quotation is not a public web address.", "not-a-url"
        )
    reply = client.get(address)
    if not reply.ok:
        if reply.missing:
            return Outcome(
                UNVERIFIED,
                f"The source page does not exist ({reply.status}), so the quotation could not be checked.",
                "source-missing",
            )
        return unreachable(reply, "The source page")
    text = page_text(reply.body)
    if _words(quote) in _words(text):
        return Outcome(VERIFIED, "The quoted words appear on the source page.")
    if len(text) < MIN_PAGE_CHARS:
        return Outcome(
            UNVERIFIED,
            "The source page loaded with almost no text; it may need a login or a script.",
            "no-text",
        )
    score, passage = closest(quote, text)
    if score >= NEAR:
        return Outcome(
            CONTRADICTED,
            f"The quoted words are not on the source page. The closest passage reads: “{passage}”.",
            found={"closest": passage, "similarity": round(score, 2)},
        )
    return Outcome(
        UNVERIFIED,
        "The source page loaded, but nothing like the quotation was found in its text.",
        "not-found",
        {"similarity": round(score, 2)},
    )
