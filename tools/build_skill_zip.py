"""Build ``dist/prove-skill.zip``: the skill folder alone, for upload to claude.ai and Cowork.

    uv run python tools/build_pyz.py && uv run python tools/build_skill_zip.py

The archive holds one folder, ``prove/``, with ``SKILL.md`` at its top. It is the
release asset named in the README. The zipapp inside must be fresh, so this refuses to
run when ``build_pyz.py --check`` would fail.
"""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugin" / "skills" / "prove"
TARGET = ROOT / "dist" / "prove-skill.zip"
FIXED_TIME = (2020, 1, 1, 0, 0, 0)


def main() -> int:
    fresh = subprocess.run([sys.executable, str(ROOT / "tools" / "build_pyz.py"), "--check"])
    if fresh.returncode:
        return fresh.returncode
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in SKILL.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    with zipfile.ZipFile(TARGET, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            info = zipfile.ZipInfo(f"prove/{path.relative_to(SKILL).as_posix()}", FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            data = path.read_bytes()
            if path.suffix == ".md":
                data = data.replace(b"\r\n", b"\n")
            zf.writestr(info, data)
    print(f"wrote {TARGET.relative_to(ROOT)} ({TARGET.stat().st_size:,} bytes, {len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
