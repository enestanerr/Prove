"""arXiv: the public API says whether an id exists and what its title is."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

from provecheck import CONTRADICTED, UNVERIFIED
from provecheck.sources import Outcome, compare_title, unreachable
from provecheck.sources.client import Client

_ATOM = "{http://www.w3.org/2005/Atom}"
_PREFIX = re.compile(r"^(?:https?://arxiv\.org/(?:abs|pdf)/|arxiv:\s*)", re.I)
_ID = re.compile(r"^(\d{4}\.\d{4,5}|[a-z-]+(\.[A-Z]{2})?/\d{7})(v\d+)?$")


def clean(value: str) -> str:
    return _PREFIX.sub("", value.strip()).removesuffix(".pdf")


def resolve(source: dict, client: Client) -> Outcome:
    ident = clean(source["value"])
    what = f"arXiv {ident}"
    if not _ID.match(ident):
        return Outcome(CONTRADICTED, f"{what} is not a valid arXiv identifier.")
    reply = client.get(
        f"https://export.arxiv.org/api/query?id_list={quote(ident)}", accept="application/atom+xml"
    )
    if not reply.ok:
        return unreachable(reply, "arXiv")
    try:
        feed = ET.fromstring(reply.body)
    except ET.ParseError:
        return Outcome(
            UNVERIFIED, "arXiv answered with something that is not a feed.", "unreachable"
        )
    entries = [
        e
        for e in feed.findall(f"{_ATOM}entry")
        if (e.findtext(f"{_ATOM}title") or "").strip() != "Error"
    ]
    if not entries:
        return Outcome(CONTRADICTED, f"{what} does not exist: arXiv has no paper with this id.")
    entry = entries[0]
    title = " ".join((entry.findtext(f"{_ATOM}title") or "").split()) or None
    published = entry.findtext(f"{_ATOM}published") or ""
    year = int(published[:4]) if published[:4].isdigit() else None
    return compare_title(source.get("cited_title"), title, year, what)
