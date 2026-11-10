"""Build ``plugin/skills/prove/scripts/provecheck.pyz`` from ``src/provecheck``.

    uv run python tools/build_pyz.py           # build
    uv run python tools/build_pyz.py --check   # fail if the committed file is stale

The zipapp holds the whole package: the core is standard library only and the
optional features import their dependency when they are used. It runs with any
``python3`` >= 3.10 and needs no install, which is what makes the skill work in
sandboxes with no network.

``--check`` compares file names and contents, not archive bytes, because the
deflate stream can differ between zlib builds.
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
TARGET = ROOT / "plugin" / "skills" / "prove" / "scripts" / "provecheck.pyz"
SHEBANG = b"#!/usr/bin/env python3\n"
MAIN = "from provecheck.cli import main\n\nraise SystemExit(main())\n"
FIXED_TIME = (2020, 1, 1, 0, 0, 0)  # reproducible archives


def members() -> dict[str, bytes]:
    files = {"__main__.py": MAIN.encode()}
    for path in sorted((SRC / "provecheck").rglob("*")):
        if path.is_file() and path.suffix in (".py", ".json") and "__pycache__" not in path.parts:
            data = path.read_bytes().replace(b"\r\n", b"\n")
            files[path.relative_to(SRC).as_posix()] = data
    return files


def build() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name, data in members().items():
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, data)
    return SHEBANG + buffer.getvalue()


def contents(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as zf:
        return {name: zf.read(name) for name in zf.namelist()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="verify the committed zipapp is fresh")
    args = parser.parse_args()
    if args.check:
        if not TARGET.is_file():
            print(f"{TARGET.relative_to(ROOT)} is missing; run tools/build_pyz.py", file=sys.stderr)
            return 1
        have, want = contents(TARGET), members()
        stale = sorted(n for n in set(have) | set(want) if have.get(n) != want.get(n))
        if stale:
            print(f"{TARGET.relative_to(ROOT)} is stale; run tools/build_pyz.py", file=sys.stderr)
            for name in stale:
                print(f"  differs: {name}", file=sys.stderr)
            return 1
        print(f"{TARGET.relative_to(ROOT)} is fresh ({len(want)} files)")
        return 0
    data = build()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(data)
    print(f"wrote {TARGET.relative_to(ROOT)} ({len(data):,} bytes, {len(members())} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
