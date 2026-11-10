"""Source checks (SPEC §9): does the cited thing exist, and does it say what is quoted?

One module per kind (``doi``, ``arxiv``, ``url``, ``quote``), each a function
``resolve(source, client) -> Outcome``. Adding a resolver is one new file plus
its test and one line in ``_resolvers``.

Wording is factual: "DOI does not resolve", never "fabricated". Anything that
is not a clear answer (timeouts, paywalls, 403, offline) is ``unverified``.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from provecheck import CONTRADICTED, UNVERIFIED, VERIFIED
from provecheck.sources.client import Client, Response

SOURCES_SCHEMA = "prove.sources.v1"
TITLE_MATCH = 0.85  # at or above: the same work
TITLE_DIFFERENT = 0.5  # below: clearly a different work


@dataclass
class Outcome:
    verdict: str
    message: str
    reason: str | None = None
    found: dict = field(default_factory=dict)


def unreachable(reply: Response, what: str) -> Outcome:
    """Anything short of a clear answer is unverified, with the plain cause."""
    if reply.error == "offline":
        return Outcome(UNVERIFIED, "Not checked: offline.", "offline")
    if reply.status is None:
        return Outcome(UNVERIFIED, f"{what} could not be reached ({reply.error}).", "unreachable")
    causes = {401: "needs a login", 403: "access is refused", 429: "too many requests"}
    cause = causes.get(reply.status, "the server answered with an error")
    return Outcome(UNVERIFIED, f"{what} answered {reply.status}: {cause}.", "unreachable")


def _plain(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(re.sub(r"[^\w\s]", " ", text).split())


def similarity(a: str, b: str) -> float:
    """0..1 likeness of two titles, ignoring case and punctuation.

    A cited title that is the start of the real one (the subtitle left out) counts as a match.
    """
    a, b = _plain(a), _plain(b)
    if not a or not b:
        return 0.0
    short, long = sorted((a, b), key=len)
    if long.startswith(short + " ") and (len(short) >= 15 or len(short.split()) >= 3):
        return 1.0
    try:
        from rapidfuzz import fuzz  # optional extra, faster

        return fuzz.ratio(a, b) / 100
    except ImportError:
        return SequenceMatcher(None, a, b).ratio()


def compare_title(cited: str | None, real: str | None, year: int | None, what: str) -> Outcome:
    """Shared by the registries: decide from the title the registry returned."""
    found = {"title": real, "year": year}
    if not cited:
        return Outcome(VERIFIED, f"{what} resolves to “{real}”.", found=found)
    if not real:
        return Outcome(
            UNVERIFIED,
            f"{what} resolves, but the registry gives no title to compare.",
            "no-title",
            found,
        )
    score = similarity(cited, real)
    found["similarity"] = round(score, 2)
    when = f" ({year})" if year else ""
    if score >= TITLE_MATCH:
        return Outcome(
            VERIFIED, f"{what} resolves to “{real}”{when}, matching the cited title.", found=found
        )
    if score < TITLE_DIFFERENT:
        return Outcome(
            CONTRADICTED,
            f"{what} resolves to a different work: “{real}”{when}. The document cites “{cited}”.",
            found=found,
        )
    return Outcome(
        UNVERIFIED,
        f"{what} resolves to “{real}”{when}; the cited title is similar but not the same.",
        "title-differs",
        found,
    )


def _resolvers() -> dict:
    from provecheck.sources import arxiv, doi, quote, url

    return {"doi": doi.resolve, "arxiv": arxiv.resolve, "url": url.resolve, "quote": quote.resolve}


def resolve_all(sources: list[dict], offline: bool = False, cache_dir=None) -> dict:
    client = Client(cache_dir, offline)
    resolvers = _resolvers()
    records = []
    for source in sources:
        outcome = resolvers[source["kind"]](source, client)
        records.append(
            {
                "id": source["id"],
                "kind": source["kind"],
                "value": source["value"],
                "cited_title": source.get("cited_title"),
                "page": (source.get("loc") or {}).get("page"),
                "verdict": outcome.verdict,
                "assurance": "resolved",
                "reason": outcome.reason,
                "message": outcome.message,
                "found": outcome.found,
            }
        )
    return {"schema": SOURCES_SCHEMA, "offline": offline, "sources": records}
