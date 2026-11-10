"""Print what Claude did in one end-to-end run: every tool call, every error, the answer.

    uv run python evals/show_transcript.py evals/results/<run>/<doc>/transcript.jsonl

Used to tighten SKILL.md from real transcripts: wherever Claude improvised, the skill
text was unclear.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def brief(value: object, limit: int = 220) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + " …"


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        kind = event.get("type")
        if kind == "assistant":
            for block in event["message"].get("content", []):
                if block.get("type") == "tool_use":
                    args = block.get("input") or {}
                    detail = (
                        args.get("command") or args.get("file_path") or args.get("skill") or args
                    )
                    print(f"-> {block['name']}: {brief(detail)}")
                elif block.get("type") == "text" and block["text"].strip():
                    print(f"   says: {brief(block['text'], 300)}")
        elif kind == "user":
            for block in event["message"].get("content", []):
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_result"
                    and block.get("is_error")
                ):
                    print(f"   ERROR: {brief(block.get('content'), 400)}")
        elif kind == "result":
            print(f"\n== result ({event.get('num_turns')} turns, ${event.get('total_cost_usd')})")
            print(event.get("result"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
