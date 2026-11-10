"""Synthetic corpus: reports about fictional organisations, with planted errors and traps.

    uv run python evals/synth/generate.py --seed 1 --n 30 --out evals/corpus

Every report is built from seeded random data, so the generator knows the truth:
which printed numbers are wrong (``planted``), which only look wrong (``traps``),
and what each chart really shows. It writes, per report:

    report.md  report.pdf  figure1.png  figure2.png
    truth.json        what was planted, the traps, the true chart values
    claims.gold.json  the claims file a perfect reader would write

``build(seed, index)`` is pure and fast (no files, no plotting); the judge eval
uses it directly. Rendering needs matplotlib and PyMuPDF.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from provecheck.display import fixed  # noqa: E402

CORPUS_VERSION = "v1"
ORGS = ["Harbor", "Juniper", "Cobalt", "Meridian", "Saffron", "Tamarack", "Osprey", "Linden", "Quarry", "Basalt"]  # fmt: skip
KINDS = ["Logistics", "Foods", "Clinic Group", "Energy Cooperative", "Books", "Transit Authority", "Hardware", "Housing Trust"]  # fmt: skip
REGIONS = ["North", "South", "East", "West", "Central", "Coastal", "Highland", "Valley"]
UNITS = ["orders", "visits", "shipments", "enrolments", "service calls"]
METRICS = ["Gross margin", "On-time rate", "Retention rate", "Occupancy rate"]
SERIES = ["Support tickets", "Marketing spend", "Energy use", "Training hours"]
COSTS = ["Staff", "Rent", "Software", "Travel", "Insurance", "Utilities"]
QUARTERS = ["Q4", "Q1", "Q2", "Q3"]
MONTHS = ["Jun", "Jul", "Aug", "Sep"]
AREAS = ["Metro", "Suburban", "Rural"]

REAL_WORKS = [
    ("10.1177/1948550616673876", "Brown, N. J. L., & Heathers, J. A. J.", 2017,
     "The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology"),
    ("10.3758/s13428-015-0664-2", "Nuijten, M. B., Hartgerink, C. H. J., et al.", 2016,
     "The prevalence of statistical reporting errors in psychology (1985–2013)"),
]  # fmt: skip
QUOTE_URL = "https://www.iana.org/help/example-domains"
QUOTE_TRUE = "These domains may be used as illustrative examples in documents without prior coordination with us."
QUOTE_ALTERED = "These domains may be used as illustrative examples in documents only with prior coordination with us."


def dec(x: Fraction) -> str:
    """A terminating fraction as the plain decimal string a claims file uses."""
    places = 0
    while (x * 10**places).denominator != 1:
        places += 1
    return fixed(x, places, places).replace(",", "")


def F(x: float | int | str, places: int = 6) -> Fraction:
    return Fraction(round(float(x) * 10**places), 10**places)


def rnd(x: Fraction, places: int) -> Fraction:
    return Fraction(round(x * 10**places), 10**places)


class Report:
    """One report under construction: the Markdown, the gold claims and the truth, in step."""

    def __init__(self, seed: int, index: int) -> None:
        self.rng = random.Random(f"prove-{CORPUS_VERSION}-{seed}-{index}")
        self.name = f"doc-{index:03d}"
        self.locale = "de" if self.rng.random() < 0.2 else "en"
        self.org = f"{self.rng.choice(ORGS)} {self.rng.choice(KINDS)}"
        self.pages: list[list[str]] = [[]]
        self.numbers: list[dict] = []
        self.claims: list[dict] = []
        self.charts: list[dict] = []
        self.sources: list[dict] = []
        self.skipped: list[dict] = [{"text": "2026", "reason": "year"}]
        self.truth: dict = {"planted": [], "traps": [], "charts": [], "sources": []}
        self.figures: list[dict] = []
        self.cache: dict[str, tuple[int, str]] = {}

    # --- writing ---------------------------------------------------------------------

    @property
    def page(self) -> int:
        return len(self.pages)

    def add(self, *lines: str) -> None:
        self.pages[-1].extend([*lines, ""])

    def new_page(self) -> None:
        self.pages.append([])

    def fmt(self, x: Fraction | int, places: int = 0) -> str:
        """A number as this report prints it: 1,234.5 or, in European notation, 1.234,5."""
        text = fixed(Fraction(x), places, places)
        if self.locale != "en":
            text = text.replace(",", "#").replace(".", ",").replace("#", ".")
        return text

    def num(self, text: str, value: Fraction, places: int, quote: str, **extra) -> str:
        ident = f"n{len(self.numbers) + 1}"
        loc = {"page": extra.pop("page", self.page), "quote": quote}
        if extra.pop("image", False):
            loc["image"] = True
        entry = {"id": ident, "text": text, "value": dec(Fraction(value)), "decimals": places,
                 "exact": extra.pop("exact", None), "loc": loc, **extra}  # fmt: skip
        self.numbers.append(entry)
        return ident

    def claim(
        self, target: str | None, derivation: dict, say: str, hedge: str | None = None
    ) -> str:
        ident = f"c{len(self.claims) + 1}"
        claim = {
            "id": ident,
            "kind": "derived",
            "hedge": hedge,
            "derivation": derivation,
            "say": say,
        }
        if target:
            claim["target"] = target
        self.claims.append(claim)
        return ident

    def chart_claim(self, check: str, say: str, **fields) -> None:
        ident = f"c{len(self.claims) + 1}"
        self.claims.append(
            {
                "id": ident,
                "kind": "chart",
                "check": check,
                "chart": fields.pop("chart"),
                "say": say,
                **fields,
            }
        )

    def mark(
        self, kind: str, error_type: str, text: str, quote: str, page: int | None = None, **extra
    ) -> None:
        item = {"id": f"{'e' if kind == 'planted' else 't'}{len(self.truth[kind]) + 1}",
                "type": error_type, "page": page or self.page, "text": text, "quote": quote, **extra}  # fmt: skip
        self.truth[kind].append(item)

    def chance(self, p: float) -> bool:
        return self.rng.random() < p

    def reading(self, true: Fraction, span: Fraction) -> tuple[dict, dict]:
        """Two honest readings of a mark: both contain the true value."""

        def one(width: float) -> dict:
            half = span * F(width)
            shift = half * F(self.rng.uniform(-0.6, 0.6))
            lo, hi = rnd(true + shift - half, 1), rnd(true + shift + half, 1)
            return {"lo": dec(min(lo, rnd(true, 1))), "hi": dec(max(hi, rnd(true, 1)))}

        return one(0.02), one(0.012)

    # --- blocks ----------------------------------------------------------------------

    def summary(self) -> None:
        r, money = self.rng, "$" if self.locale == "en" else "€"
        a_true = F(r.uniform(1.2, 9.5))
        b_true = a_true * (1 + F(r.uniform(3, 18)) / 100)
        kind = r.choices(["clean", "planted", "trap"], [0.35, 0.3, 0.35])[0]
        places = 1 if kind == "trap" else 2
        a, b = rnd(a_true, places), rnd(b_true, places)
        if kind == "trap":  # the author computed the rate from unrounded figures
            pct = rnd((b_true / a_true - 1) * 100, 0)
        else:
            pct = rnd((b / a - 1) * 100, 0)
            if kind == "planted":
                pct += r.choice([-1, 1]) * r.randint(3, 6)
        ta, tb, tp = f"{self.fmt(a, places)}M", f"{self.fmt(b, places)}M", f"{self.fmt(pct)}%"
        text = f"Revenue rose from {money}{ta} in Q2 to {money}{tb} in Q3, up {tp}."
        self.add("## Summary", "", text)
        ids = [self.num(t, v * 10**6, places, text, unit="currency") for t, v in ((ta, a), (tb, b))]
        target = self.num(tp, pct, 0, text, unit="%")
        self.claim(
            target,
            op("pct_change", *ids),
            "Revenue growth should be the change between the two quarters.",
        )
        if kind == "planted":
            self.mark("planted", "pct_change", tp, text)
        elif kind == "trap":
            self.mark("traps", "rounding", tp, text)

        metric = r.choice(METRICS)
        p1 = F(r.uniform(20, 60), 1)
        gain = F(r.uniform(1.5, 6), 1)
        t1, t2, tg = f"{self.fmt(p1, 1)}%", f"{self.fmt(p1 + gain, 1)}%", self.fmt(gain, 1)
        if self.chance(0.3):  # points written as a percentage
            text = f"{metric} improved from {t1} to {t2}, an increase of {tg}%."
            ids = [self.num(t, v, 1, text, unit="%") for t, v in ((t1, p1), (t2, p1 + gain))]
            target = self.num(f"{tg}%", gain, 1, text, unit="%")
            say = "The sentence gives the increase as a percentage, so it should be the relative change."
            self.claim(target, op("pct_change", *ids), say)
            self.mark("planted", "pp_vs_pct", f"{tg}%", text)
        else:
            text = f"{metric} improved from {t1} to {t2}, a gain of {tg} percentage points."
            ids = [self.num(t, v, 1, text, unit="%") for t, v in ((t1, p1), (t2, p1 + gain))]
            target = self.num(tg, gain, 1, text, unit="pp")
            self.claim(
                target,
                op("pp_diff", ids[1], ids[0]),
                "The gain should be the difference in points.",
            )
        self.add(text)

    def regions(self) -> None:
        r = self.rng
        unit = r.choice(UNITS)
        names = r.sample(REGIONS, r.randint(4, 5))
        values = [r.randint(300, 2500) for _ in names]
        total = sum(values)
        sum_error = self.chance(0.3)
        printed_total = total + (
            r.choice([-1, 1]) * r.choice([10, 20, 30, 110]) if sum_error else 0
        )

        # Page 1: the total restated, and a hedged share.
        summary_page = self.page
        restated = None
        if not sum_error:
            crossref_error = self.chance(0.3)
            shown = total + (
                r.choice([-1, 1]) * r.choice([9, 27, 90, 180]) if crossref_error else 0
            )
            text = f"In total, {self.fmt(shown)} {unit} were recorded in the quarter."
            self.add(text)
            restated = (
                self.num(self.fmt(shown), shown, 0, text, exact="count", unit=unit),
                crossref_error,
                text,
                shown,
            )
        hedged = r.randrange(len(names))
        share = Fraction(values[hedged] * 100, total)
        about = rnd(share, 0) + r.choice([-1, 0, 0, 1])
        hedge_text = f"About {self.fmt(about)}% of {unit} came from the {names[hedged]} region."
        self.add(hedge_text)
        hedge_id = self.num(f"{self.fmt(about)}%", about, 0, hedge_text, unit="%")

        # Page 2: the table and a share.
        self.new_page()
        self.add(
            f"## {unit.capitalize()} by region",
            "",
            f"| Region | {unit.capitalize()} |",
            "| :--- | ---: |",
        )
        self.pages[-1].pop()
        rows = []
        for name, value in zip(names, values, strict=True):
            self.pages[-1].append(f"| {name} | {self.fmt(value)} |")
            rows.append(
                self.num(
                    self.fmt(value),
                    value,
                    0,
                    f"{name} | {self.fmt(value)}",
                    exact="count",
                    unit=unit,
                )
            )
        total_quote = f"Total | {self.fmt(printed_total)}"
        self.pages[-1].extend([f"| {total_quote} |", ""])
        total_id = self.num(
            self.fmt(printed_total), printed_total, 0, total_quote, exact="count", unit=unit
        )
        parts = op("sum", *rows)
        self.claim(total_id, parts, "The total row should be the sum of the regions.")
        if sum_error:
            self.mark("planted", "sum", self.fmt(printed_total), total_quote)
        if restated:
            ident, wrong, text, shown = restated
            self.claim(
                ident, op("eq", total_id), "The total in the summary should match the table."
            )
            if wrong:
                self.mark("planted", "crossref", self.fmt(shown), text, page=summary_page)
        self.claim(
            hedge_id,
            op("pct_of", rows[hedged], parts),
            "The share should be the region divided by all regions.",
            "approx",
        )
        self.mark("traps", "hedge", f"{self.fmt(about)}%", hedge_text, page=summary_page)

        pick = r.choice([i for i in range(len(names)) if i != hedged])
        share = rnd(Fraction(values[pick] * 100, total), 1)
        share_error = self.chance(0.3)
        if share_error:
            share += r.choice([-1, 1]) * F(r.uniform(2, 6), 1)
        text = f"The {names[pick]} region accounted for {self.fmt(share, 1)}% of {unit}."
        self.add(text)
        ident = self.num(f"{self.fmt(share, 1)}%", share, 1, text, unit="%")
        self.claim(
            ident,
            op("pct_of", rows[pick], parts),
            "The share should be the region divided by all regions.",
        )
        if share_error:
            self.mark("planted", "pct_of", f"{self.fmt(share, 1)}%", text)

    def _axis(self, lowest: int, highest: int, baseline: bool) -> tuple[int, int, int]:
        step = 50 if highest <= 500 else 100 if highest <= 1000 else 200
        top = (highest // step + 2) * step
        bottom = max(0, (lowest // step - 1) * step) if baseline else 0
        return bottom, top, step

    def _off(self, true: int, span: int) -> int:
        """A wrong value at least 12% of the axis span away, never a round figure."""
        shift = round(span * self.rng.uniform(0.13, 0.22))
        wrong = true + shift if self.chance(0.5) or true - shift <= 0 else true - shift
        return wrong + 3 if wrong % 100 == 0 else wrong

    def series_chart(self) -> None:
        r = self.rng
        metric = r.choice(SERIES)
        kind = r.choices(["bar", "line"], [0.7, 0.3])[0]
        labels = QUARTERS if kind == "bar" else MONTHS
        values = [r.randint(120, 880) for _ in labels]
        values = [v + 7 if v % 100 == 0 else v for v in values]
        lo, hi, step = self._axis(min(values), max(values), baseline=self.chance(0.3))
        span = hi - lo
        with_labels = kind == "bar" and self.chance(0.4)
        text_error = self.chance(0.35)
        label_error = with_labels and not text_error and self.chance(0.4)
        at = r.randrange(len(labels))
        printed_labels = list(values)
        if label_error:
            printed_labels[at] = self._off(values[at], span)

        figure, page = "Figure 1", self.page
        caption = f"{figure}: {metric} by {'quarter' if kind == 'bar' else 'month'}, thousands"
        self.add(f"![{caption}](figure1.png)")
        self.skipped.append(
            {"text": "1", "loc": {"page": page, "quote": figure}, "reason": "figure number"}
        )
        self.figures.append({"file": "figure1.png", "kind": kind, "title": f"{metric} (thousands)", "labels": labels,
                             "values": values, "axis": [lo, hi, step],
                             "value_labels": [self.fmt(v) for v in printed_labels] if with_labels else None})  # fmt: skip
        marks, notes = [], []
        for label, value in zip(labels, values, strict=True):
            read_a, read_b = self.reading(Fraction(value), Fraction(span))
            marks.append(
                {"label": label, "read_a": read_a, "read_b": read_b, "printed_label": None}
            )
        if lo > 0 and kind == "bar":
            notes.append(f"The bar axis starts at {lo}, not at zero.")
        chart = {"id": "g1", "loc": {"page": page, "figure": figure}, "type": kind,
                 "y_axis": {"min": str(lo), "max": str(hi), "scale": "linear", "unit": "thousands"},
                 "marks": marks, "notes": notes}  # fmt: skip
        self.charts.append(chart)
        self.truth["charts"].append({"figure": figure, "page": page, "axis": [lo, hi],
                                     "marks": [{"label": n, "value": v} for n, v in zip(labels, values, strict=True)]})  # fmt: skip

        stated = self._off(values[at], span) if text_error else values[at]
        text = f"{metric} reached {self.fmt(stated)} thousand in {labels[at]}."
        self.add(text)
        ident = self.num(self.fmt(stated), stated, 0, text, unit="thousands")
        self.chart_claim("text_vs_chart", f"The figure in the text should match the {labels[at]} mark in {figure}.",
                         chart="g1", target=ident, mark={"label": labels[at]})  # fmt: skip
        if text_error:
            self.mark("planted", "chart_text", self.fmt(stated), text)
        if with_labels:
            for i, label in enumerate(labels):
                shown = self.fmt(printed_labels[i])
                ident = self.num(
                    shown, printed_labels[i], 0, shown, unit="thousands", image=True, page=page
                )
                marks[i]["printed_label"] = ident
                self.chart_claim("label_vs_mark", f"The value label on the {label} bar should match its height.",
                                 chart="g1", target=ident, mark={"label": label})  # fmt: skip
                if label_error and i == at:
                    self.truth["planted"].append({"id": f"e{len(self.truth['planted']) + 1}", "type": "chart_label",
                                                  "page": page, "text": shown, "image": True})  # fmt: skip

    def costs(self) -> None:
        r = self.rng
        items = r.sample(COSTS, r.randint(3, 5))
        true = [F(r.uniform(8, 95), 3) for _ in items]
        total = rnd(sum(true), 1)
        planted = self.chance(0.25)
        if planted:
            total += r.choice([-1, 1]) * F(r.uniform(1.5, 4), 1)
        self.new_page()
        self.add("## Costs", "", "| Item | Cost (USD thousands) |", "| :--- | ---: |")
        self.pages[-1].pop()
        rows = []
        for name, value in zip(items, true, strict=True):
            shown = self.fmt(rnd(value, 1), 1)
            self.pages[-1].append(f"| {name} | {shown} |")
            rows.append(
                self.num(
                    shown, rnd(value, 1) * 1000, 1, f"{name} | {shown}", scale="1000", unit="USD"
                )
            )
        quote = f"Total | {self.fmt(total, 1)}"
        self.pages[-1].extend([f"| {quote} |", ""])
        ident = self.num(self.fmt(total, 1), total * 1000, 1, quote, scale="1000", unit="USD")
        self.claim(ident, op("sum", *rows), "The total cost should be the sum of the items.")
        # Rows are rounded, so an honest total may differ from their sum by the rounding.
        self.mark(
            "planted" if planted else "traps",
            "sum" if planted else "rounding",
            self.fmt(total, 1),
            quote,
        )

    def stacked_chart(self) -> None:
        r = self.rng
        online = [r.randint(40, 190) for _ in AREAS]
        stores = [r.randint(40, 190) for _ in AREAS]
        lo, hi, step = (
            0,
            (max(a + b for a, b in zip(online, stores, strict=True)) // 50 + 2) * 50,
            50,
        )
        figure, page = "Figure 2", self.page
        self.add(f"![{figure}: Sales by area and channel, thousands](figure2.png)")
        self.skipped.append(
            {"text": "2", "loc": {"page": page, "quote": figure}, "reason": "figure number"}
        )
        self.figures.append({"file": "figure2.png", "kind": "stacked", "title": "Sales by area and channel (thousands)",
                             "labels": AREAS, "values": [online, stores], "series": ["Online", "Stores"],
                             "axis": [lo, hi, step], "value_labels": None})  # fmt: skip
        marks, truth_marks = [], []
        for series, values in (("Online", online), ("Stores", stores)):
            for label, value in zip(AREAS, values, strict=True):
                read_a, read_b = self.reading(Fraction(value), Fraction(hi - lo))
                marks.append(
                    {
                        "label": label,
                        "series": series,
                        "read_a": read_a,
                        "read_b": read_b,
                        "printed_label": None,
                    }
                )
                truth_marks.append({"label": label, "series": series, "value": value})
        self.charts.append({"id": "g2", "loc": {"page": page, "figure": figure}, "type": "stacked_bar",
                            "y_axis": {"min": str(lo), "max": str(hi), "scale": "linear", "unit": "thousands"},
                            "marks": marks, "notes": []})  # fmt: skip
        self.truth["charts"].append(
            {"figure": figure, "page": page, "axis": [lo, hi], "marks": truth_marks}
        )
        at = r.randrange(len(AREAS))
        both = online[at] + stores[at]
        planted = self.chance(0.3)
        stated = self._off(both, hi - lo) if planted else both
        text = f"Online and store sales together reached {self.fmt(stated)} thousand in the {AREAS[at]} area."
        self.add(text)
        ident = self.num(self.fmt(stated), stated, 0, text, unit="thousands")
        self.chart_claim("parts_sum", f"The two segments of the {AREAS[at]} bar in {figure} should add up to the figure in the text.",
                         chart="g2", target=ident,
                         marks=[{"label": AREAS[at], "series": "Online"}, {"label": AREAS[at], "series": "Stores"}])  # fmt: skip
        if planted:
            self.mark("planted", "parts_sum", self.fmt(stated), text)

    def references(self, index: int) -> None:
        r = self.rng
        misquote = self.chance(0.3)
        words = QUOTE_ALTERED if misquote else QUOTE_TRUE
        self.add(f"IANA describes its example domains this way: “{words}” ({QUOTE_URL})")
        self.sources.append({"id": "s1", "kind": "quote", "value": QUOTE_URL, "quote": words,
                             "loc": {"page": self.page, "quote": "IANA describes its example domains this way"}})  # fmt: skip
        self.truth["sources"].append({"id": "s1", "kind": "quote", "value": QUOTE_URL, "planted": misquote,
                                      "type": "misquote" if misquote else "quote"})  # fmt: skip
        self.add("## References")
        works = [r.choice(REAL_WORKS)]
        missing = self.chance(0.4)
        if missing:
            works.append((f"10.5555/prove.synth.{index:04d}", "Okafor, T., & Lindqvist, A.", 2021,
                          "Reconciling quarterly service figures in small organisations"))  # fmt: skip
        else:
            works.append(next(w for w in REAL_WORKS if w != works[0]))
        for n, (doi, authors, year, title) in enumerate(works, start=1):
            line = f"[{n}] {authors} ({year}). {title}. doi:{doi}"
            self.add(line)
            self.skipped.append(
                {"loc": {"page": self.page, "quote": line}, "reason": "reference list entry"}
            )
            ident = f"s{n + 1}"
            self.sources.append({"id": ident, "kind": "doi", "value": doi, "cited_title": title, "cited_year": year,
                                 "loc": {"page": self.page, "quote": f"[{n}] {authors} ({year})."}})  # fmt: skip
            invented = doi.startswith("10.5555/")
            self.truth["sources"].append({"id": ident, "kind": "doi", "value": doi, "planted": invented,
                                          "type": "doi_missing" if invented else "doi"})  # fmt: skip
            if invented:  # what the registries answer for a DOI nobody registered
                for url in (f"https://api.crossref.org/works/{doi}", f"https://api.datacite.org/dois/{doi}",
                            f"https://doi.org/api/handles/{doi}"):  # fmt: skip
                    self.cache[url] = (404, "")

    # --- results ---------------------------------------------------------------------

    def markdown(self) -> str:
        head = [f"# {self.org} — Q3 2026 report", "",
                f"*{self.org} is fictional. Synthetic report for the Prove evaluation corpus.*", ""]  # fmt: skip
        pages = ["\n".join(lines).rstrip() for lines in self.pages]
        return "\n".join(head) + "\n\n---\n\n".join(pages) + "\n"

    def gold(self, path: str) -> dict:
        return {"schema": "prove.claims.v1", "document": {"path": path, "locale": self.locale},
                "numbers": self.numbers, "claims": self.claims, "charts": self.charts,
                "sources": self.sources, "skipped": self.skipped}  # fmt: skip


def op(name: str, *args) -> dict:
    return {"op": name, "args": [{"ref": a} if isinstance(a, str) else a for a in args]}


def build(seed: int, index: int) -> Report:
    """One report, fully determined by (seed, index)."""
    report = Report(seed, index)
    report.summary()
    report.regions()
    report.series_chart()
    report.costs()
    report.stacked_chart()
    report.references(index)
    return report


def draw(spec: dict, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lo, hi, step = spec["axis"]
    fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=150)
    if spec["kind"] == "line":
        ax.plot(spec["labels"], spec["values"], color="#3b6ea5", marker="o", linewidth=2)
    elif spec["kind"] == "stacked":
        bottom = [0] * len(spec["labels"])
        for values, name, color in zip(
            spec["values"], spec["series"], ("#3b6ea5", "#e39c37"), strict=True
        ):
            ax.bar(spec["labels"], values, bottom=bottom, label=name, color=color, width=0.55)
            bottom = [b + v for b, v in zip(bottom, values, strict=True)]
        ax.legend(frameon=False, fontsize=9)
    else:
        bars = ax.bar(spec["labels"], spec["values"], color="#3b6ea5", width=0.6)
        for bar, text in zip(bars, spec["value_labels"] or [], strict=False):
            ax.annotate(
                text,
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                ha="center",
                va="bottom",
                fontsize=9,
            )
    ax.set_ylim(lo, hi)
    ax.set_yticks(range(lo, hi + 1, step))
    ax.yaxis.grid(True, color="#cccccc", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(spec["title"], fontsize=11)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, metadata={"Software": None})
    plt.close(fig)


def write_cache(cache: dict[str, tuple[int, str]], folder: Path) -> None:
    """Registry answers for invented DOIs, in the format of the source client's cache."""
    from provecheck.sources.client import Client

    folder.mkdir(parents=True, exist_ok=True)
    client = Client(folder)
    for url, (status, body) in cache.items():
        record = {"url": url, "status": status, "body": body}
        client._path(url).write_text(json.dumps(record) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--out", default=str(ROOT / "evals" / "corpus"))
    parser.add_argument("--no-render", action="store_true", help="skip figures and PDFs")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "tools"))
    out = Path(args.out)
    planted = traps = 0
    for index in range(1, args.n + 1):
        report = build(args.seed, index)
        folder = out / report.name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "report.md").write_text(report.markdown(), encoding="utf-8", newline="\n")
        rel = (
            (folder / "report.md").resolve().relative_to(ROOT).as_posix()
            if out.resolve().is_relative_to(ROOT)
            else "report.md"
        )
        for name, data in (("truth.json", report.truth), ("claims.gold.json", report.gold(rel))):
            (folder / name).write_text(
                json.dumps(data, indent=1, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        if not args.no_render:
            import mdpdf

            for spec in report.figures:
                draw(spec, folder / spec["file"])
            mdpdf.render(folder / "report.md", folder / "report.pdf")
        planted += len(report.truth["planted"]) + sum(s["planted"] for s in report.truth["sources"])
        traps += len(report.truth["traps"])
    print(
        f"corpus {CORPUS_VERSION}, seed {args.seed}: {args.n} reports, {planted} planted errors, {traps} traps -> {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
