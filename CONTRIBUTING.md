# Contributing to Prove

Thanks for looking. Prove is built so that the most useful contributions are small:
one file, one test, one pull request.

## Set up

```bash
git clone https://github.com/enestanerr/prove && cd prove
uv sync --all-extras
uv run pytest -q                       # no network needed
uv run ruff check . && uv run ruff format --check .
uv run python reference/test_reference.py   # must print 10/10 passed
uv run python evals/run_judge.py            # must print "false alarms: 0"
```

## The rules that do not bend

- **Verdicts come from code.** Nothing in the skill, the report or the docs states a
  verdict that `provecheck` did not compute.
- **No false alarms from rounding.** `contradicted` means impossible under any rounding
  of what is printed. When in doubt the answer is `suspect` or `unverified`.
- **Never loosen a rule to make a test or an eval pass.** Fix the code, or fix the test
  and say why.
- **The core is standard library only.** Optional features import their dependency when
  they are used.
- **No network in tests.**
- `docs/SPEC.md` is the contract. If you change behaviour, change the spec in the same
  pull request.

## Add a relation in one file

A relation says how a printed number should be computed. Here is `median`, start to
finish.

**1. Create `src/provecheck/relations/median.py`:**

```python
"""median: the middle value of a1 ... an."""

from provecheck.intervals import Interval
from provecheck.relations import Value, relation, same_kind


@relation("median", min_args=1, template="median({,})", summary="the middle value of a1 ... an")
def median(args: list[Value]) -> Value:
    kind = same_kind(args, "median")

    def middle(xs):
        xs = sorted(xs)
        mid = len(xs) // 2
        return xs[mid] if len(xs) % 2 else (xs[mid - 1] + xs[mid]) / 2

    # The median is monotone in every operand, so the bounds are the medians of the bounds.
    rng = Interval(middle(a.range.lo for a in args), middle(a.range.hi for a in args))
    return Value(middle(a.point for a in args), rng, kind)
```

The function returns two things: the **point** (computed from the printed values) and
the **range** (what the printed values allow, given their rounding). The decorator
registers it; nothing else needs to know.

**2. Add `tests/test_relation_median.py`:**

```python
from fractions import Fraction as F

from helpers import op, quick

from provecheck import CONTRADICTED, VERIFIED


def test_median_of_printed_values():
    v = quick(
        "values 3, 9 and 4 have a median of 4",
        {"a": "3", "b": "9", "c": "4", "t": "4"},
        "t",
        op("median", "a", "b", "c"),
        exact={"a", "b", "c", "t"},
    )
    assert v["verdict"] == VERIFIED


def test_wrong_median_is_contradicted():
    v = quick(
        "values 3, 9 and 4 have a median of 9",
        {"a": "3", "b": "9", "c": "4", "t": "9"},
        "t",
        op("median", "a", "b", "c"),
        exact={"a", "b", "c", "t"},
    )
    assert v["verdict"] == CONTRADICTED
```

Add `"median"` to the `RATIONAL` list in `tests/test_relations.py` and the three
property tests there run on it for free: the point is inside the range, widening an
operand never shrinks the range, exact operands give a zero-width range.

**3. Document it:** one row in the table in `docs/SPEC.md` §4 and one in
`plugin/skills/prove/reference/claims-schema.md`. Then `uv run python tools/build_pyz.py`
so the zipapp in the plugin carries it.

The interval is the part to get right. If your relation is not monotone in an operand,
compute the range from interval arithmetic (`a.range + b.range`, `/`, `*`) rather than
from end points. A range that is too wide costs recall; a range that is too narrow
causes a false alarm, and that is the one bug this project cannot have.

## Other one-file contributions

| What | Where | Test with |
| :- | :- | :- |
| A source resolver (PubMed, OpenAlex, ISBN, …) | `src/provecheck/sources/<kind>.py`, one line in `_resolvers()` | recorded answers in `tests/fixtures/sources/cache`, see `tools/record_source_fixtures.py` |
| A number format or locale (lakh/crore, Arabic-Indic digits, …) | `src/provecheck/numbers.py` | a row in `PARSE_CASES` in `tests/test_numbers.py` |
| An ingest format (DOCX, PPTX, ODS, LaTeX) | `src/provecheck/ingest/<format>.py` | a small fixture file and a test in `tests/test_ingest.py` |
| An example document | `examples/<name>/` with `report.md`, `claims.json`, `truth.json` | `uv run python tools/build_examples.py`; add the name to `tests/golden/test_examples.py` |

## Reporting a wrong verdict

A wrong verdict is the most valuable bug report. Please include the sentence or table
from the document, the claim from `claims.json`, and what `provecheck` printed.

The order of work is fixed: the case goes into the judge eval or a test first, failing;
then the fix; then a release the same day. Tolerances are never widened to hide a false
alarm. The question is always why the claim was mis-specified or why the rule was
wrong.

## Style

- Exact arithmetic: `fractions.Fraction` in the core, no floats until display.
- Public names in English. Verdict strings are lowercase.
- User-facing text: plain sentences, the computation shown, no jargon.
- Small commits with messages that say what changed and why. Add a line to
  `CHANGELOG.md`.

By contributing you agree that your work is released under the MIT licence, and to
follow the [Code of Conduct](CODE_OF_CONDUCT.md).
