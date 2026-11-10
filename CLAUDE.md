# Prove — instructions for Claude Code

You are building **Prove**: an open-source skill + plugin + Python CLI that audits every
checkable claim in a document (numbers, charts, sources, later logic) and returns a
verdict per claim. The model proposes what to check; **code decides the verdict**.

Owner: Enes (GitHub `enestanerr`). Repo: `enestanerr/prove`. PyPI/CLI name: `provecheck`.
License: MIT. Python 3.10+.

## Read before you write code

1. `PLAN.md` — phases, order, definition of done for each phase.
2. `docs/SPEC.md` — the claims file, the verdict rule, every check. This is the contract.
3. `docs/ARCHITECTURE.md` — repo layout, modules, packaging.
4. `docs/SKILL-DRAFT.md` — drafts of `SKILL.md`, `plugin.json`, `marketplace.json`.
5. `reference/` — a tiny tested reference of the verdict rule. The product code must
   reproduce every result in `reference/test_reference.py`.

Work one phase at a time, in order. Do not start a phase until the previous phase's
definition of done passes. If a phase is running late, apply the cut lines in `PLAN.md`
instead of weakening a check.

## Non-negotiables

- **Verdicts come from code.** Nothing in the skill, the report or the README may state a
  verdict that `provecheck` did not compute. The model never edits a verdict.
- **No false alarms from rounding.** A claim is `contradicted` only when the intervals in
  `docs/SPEC.md` §2 are disjoint. When in doubt the verdict is `suspect` or `unverified`,
  never `contradicted`.
- **Ground every operand.** A number the model reports must be found, as printed, at the
  location it gives. If it is not found, the claim is `unverified`.
- **Never loosen a rule to make a test or an eval pass.** If a test fails, fix the code or
  fix the test with a written reason. Report eval numbers as measured, including bad ones.
- **Core stays stdlib-only.** Number parsing, intervals, relations, grounding, scan and
  verdicts import nothing outside the standard library. Extras (`pdf`, `xlsx`, `logic`)
  are optional and imported lazily.
- **No network in tests.** Source resolvers are tested against recorded fixtures.
- **Never publish, push, tag, or post without Enes saying so in the session.**

## External formats change — verify, don't recall

Claude Code's plugin, skill, hook and marketplace formats change often. Before writing
or editing `plugin.json`, `marketplace.json`, `hooks.json` or `SKILL.md` frontmatter:

1. Fetch `https://code.claude.com/docs/llms.txt` and open the current pages for plugins,
   plugin components, marketplace reference, hooks, skills and plugin evals.
2. Follow what the live docs say over anything in this package.
3. Run `claude plugin validate ./plugin --strict` and fix every message.

Known constraints checked on 10 Nov 2026 (re-verify):
- Only `plugin.json` lives in `.claude-plugin/`; components sit at the plugin root.
- A `CLAUDE.md` at a plugin root triggers a validate warning, so the plugin lives in
  `./plugin/`, not at the repo root.
- A plugin with a top-level `bin/` directory is not installable on claude.ai or Cowork.
  Do not create `bin/`.
- Plugin names starting with `claude-` or `anthropic-` are rejected. Ours is `prove`.
- `userConfig` fields with `options` stop older Claude Code versions loading the plugin.
  Use plain boolean/string fields.

## Commands

```bash
uv sync --all-extras          # set up
uv run pytest -q              # tests (no network)
uv run ruff check . && uv run ruff format --check .
uv run python -m provecheck --help
uv run python tools/build_pyz.py        # builds plugin/scripts/provecheck.pyz
python3 reference/test_reference.py     # verdict-rule reference, must stay 10/10
claude plugin validate ./plugin --strict
claude --plugin-dir ./plugin            # try the plugin locally
```

## Conventions

- Exact arithmetic: `fractions.Fraction` everywhere in the core. No floats until display.
- Public names in English. Verdict strings are lowercase:
  `verified`, `contradicted`, `suspect`, `unverified`, `skipped`.
- Every relation and every resolver is one small module with its own tests, so outside
  contributors can add one in a single pull request.
- Property-based tests (Hypothesis) for interval arithmetic and number parsing.
- User-facing text in the report: plain sentences, the computation shown, no jargon.
- Commit small, with messages that say what changed and why. Keep a `CHANGELOG.md`.

## Done means

A task is done when: tests pass, `ruff` is clean, the reference test is 10/10, the
relevant section of `docs/SPEC.md` still matches the code (update the spec in the same
commit if behaviour changed on purpose), and you have run the thing end to end once.
Say plainly what you did not verify.
