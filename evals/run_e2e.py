"""End-to-end eval: headless Claude Code with only the Prove plugin, one document per run.

    uv run python evals/run_e2e.py --model claude-sonnet-5-5 --effort medium --n 30
    uv run python evals/run_e2e.py --model claude-sonnet-5-5 --docs examples/kestrel-q3/report.pdf

Each document is copied alone into a fresh folder, so the model sees the
document and nothing else from this repo (no gold claims, no expected reports).
The run is scored against the ``truth.json`` that sits beside the document.

A model must be named on the command line: this spends real usage, and nothing
here falls back to a default. Results go to
``evals/results/<date>-<model>-<effort>/``. Transcripts are kept locally and
are not committed.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import score as scoring  # noqa: E402

import provecheck  # noqa: E402
from provecheck.ingest import ingest  # noqa: E402

PROMPT = "Audit {name}: check every number, chart and citation in it."
ALLOWED = "Skill,Read,Write,Edit,Glob,Grep,Bash(python *),Bash(python3 *),Bash(ls *),Bash(cat *),Bash(mkdir *)"
FIELDS = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")


def run_one(doc: Path, out: Path, args: argparse.Namespace) -> dict:
    """Run the audit of one document in an empty folder and collect what it produced."""
    work = out / "run"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    shutil.copy(doc, work / doc.name)
    if doc.suffix.lower() in (".md", ".html"):  # figures a Markdown file points at
        for image in doc.parent.glob("*.png"):
            if not image.name.endswith("-crop.png"):
                shutil.copy(image, work / image.name)

    env = dict(os.environ)
    # The interpreter of this environment first, so `python` has the optional PDF support.
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    cmd = [
        shutil.which("claude") or "claude",
        "-p", args.prompt.format(name=doc.name),
        "--model", args.model,
        "--effort", args.effort,
        "--plugin-dir", str(ROOT / "plugin"),
        "--setting-sources", "project",
        "--strict-mcp-config",
        "--permission-mode", "acceptEdits",
        "--allowedTools", ALLOWED,
        "--output-format", "stream-json",
        "--verbose",
        "--no-session-persistence",
    ]  # fmt: skip
    started = time.time()
    transcript = out / "transcript.jsonl"
    with open(transcript, "w", encoding="utf-8") as log:
        try:
            proc = subprocess.run(
                cmd, cwd=work, env=env, stdout=log, stderr=subprocess.PIPE, timeout=args.timeout,
                text=True, encoding="utf-8",
            )  # fmt: skip
            status = (
                "ok" if proc.returncode == 0 else f"exit {proc.returncode}: {proc.stderr[-400:]}"
            )
        except subprocess.TimeoutExpired:
            status = f"timeout after {args.timeout}s"

    result = {}
    for line in transcript.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "result":
            result = event
    usage = result.get("usage") or {}
    record = {
        "document": doc.name,
        "status": status,
        "wall_seconds": round(time.time() - started, 1),
        "turns": result.get("num_turns"),
        "cost_usd": result.get("total_cost_usd"),
        "tokens": {k: usage.get(k) for k in FIELDS},
        "permission_denials": len(result.get("permission_denials") or []),
        "answer": result.get("result"),
    }
    for name in ("claims.json", "verdicts.json", "prove-report.json", "prove-report.md"):
        produced = work / "prove-work" / name
        if produced.is_file():
            shutil.copy(produced, out / name)
    return record


def score_one(doc: Path, out: Path, record: dict) -> dict:
    truth_path = doc.parent / "truth.json"
    if not (out / "claims.json").is_file() or not (out / "verdicts.json").is_file():
        record["score"] = None
        record["status"] += " | no claims.json or verdicts.json was produced"
        return record
    claims = json.loads((out / "claims.json").read_text(encoding="utf-8"))
    verdicts = json.loads((out / "verdicts.json").read_text(encoding="utf-8"))
    if truth_path.is_file():
        truth = json.loads(truth_path.read_text(encoding="utf-8"))
        record["score"] = scoring.score_claims(truth, claims, verdicts, ingest(doc))
        record["charts"] = scoring.score_charts(truth, claims)
    return record


def summarize(records: list[dict]) -> dict:
    scored = [r for r in records if r.get("score")]
    marks = [m for r in scored for m in r.get("charts") or [] if "error_share_of_span" in m]
    planted = sum(r["score"]["planted_total"] for r in scored)
    claims = sum(r["score"]["claims"] for r in scored)
    alarms = sum(len(r["score"]["false_alarms"]) for r in scored)

    def total(key: str) -> int:
        return sum((r["tokens"] or {}).get(key) or 0 for r in records)

    return {
        "documents": len(records),
        "scored": len(scored),
        "planted_errors": planted,
        "caught": sum(r["score"]["caught"] for r in scored),
        "caught_as_suspect": sum(r["score"]["caught_as_suspect"] for r in scored),
        "claims": claims,
        "false_alarms": alarms,
        "false_alarms_per_1000_claims": round(1000 * alarms / claims, 1) if claims else None,
        "cascades": sum(len(r["score"]["cascades"]) for r in scored),
        "traps": sum(r["score"]["trap_total"] for r in scored),
        "traps_flagged": sum(r["score"]["traps_flagged"] for r in scored),
        "numbers_found": sum(r["score"]["coverage"]["found"] or 0 for r in scored),
        "numbers_missed": sum(r["score"]["coverage"]["missed"] or 0 for r in scored),
        "chart_marks_read": len(marks),
        "chart_marks_within_interval": sum(m["contains_true_value"] for m in marks),
        "chart_mean_error_share_of_span": (
            round(sum(m["error_share_of_span"] for m in marks) / len(marks), 4) if marks else None
        ),
        "tokens_in_per_doc": round(
            sum(total(k) for k in FIELDS if k != "output_tokens") / max(1, len(records))
        ),
        "tokens_out_per_doc": round(total("output_tokens") / max(1, len(records))),
        "wall_seconds_per_doc": round(
            sum(r["wall_seconds"] for r in records) / max(1, len(records))
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", required=True, help="model id, e.g. claude-sonnet-5-5")
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--docs", nargs="*", default=[], help="documents to audit")
    parser.add_argument("--corpus", default=str(ROOT / "evals" / "corpus"))
    parser.add_argument("--n", type=int, default=0, help="take the first N corpus documents")
    parser.add_argument("--format", choices=["pdf", "md"], default="pdf")
    parser.add_argument("--timeout", type=int, default=1800, help="seconds per document")
    parser.add_argument("--prompt", default=PROMPT)
    parser.add_argument(
        "--out", help="results folder (default: evals/results/<date>-<model>-<effort>)"
    )
    args = parser.parse_args()

    docs = [Path(d).resolve() for d in args.docs]
    if args.n:
        found = sorted(Path(args.corpus).glob(f"*/report.{args.format}"))
        docs += [d.resolve() for d in found[: args.n]]
    if not docs:
        parser.error("nothing to run: give --docs or --n")
    stamp = datetime.date.today().isoformat()
    out_root = Path(args.out or ROOT / "evals" / "results" / f"{stamp}-{args.model}-{args.effort}")
    out_root.mkdir(parents=True, exist_ok=True)
    version = subprocess.run(
        [shutil.which("claude") or "claude", "--version"], capture_output=True, text=True
    ).stdout.strip()

    records = []
    for doc in docs:
        out = out_root / doc.parent.name
        out.mkdir(parents=True, exist_ok=True)
        print(f"== {doc.parent.name}/{doc.name}", flush=True)
        record = score_one(doc, out, run_one(doc, out, args))
        (out / "run.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n", "utf-8"
        )
        s = record.get("score")
        if s:
            print(
                f"   {record['status']}: caught {s['caught']}/{s['planted_total']}, "
                f"false alarms {len(s['false_alarms'])}, missed numbers {s['coverage']['missed']}, "
                f"{record['wall_seconds']}s",
                flush=True,
            )
        else:
            print(f"   {record['status']}", flush=True)
        records.append(record)

    summary = {
        "date": stamp,
        "model": args.model,
        "effort": args.effort,
        "claude_code": version,
        "plugin": json.loads((ROOT / "plugin/.claude-plugin/plugin.json").read_text("utf-8"))[
            "version"
        ],
        "provecheck": provecheck.__version__,
        "prompt": args.prompt,
        **summarize(records),
    }
    (out_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", "utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
