"""Rebuild the generated files of the examples: figures, PDFs and expected reports.

    uv run python tools/build_examples.py            # everything
    uv run python tools/build_examples.py --reports  # only the expected reports

The Markdown reports and the claims files are written by hand; everything else
in ``examples/`` comes from here, so a change in report layout is one command.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
EXAMPLES = ROOT / "examples"


def bar_chart(path: Path, title: str, labels: list[str], values: list[float], ymax: float, step: float,
              value_labels: list[str] | None = None, ylabel: str = "") -> None:  # fmt: skip
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=150)
    bars = ax.bar(labels, values, color="#3b6ea5", width=0.6)
    ax.set_ylim(0, ymax)
    ax.set_yticks([step * i for i in range(int(ymax / step) + 1)])
    ax.yaxis.grid(True, color="#cccccc", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(title, fontsize=11)
    if ylabel:
        ax.set_ylabel(ylabel)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    if value_labels:
        for bar, text in zip(bars, value_labels, strict=True):
            ax.annotate(
                text,
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                ha="center",
                va="bottom",
                fontsize=9,
            )
    fig.tight_layout()
    fig.savefig(path, metadata={"Software": None})
    plt.close(fig)


def build_kestrel() -> None:
    import mdpdf

    from provecheck.ingest.pdf import crop

    d = EXAMPLES / "kestrel-q3"
    bar_chart(d / "figure2.png", "Marketing spend by quarter (USD thousands)",
              ["Q4", "Q1", "Q2", "Q3"], [265, 240, 275, 310], 400, 50)  # fmt: skip
    crop(d / "figure2.png", 1, (0.0, 0.0, 1.0, 1.0), 2, d / "figure2-crop.png")
    mdpdf.render(d / "report.md", d / "report.pdf")


def build_reports(name: str) -> None:
    """ingest -> check -> report, exactly as a user would run them."""
    from provecheck.ingest import ingest
    from provecheck.report import build_report, write_reports
    from provecheck.verdict import check_claims

    d = EXAMPLES / name
    claims = json.loads((d / "claims.json").read_text(encoding="utf-8"))
    doc = ingest(Path(claims["document"]["path"]))
    report = build_report(check_claims(claims, doc))
    for path in write_reports(report, d, ["json", "md", "html", "card"], base=d):
        print(f"wrote {path.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reports", action="store_true", help="only rebuild the expected reports")
    args = parser.parse_args()
    import os

    os.chdir(ROOT)  # document paths in the claims files are relative to the repo root
    if not args.reports:
        build_kestrel()
    for name in sorted(p.name for p in EXAMPLES.iterdir() if (p / "claims.json").is_file()):
        build_reports(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
