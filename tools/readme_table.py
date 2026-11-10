"""Write the measured-results block of README.md from the result files in evals/results.

    uv run python evals/run_judge.py --json evals/results/judge.json
    uv run python tools/readme_table.py            # rewrite the block in README.md
    uv run python tools/readme_table.py --check    # fail if README.md is out of date

Every number in the README's results section comes from here, so it cannot drift
from what was measured. Rows are sorted by date, newest first.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "evals" / "results"
START, END = "<!-- measured:start -->", "<!-- measured:end -->"
NAMES = {
    "claude-fable-5-2": "Fable 5.2",
    "claude-opus-5-5": "Opus 5.5",
    "claude-sonnet-5-5": "Sonnet 5.5",
    "claude-haiku-5-5": "Haiku 5.5",
}


def pct(part: int, whole: int) -> str:
    return f"{part}/{whole} ({100 * part / whole:.0f}%)" if whole else "–"


def block() -> str:
    lines = []
    judge_path = RESULTS / "judge.json"
    if judge_path.is_file():
        j = json.loads(judge_path.read_text(encoding="utf-8"))
        lines += [
            "**Judge eval** (no model, runs in CI): given correct claims, is the verdict right?",
            "",
            f"Synthetic corpus {j['corpus']}, seed {j['seed']}: {j['synthetic_reports']} reports and "
            f"{j['examples']} example documents, {j['claims']:,} claims.",
            "",
            "| Planted errors contradicted | False alarms | Traps flagged |",
            "| :- | :- | :- |",
            f"| {pct(j['caught'], j['planted'])} | {j['false_alarms']} | "
            f"{j['trap_outcomes'].get('contradicted', 0)} of {j['traps']} |",
            "",
        ]
    runs = []
    for path in sorted(RESULTS.glob("*/summary.json"), reverse=True):
        runs.append(json.loads(path.read_text(encoding="utf-8")))
    if runs:
        first = runs[0]
        lines += [
            "**End-to-end eval** (the model reads the document and writes the claims itself):",
            "",
            "| Model | Run | Reports audited | Planted errors caught | False alarms | Knock-on flags | "
            "Traps flagged | Numbers missed | Chart readings holding the true value | "
            "Tokens in (with cache reads) / out per doc |",
            "| :- | :- | :- | :- | :- | :- | :- | :- | :- | :- |",
        ]
        for s in runs:
            model = f"{NAMES.get(s['model'], s['model'])} ({s['effort']})"
            alarms = f"{s['false_alarms']} of {s['claims']} claims"
            marks = pct(s["chart_marks_within_interval"], s["chart_marks_read"])
            lines.append(
                f"| {model} | {s['date']} | {s['scored']}/{s['documents']} | "
                f"{pct(s['caught'], s['planted_errors'])} | {alarms} | {s['cascades']} | "
                f"{s['traps_flagged']} of {s['traps']} | "
                f"{s['numbers_missed']} of {s['numbers_found']:,} | {marks} | "
                f"{s['tokens_in_per_doc']:,} / {s['tokens_out_per_doc']:,} |"
            )
        types = " · ".join(f"{k} {v}" for k, v in first["caught_by_type"].items())
        lines += [
            "",
            f"Caught by error type, {NAMES.get(first['model'], first['model'])}: {types}.",
            f"Chart marks read: {first['chart_marks_read']} of the {first['chart_marks']} drawn in "
            f"the corpus. Cited sources checked: {first['sources_checked']} of "
            f"{first['sources_cited']}. Cost: about ${first['cost_usd_per_doc']:.2f} and "
            f"{first['wall_seconds_per_doc']} seconds per document.",
            f"Versions: Claude Code {first['claude_code'].split()[0]}, plugin {first['plugin']}, "
            f"provecheck {first['provecheck']}.",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    fresh = f"{head}{START}\n{block()}{END}{tail}"
    if args.check:
        if fresh != text:
            print(
                "README.md results block is out of date; run tools/readme_table.py", file=sys.stderr
            )
            return 1
        print("README.md results block matches evals/results")
        return 0
    readme.write_text(fresh, encoding="utf-8", newline="\n")
    print("wrote the results block in README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
