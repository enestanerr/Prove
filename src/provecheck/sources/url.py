"""URL: does the page load?"""

from __future__ import annotations

from provecheck import CONTRADICTED, UNVERIFIED, VERIFIED
from provecheck.sources import Outcome, unreachable
from provecheck.sources.client import Client


def resolve(source: dict, client: Client) -> Outcome:
    address = source["value"].strip()
    if not address.lower().startswith(("http://", "https://")):
        return Outcome(UNVERIFIED, "Not a web address that can be checked.", "not-a-url")
    reply = client.get(address)
    if reply.ok:
        return Outcome(VERIFIED, f"The page loads ({reply.status}).")
    if reply.missing:
        gone = "Not Found" if reply.status == 404 else "Gone"
        return Outcome(
            CONTRADICTED, f"The page does not exist: the server answers {reply.status} {gone}."
        )
    return unreachable(reply, "The page")
