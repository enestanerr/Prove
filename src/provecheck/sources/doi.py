"""DOI: Crossref, then DataCite, then the doi.org handle registry."""

from __future__ import annotations

import re
from urllib.parse import quote

from provecheck import CONTRADICTED, UNVERIFIED, VERIFIED
from provecheck.sources import Outcome, compare_title, unreachable
from provecheck.sources.client import Client

_PREFIX = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.I)


def clean(value: str) -> str:
    return _PREFIX.sub("", value.strip()).strip().rstrip(".")


def _year(parts: object) -> int | None:
    try:
        return int(parts["date-parts"][0][0])
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def resolve(source: dict, client: Client) -> Outcome:
    doi = clean(source["value"])
    what = f"DOI {doi}"
    path = quote(doi, safe="/")

    crossref = client.get(f"https://api.crossref.org/works/{path}", accept="application/json")
    if crossref.ok and (data := crossref.json()):
        work = data.get("message") or {}
        title = " ".join((work.get("title") or [""])[0].split()) or None
        year = _year(work.get("issued")) or _year(work.get("published"))
        return compare_title(source.get("cited_title"), title, year, what)
    if not crossref.missing:
        return unreachable(crossref, "Crossref")

    datacite = client.get(f"https://api.datacite.org/dois/{path}", accept="application/json")
    if datacite.ok and (data := datacite.json()):
        attrs = (data.get("data") or {}).get("attributes") or {}
        titles = attrs.get("titles") or [{}]
        return compare_title(
            source.get("cited_title"), titles[0].get("title"), attrs.get("publicationYear"), what
        )
    if not datacite.missing:
        return unreachable(datacite, "DataCite")

    handle = client.get(f"https://doi.org/api/handles/{path}", accept="application/json")
    if handle.ok:
        if source.get("cited_title"):
            return Outcome(
                UNVERIFIED,
                f"{what} is registered at doi.org, but neither Crossref nor DataCite has its title.",
                "no-title",
            )
        return Outcome(VERIFIED, f"{what} is registered at doi.org.")
    if handle.missing:
        return Outcome(
            CONTRADICTED,
            f"{what} does not resolve: Crossref, DataCite and doi.org answer “not found”.",
        )
    return unreachable(handle, "doi.org")
