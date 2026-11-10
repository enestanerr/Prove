"""A small shareable scorecard: counts only, no document content."""

from __future__ import annotations

from provecheck.report import ORDER

COLORS = {
    "contradicted": "#c62828",
    "suspect": "#b26a00",
    "unverified": "#5f6b7a",
    "verified": "#2e7d32",
}


def render(report: dict) -> str:
    summary, cov = report["summary"], report.get("coverage")
    tiles = []
    for i, verdict in enumerate(ORDER):
        x = 24 + i * 113
        tiles.append(
            f'<g transform="translate({x},64)">'
            f'<rect width="101" height="76" rx="8" fill="#ffffff" stroke="#d9dee5"/>'
            f'<rect width="101" height="5" rx="2.5" fill="{COLORS[verdict]}"/>'
            f'<text x="50.5" y="44" text-anchor="middle" font-size="28" font-weight="700" '
            f'fill="{COLORS[verdict]}">{summary[verdict]}</text>'
            f'<text x="50.5" y="64" text-anchor="middle" font-size="11" fill="#48515c">{verdict}</text>'
            "</g>"
        )
    if cov:
        line = (
            f"{cov['found']} numeric statements · {cov['checked']} checked · "
            f"{cov['skipped']} skipped · {cov['missed']} missed"
        )
    else:
        line = "coverage not available"
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="500" height="190" viewBox="0 0 500 190" '
        'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif" role="img" '
        'aria-label="Prove scorecard">\n'
        '<rect width="500" height="190" rx="12" fill="#f5f7fa" stroke="#d9dee5"/>\n'
        '<text x="24" y="40" font-size="20" font-weight="700" fill="#16202c">Prove</text>\n'
        '<text x="88" y="40" font-size="12" fill="#48515c">claims audited, verdicts by code</text>\n'
        + "\n".join(tiles)
        + f'\n<text x="24" y="168" font-size="12" fill="#48515c">{line}</text>\n</svg>\n'
    )
