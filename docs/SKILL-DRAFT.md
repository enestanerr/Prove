# Skill and plugin drafts

Starting points. **Verify every field against the live docs before committing**
(`https://code.claude.com/docs/llms.txt` → plugins, components, marketplace reference,
skills, hooks). Then run `claude plugin validate ./plugin --strict`.

## `plugin/skills/prove/SKILL.md`

```markdown
---
name: prove
description: >-
  Audit a document claim by claim: recompute every number, read charts back against
  the text, and check that cited sources exist. Use when the user asks to audit, verify,
  fact-check or sanity-check a report, PDF, deck, spreadsheet or draft; asks whether the
  numbers add up; or is about to send a document that contains figures, charts or
  citations. Verdicts are computed by a bundled script, not by the model.
---

# Prove

You read the document and propose checks. `provecheck` decides every verdict.

`PROVE` below means `python3 <this skill's folder>/scripts/provecheck.pyz`.
In a Claude Code plugin that folder is `${CLAUDE_PLUGIN_ROOT}/skills/prove`.

## Rules you must not break

1. Never state a verdict that `provecheck` did not print. Never change one.
2. Copy numbers exactly as printed, with the sentence they sit in. Do not correct,
   round or reformat them.
3. A number is rounded unless you can name why it is exact: `count`, `ledger`,
   `defined` or `cell`.
4. If you cannot say how a number should be computed, do not invent a derivation.
   Leave it without a claim; it will show as unverified.
5. Every number in the document ends up either in `numbers` or in `skipped` with a
   reason. Run the coverage step and go back for anything missed.

## Steps

1. **Ingest.** `PROVE ingest <file> -o work/doc.json --render-pages work/pages`
   If PDF support is missing, read the file with your own tools and say so in the report.
2. **Scan.** `PROVE scan work/doc.json` lists every numeric token. Keep the list open.
3. **Read and write `work/claims.json`.** Follow `reference/claims-schema.md`.
   - Derived numbers: totals, differences, shares, growth rates, averages, CAGR.
   - Cross-references: the same quantity printed in two places.
   - Charts: follow `reference/charts.md`. Read each mark twice, the second time from a
     2× crop made with `PROVE crop`. Give an honest interval, not a point.
   - Sources: DOIs, arXiv ids, URLs, and any direct quotation with its source.
4. **Check.** `PROVE check work/claims.json --doc work/doc.json -o work/verdicts.json`
   Fix schema or grounding errors it reports about *your* file. Do not touch verdicts.
5. **Sources.** `PROVE sources work/claims.json` (skip with `--offline` if there is no
   network, and tell the user they were not checked).
6. **Report.** `PROVE report work/verdicts.json --html --md --card`
7. **Tell the user**, in this order: how many claims were contradicted, each one in a
   sentence with the computation, then suspects, then the coverage line. Link the HTML
   report. Say what was not checked.

## What to say about each verdict

- contradicted: "This cannot be right under any rounding." Show the numbers.
- suspect: "This only works if the inputs sit at the edge of their rounding." Show the range.
- unverified: "Not checked", with the reason. Never present it as a problem.

A clean report means the checked claims passed. Say how many were checked.
```

Keep `SKILL.md` under ~150 lines. Put the schema walkthrough, the chart-reading
protocol and two full examples in `reference/*.md` so they load only when needed.

## `plugin/.claude-plugin/plugin.json`

```json
{
  "name": "prove",
  "displayName": "Prove",
  "version": "0.1.0",
  "description": "Audit every checkable claim in a document. Numbers are recomputed by code, charts are read back against the text, sources are resolved. One verdict per claim.",
  "author": { "name": "enestanerr", "url": "https://github.com/enestanerr" },
  "homepage": "https://github.com/enestanerr/prove",
  "repository": "https://github.com/enestanerr/prove",
  "license": "MIT",
  "keywords": ["verification", "fact-checking", "numbers", "charts", "citations", "audit"]
}
```

For the Anthropic directory listing, the docs name extra fields (`icon`,
`documentationUrl`, `supportUrl`, `privacyPolicyUrl`, `termsOfServiceUrl`). Add them
when submitting; check the minimum Claude Code version they require so `--strict` does
not fail for users on older versions.

## `.claude-plugin/marketplace.json` (repo root)

```json
{
  "name": "enestanerr",
  "owner": { "name": "enestanerr" },
  "plugins": [
    {
      "name": "prove",
      "source": "./plugin",
      "description": "Audit every checkable claim in a document. Verdicts by code."
    }
  ]
}
```

## Install paths to document in the README (test each one before launch)

| Where | How |
| :- | :- |
| Claude Code | `/plugin marketplace add enestanerr/prove` then `/plugin install prove@enestanerr` |
| Other agents (Codex, Cursor, …) | `npx skills add enestanerr/prove` |
| claude.ai / Cowork | upload `prove-skill.zip` from the latest release as a skill; code execution must be on |
| CLI / CI | `uvx provecheck …` or `pipx install provecheck` |

Decide the invocation name after reading the components page. The goal is that a user
can type something short (`/prove` or `/prove:prove`) and that plain requests such as
"audit this report" trigger the skill through its description.

## Gate (v0.2)

An opt-in hook that reminds Claude to audit a deliverable before finishing a turn:

- Event: `Stop` (verify the current name and the block/continue contract in the hooks
  docs).
- Script: looks at files written in the turn; if any is a document type and contains
  numeric tokens with no fresh `prove-report.json` beside it, returns the message "Run
  the prove skill on <file> before finishing."
- Off by default. A boolean `userConfig` value turns it on. No `options` field.
- It must be fast (< 300 ms) and must never block more than once per file per turn.
