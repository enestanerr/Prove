"""Record the HTTP answers behind tests/fixtures/sources (needs the network; run by hand).

    uv run python tools/record_source_fixtures.py

The resolvers' own on-disk cache is the fixture format: tests run the real
resolvers offline against this folder. Registry answers are trimmed to the
fields the resolvers read, so the fixtures stay small.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "sources"
CACHE = FIXTURES / "cache"


def trim(record: dict) -> dict:
    try:
        data = json.loads(record["body"])
    except ValueError:
        return record
    if "api.crossref.org" in record["url"] and isinstance(data.get("message"), dict):
        keep = ("DOI", "title", "issued", "published", "type", "container-title")
        data = {
            "status": data.get("status"),
            "message": {k: data["message"][k] for k in keep if k in data["message"]},
        }
    elif "api.datacite.org" in record["url"] and isinstance(data.get("data"), dict):
        attrs = data["data"].get("attributes") or {}
        data = {
            "data": {
                "attributes": {
                    k: attrs[k] for k in ("doi", "titles", "publicationYear") if k in attrs
                }
            }
        }
    record["body"] = json.dumps(data, ensure_ascii=False)
    return record


def main() -> int:
    # A neutral client name for the recording run.
    os.environ.setdefault("PROVECHECK_USER_AGENT", "provecheck-fixture-recorder")
    from provecheck.sources import resolve_all

    if CACHE.exists():
        shutil.rmtree(CACHE)
    claims = json.loads((FIXTURES / "claims.json").read_text(encoding="utf-8"))
    result = resolve_all(claims["sources"], cache_dir=CACHE)
    for path in sorted(CACHE.glob("*.json")):
        record = trim(json.loads(path.read_text(encoding="utf-8")))
        path.write_text(
            json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
        )
    for rec in result["sources"]:
        print(f"{rec['verdict']:<12} {rec['id']:<16} {rec['message']}")
    print(f"{len(list(CACHE.glob('*.json')))} recorded answers in {CACHE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
