"""Validate every claims file in examples/ and reference/ (run in CI).

Each file must pass the hand-written validator and the JSON Schema.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from provecheck.schema import load_schema, validate_claims

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    validator = jsonschema.Draft202012Validator(load_schema())
    files = sorted((ROOT / "examples").glob("*/claims.json"))
    files.append(ROOT / "reference" / "claims.example.json")
    failed = 0
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_claims(data) + [e.message for e in validator.iter_errors(data)]
        print(f"{'ok  ' if not errors else 'FAIL'} {path.relative_to(ROOT)}")
        for e in errors:
            print(f"     {e}")
        failed += bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
