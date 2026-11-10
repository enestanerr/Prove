"""Judge eval: given correct claims, does provecheck give the right verdict?

    uv run python evals/run_judge.py [--seed 1] [--n 200]

Deterministic, needs no model and no network, and runs in CI. It checks the gold
claims of a seeded synthetic corpus, plus the hand-written example documents,
and scores every verdict against the truth:

    false alarms   a clean number or a trap reported as contradicted   (must be 0)
    judge misses   a planted error not reported as contradicted         (must be 0)

Zero false alarms is a release gate: the exit code is 1 otherwise. Every bug
report that turns out to be a wrong verdict becomes a case here before it is
fixed (see docs/EVALS.md).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "synth"))

import generate  # noqa: E402
import score as scoring  # noqa: E402

from provecheck.ingest import DOC_SCHEMA, ingest  # noqa: E402
from provecheck.ingest.markdown import pages_of_markdown  # noqa: E402
from provecheck.schema import validate_claims  # noqa: E402
from provecheck.sources import resolve_all  # noqa: E402
from provecheck.verdict import check_claims  # noqa: E402

RECORDED = ROOT / "tests" / "fixtures" / "sources" / "cache"
EXAMPLES = ("kestrel-q3", "larkspur-survey", "anadolu-kargo")


class Tally:
    def __init__(self) -> None:
        self.by_type: dict[str, list[int]] = {}
        self.traps: dict[str, int] = {}
        self.false_alarms: list[str] = []
        self.misses: list[str] = []
        self.claims = self.documents = self.numbers = self.missed_numbers = 0

    def add(self, name: str, result: dict, source_rows: list[dict]) -> None:
        self.documents += 1
        self.claims += result["claims"] + len(source_rows)
        self.numbers += result["coverage"]["found"] or 0
        self.missed_numbers += result["coverage"]["missed"] or 0
        for item in [*result["planted"], *[s for s in source_rows if s["planted"]]]:
            caught = self.by_type.setdefault(item["type"], [0, 0])
            caught[1] += 1
            if item["outcome"] == "contradicted":
                caught[0] += 1
            else:
                self.misses.append(f"{name}: {item['type']} {item['id']} ended {item['outcome']}")
        for trap in result["traps"]:
            self.traps[trap["outcome"]] = self.traps.get(trap["outcome"], 0) + 1
        for alarm in [*result["false_alarms"], *result["cascades"]]:
            self.false_alarms.append(
                f"{name}: claim {alarm['claim']} ({alarm['kind']}): {alarm['sentence']}"
            )
        for row in source_rows:
            if not row["planted"] and row["outcome"] == "contradicted":
                self.false_alarms.append(f"{name}: source {row['id']} ({row['type']})")


def judge_synthetic(seed: int, index: int, cache: Path) -> tuple[str, dict, list[dict]]:
    report = generate.build(seed, index)
    claims = report.gold("report.md")
    problems = validate_claims(claims)
    if problems:
        raise SystemExit(
            f"{report.name}: the generator wrote an invalid claims file: {problems[:3]}"
        )
    doc = {"schema": DOC_SCHEMA, "path": "report.md", "sha256": None, "format": "markdown",
           "locale": None, "pages": pages_of_markdown(report.markdown())}  # fmt: skip
    generate.write_cache(report.cache, cache)
    sources = resolve_all(claims["sources"], offline=True, cache_dir=cache)
    result = scoring.score_claims(report.truth, claims, check_claims(claims, doc), doc)
    return report.name, result, scoring.score_sources(report.truth, sources)


def judge_example(name: str) -> tuple[str, dict, list[dict]]:
    folder = ROOT / "examples" / name
    claims = json.loads((folder / "claims.json").read_text(encoding="utf-8"))
    truth = json.loads((folder / "truth.json").read_text(encoding="utf-8"))
    doc = ingest(folder / "report.md")
    return name, scoring.score_claims(truth, claims, check_claims(claims, doc), doc), []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--n", type=int, default=200, help="synthetic reports to judge")
    parser.add_argument("--json", help="also write the numbers to this file")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    tally = Tally()
    cache = Path(tempfile.mkdtemp(prefix="prove-judge-"))
    shutil.copytree(RECORDED, cache, dirs_exist_ok=True)
    try:
        for index in range(1, args.n + 1):
            tally.add(*judge_synthetic(args.seed, index, cache))
        for name in EXAMPLES:
            tally.add(*judge_example(name))
    finally:
        shutil.rmtree(cache, ignore_errors=True)

    planted = sum(v[1] for v in tally.by_type.values())
    caught = sum(v[0] for v in tally.by_type.values())
    print(f"Judge eval: corpus {generate.CORPUS_VERSION}, seed {args.seed}, {args.n} synthetic reports "
          f"and {len(EXAMPLES)} examples")  # fmt: skip
    print(
        f"claims judged: {tally.claims}   numeric statements: {tally.numbers}   missed by gold claims: {tally.missed_numbers}"
    )
    print(f"planted errors contradicted: {caught}/{planted}")
    for kind, (hit, total) in sorted(tally.by_type.items()):
        print(f"  {kind:<12} {hit}/{total}")
    trap_total = sum(tally.traps.values())
    shown = ", ".join(f"{n} {outcome}" for outcome, n in sorted(tally.traps.items()))
    print(f"traps: {trap_total} ({shown})")
    print(f"judge misses: {len(tally.misses)}")
    for line in tally.misses[:20]:
        print(f"  {line}")
    print(f"false alarms: {len(tally.false_alarms)}")
    for line in tally.false_alarms[:20]:
        print(f"  {line}")
    if args.json:
        data = {"corpus": generate.CORPUS_VERSION, "seed": args.seed, "synthetic_reports": args.n,
                "examples": len(EXAMPLES), "claims": tally.claims, "planted": planted, "caught": caught,
                "by_type": {k: f"{v[0]}/{v[1]}" for k, v in sorted(tally.by_type.items())},
                "traps": trap_total, "trap_outcomes": tally.traps,
                "false_alarms": len(tally.false_alarms), "judge_misses": len(tally.misses)}  # fmt: skip
        Path(args.json).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return 1 if tally.false_alarms or tally.misses or tally.missed_numbers else 0


if __name__ == "__main__":
    raise SystemExit(main())
