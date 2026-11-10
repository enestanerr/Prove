"""Command line: ingest, scan, check, crop, sources, report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from provecheck import CONTRADICTED, SUSPECT, UNVERIFIED, __version__

USAGE_ERROR = 2


class CliError(Exception):
    """A usage or input error. Exit code 2."""


def _read_json(path: str) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise CliError(f"cannot read {path}: {exc.strerror or exc}") from None
    except ValueError as exc:
        raise CliError(f"{path} is not valid JSON: {exc}") from None


def _write_json(path: Path, data: dict) -> None:
    from provecheck.report import dumps

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(data), encoding="utf-8", newline="\n")


def cmd_ingest(args: argparse.Namespace) -> int:
    from provecheck.ingest import ingest

    doc = ingest(args.doc, args.render_pages, args.locale)
    out = Path(args.output or "doc.json")
    _write_json(out, doc)
    textless = [p["page"] for p in doc["pages"] if not p["has_text"]]
    print(
        f"{out}: {len(doc['pages'])} page(s), format {doc['format']}, sha256 {doc['sha256'][:12]}…"
    )
    if textless:
        print(
            f"No text layer on page(s) {textless}: numbers there can only be read from the image."
        )
    if args.render_pages:
        print(f"Page images written to {args.render_pages}")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    from provecheck.grounding import DocIndex
    from provecheck.ingest import load_doc
    from provecheck.scan import scan_doc

    doc = load_doc(args.doc)
    tokens = scan_doc(DocIndex(doc), args.locale or doc.get("locale") or "en")
    if args.json:
        print(json.dumps([t.as_json() for t in tokens], ensure_ascii=False, indent=1))
        return 0
    for t in tokens:
        hint = f"  [{t.hint}?]" if t.hint else ""
        print(f"p{t.page}  {t.text:<14} {t.context}{hint}")
    print(
        f"\n{len(tokens)} numeric tokens. Each one belongs in `numbers` or in `skipped` with a reason."
    )
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    from provecheck.ingest import load_doc
    from provecheck.report import coverage_line
    from provecheck.schema import validate_claims
    from provecheck.verdict import check_claims

    claims = _read_json(args.claims)
    errors = validate_claims(claims)
    if errors:
        print(
            f"{args.claims} is not a valid claims file. Fix these and run again:", file=sys.stderr
        )
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return USAGE_ERROR
    doc = load_doc(args.doc) if args.doc else None
    verdicts = check_claims(claims, doc)
    out = Path(args.output or Path(args.claims).with_name("verdicts.json"))
    _write_json(out, verdicts)

    s = verdicts["summary"]
    print(
        f"{s[CONTRADICTED]} contradicted, {s[SUSPECT]} suspect, "
        f"{s[UNVERIFIED]} unverified, {s['verified']} verified  ->  {out}"
    )
    print(coverage_line(verdicts["coverage"]))
    for w in verdicts["warnings"]:
        print(f"warning: {w}")
    for rec in verdicts["claims"]:
        if rec["verdict"] in (CONTRADICTED, SUSPECT):
            print(f"  {rec['verdict']:<12} {rec['id']}: {rec['sentence']}")
    fixable = [r for r in verdicts["claims"] if r["verdict"] == UNVERIFIED]
    if fixable:
        print("Not checked (fix your claims file if the cause is in it):")
        for rec in fixable:
            print(f"  {rec['id']}: [{rec['reason']}] {rec['message']}")
    cov = verdicts["coverage"]
    if cov and cov["missed"]:
        print(
            f"Missed numbers ({cov['missed']}): add each to `numbers` or to `skipped` with a reason."
        )
        for t in cov["missed_tokens"][:30]:
            print(f"  p{t['page']}  {t['text']:<14} {t['context']}")
        if cov["missed"] > 30:
            print(f"  … and {cov['missed'] - 30} more (see {out})")
    return 0


def cmd_crop(args: argparse.Namespace) -> int:
    from provecheck.ingest.pdf import crop

    try:
        box = tuple(float(v) for v in args.box.split(","))
    except ValueError:
        box = ()
    if len(box) != 4:
        raise CliError(
            "--box takes four numbers: x0,y0,x1,y1 (fractions of the page, or points/pixels)"
        )
    if args.upscale < 1 or args.upscale > 8:
        raise CliError("--upscale must be between 1 and 8")
    info = crop(Path(args.doc), args.page, box, args.upscale, Path(args.output))
    print(f"{info['out']}: {info['width']}×{info['height']} px")
    return 0


def cmd_sources(args: argparse.Namespace) -> int:
    from provecheck.schema import validate_claims
    from provecheck.sources import resolve_all

    claims = _read_json(args.claims)
    errors = validate_claims(claims)
    if errors:
        print(f"{args.claims} is not a valid claims file:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return USAGE_ERROR
    result = resolve_all(claims.get("sources") or [], offline=args.offline, cache_dir=args.cache)
    out = Path(args.output or Path(args.claims).with_name("sources.json"))
    _write_json(out, result)
    for rec in result["sources"]:
        print(
            f"  {rec['verdict']:<12} {rec['id']} {rec['kind']}: {rec['value']} — {rec['message']}"
        )
    print(f"{len(result['sources'])} source(s) -> {out}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    from provecheck.report import build_report, exit_code, write_reports
    from provecheck.report.md import headline

    verdicts = _read_json(args.verdicts)
    if verdicts.get("schema") != "prove.verdicts.v1":
        raise CliError(f"{args.verdicts} is not a verdicts file (run `provecheck check` first)")
    sources_path = (
        Path(args.sources) if args.sources else Path(args.verdicts).with_name("sources.json")
    )
    sources = _read_json(str(sources_path)) if sources_path.is_file() else None
    report = build_report(verdicts, sources)
    formats = [f for f in ("html", "md", "json", "card") if getattr(args, f)] or [
        "html",
        "md",
        "json",
    ]
    out_dir = Path(args.output or Path(args.verdicts).parent)
    written = write_reports(report, out_dir, formats)
    print(headline(report["summary"]))
    print(report["coverage_line"])
    for path in written:
        print(f"wrote {path}")
    code = exit_code(report["summary"], args.fail_on)
    if code:
        print(
            f"exit code {code}: at least one claim is {args.fail_on} (this is a finding, not a failure)"
        )
    return code


def cmd_relations(args: argparse.Namespace) -> int:
    from provecheck.relations import REGISTRY

    for name in sorted(REGISTRY):
        print(f"{name:<11} {REGISTRY[name].summary}")
    return 0


def cmd_later(args: argparse.Namespace) -> int:
    raise CliError(f"`provecheck {args.command}` arrives in v0.2. See the roadmap in the README.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="provecheck",
        description="Audit every checkable claim in a document. The model proposes checks; this decides.",
    )
    p.add_argument("--version", action="version", version=f"provecheck {__version__}")
    sub = p.add_subparsers(dest="command", metavar="command")

    a = sub.add_parser("ingest", help="document -> doc.json (text, tables, page images)")
    a.add_argument("doc")
    a.add_argument("-o", "--output", help="where to write doc.json (default: ./doc.json)")
    a.add_argument("--render-pages", metavar="DIR", help="also write one PNG per PDF page")
    a.add_argument("--locale", help="number format of the document: en (1,234.5) or eu (1.234,5)")
    a.set_defaults(fn=cmd_ingest)

    a = sub.add_parser("scan", help="list every numeric token with its location")
    a.add_argument("doc", help="a document or a doc.json")
    a.add_argument("--json", action="store_true")
    a.add_argument("--locale")
    a.set_defaults(fn=cmd_scan)

    a = sub.add_parser("check", help="claims.json + doc.json -> verdicts.json")
    a.add_argument("claims")
    a.add_argument("--doc", help="doc.json (or the document itself) to ground numbers against")
    a.add_argument("-o", "--output", help="default: verdicts.json next to the claims file")
    a.set_defaults(fn=cmd_check)

    a = sub.add_parser("crop", help="cut a region out of a PDF page or image and enlarge it")
    a.add_argument("--doc", required=True, help="a PDF, or a PNG/JPEG page image")
    a.add_argument("--page", type=int, default=1)
    a.add_argument("--box", required=True, help="x0,y0,x1,y1 as fractions of the page (0..1)")
    a.add_argument("--upscale", type=int, default=2)
    a.add_argument("-o", "--output", required=True)
    a.set_defaults(fn=cmd_crop)

    a = sub.add_parser("sources", help="resolve DOIs, arXiv ids, URLs and quotations")
    a.add_argument("claims")
    a.add_argument("--offline", action="store_true", help="do not use the network")
    a.add_argument("--cache", metavar="DIR", help="response cache (default: .provecheck-cache)")
    a.add_argument("-o", "--output", help="default: sources.json next to the claims file")
    a.set_defaults(fn=cmd_sources)

    a = sub.add_parser("report", help="verdicts.json -> HTML, Markdown, JSON, SVG card")
    a.add_argument("verdicts")
    for fmt in ("html", "md", "json", "card"):
        a.add_argument(f"--{fmt}", action="store_true")
    a.add_argument("-o", "--output", metavar="DIR", help="default: next to the verdicts file")
    a.add_argument(
        "--sources", help="sources.json (default: next to the verdicts file, if present)"
    )
    a.add_argument(
        "--fail-on",
        choices=[CONTRADICTED, SUSPECT, "never"],
        default=CONTRADICTED,
        help="exit 1 when a claim has this verdict (default: contradicted)",
    )
    a.set_defaults(fn=cmd_report)

    a = sub.add_parser("relations", help="list the relations a derivation can use")
    a.set_defaults(fn=cmd_relations)

    for name, text in (
        ("logic", "check stated rules with a solver"),
        ("audit", "run every step with an API key"),
    ):
        a = sub.add_parser(name, help=f"{text} (v0.2)")
        a.add_argument("rest", nargs="*")
        a.set_defaults(fn=cmd_later)
    return p


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):  # Windows consoles are often not UTF-8
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "fn", None):
        parser.print_help()
        return USAGE_ERROR
    from provecheck.ingest import IngestError

    try:
        return args.fn(args)
    except (CliError, IngestError) as exc:
        print(f"provecheck: {exc}", file=sys.stderr)
        return USAGE_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
