---
name: prove
description: >-
  Audit a document claim by claim: recompute every number, read charts back against
  the text, and check that cited sources exist. Use when the user asks to audit, verify,
  fact-check or sanity-check a report, PDF, deck, spreadsheet or draft; asks whether the
  numbers add up; or is about to send a document that contains figures, charts or
  citations. Verdicts are computed by a bundled script, not by the model.
license: MIT
compatibility: Needs Python 3.10 or later for the bundled provecheck.pyz. PDF text and chart crops need PyMuPDF (pip install pymupdf), which is optional.
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/provecheck.pyz *) Bash(python ${CLAUDE_SKILL_DIR}/scripts/provecheck.pyz *) Bash(py -3 ${CLAUDE_SKILL_DIR}/scripts/provecheck.pyz *)
---

# Prove

You read the document and propose checks. `provecheck` decides every verdict.

`PROVE` below means `python3 ${CLAUDE_SKILL_DIR}/scripts/provecheck.pyz`.
If `${CLAUDE_SKILL_DIR}` is not replaced by a path where you read this, it is the folder
that holds this `SKILL.md`.

- If `python3` is missing or fails (on Windows it is often only a Store shortcut), run
  the very same command with `python`, and if that fails too, with `py -3`. Do not
  search the machine for an interpreter.
- Write the full path in every command: do not store it in a shell variable. Run one
  `PROVE` command per call. Quote the path if it contains spaces.
- Open the `reference/` files with your file-reading tool and write `claims.json` with
  your file-writing tool, not with `cat` or a shell heredoc.

## Rules you must not break

1. Never state a verdict that `provecheck` did not print. Never change one. Do not call
   a claim wrong, right, fine or suspicious on your own judgement.
2. Copy numbers exactly as printed, with the sentence or table row they sit in. Do not
   correct, round, reformat or convert them.
3. A number is rounded unless you can name why it is exact: `count`, `ledger`, `defined`
   or `cell`.
4. If you cannot say how a number should be computed, do not invent a derivation. Leave
   it without a claim.
5. Every number in the document ends up either in `numbers` or in `skipped` with a
   reason. Run the coverage step and go back for anything missed.
6. Do not fix the document, and do not edit `verdicts.json` or the reports.

## Steps

Work in a folder named `prove-work/` in the current directory. `DOC` is the user's file.

1. **Ingest.** `PROVE ingest DOC -o prove-work/doc.json --render-pages prove-work/pages`
   If it says PDF support is missing, try `pip install pymupdf` once. If that is not
   possible, read the file with your own tools, skip `--doc` in step 4, and tell the
   user that numbers could not be grounded, so nothing can be reported as contradicted.
2. **Scan.** `PROVE scan prove-work/doc.json` lists every numeric token with its page.
   This is your checklist for rule 5. `PROVE text prove-work/doc.json` prints the text
   of each page: copy your quotes from it.
3. **Read and write `prove-work/claims.json`.** First read
   `reference/claims-schema.md` in this skill's folder: it defines every field. Then
   read the document itself (and the page images for a PDF) and record:
   - Derived numbers: totals, differences, shares, growth rates, averages, CAGR, ranks.
     When the parts are printed, compute a share from the sum of the parts, not from a
     printed total that is itself being checked.
   - Cross-references: the same quantity printed in two places (`eq`).
   - Charts: only after reading `reference/charts.md`. Read each mark twice, the second
     time from a 2× crop made with `PROVE crop`. Give an honest interval, not a point.
   - Sources: DOIs, arXiv ids, URLs, and any direct quotation with its source.
   - Everything else numeric goes in `skipped` with a reason (year, page number, …).
   Page numbers and quotes must match what `PROVE text` printed, not your memory.
4. **Check.** `PROVE check prove-work/claims.json --doc prove-work/doc.json`
   It prints the verdicts and writes `prove-work/verdicts.json`. If it reports schema
   errors, `not-grounded`, `parse-mismatch`, `unit-mismatch`, `scale-mismatch` or missed
   numbers, the cause is usually in *your* claims file: fix the file and run it again.
   Never fix it by changing what the document says. Stop when what remains is true of
   the document.
5. **Sources.** `PROVE sources prove-work/claims.json` if the file lists any. Without
   network access add `--offline` and tell the user sources were not checked.
6. **Report.** `PROVE report prove-work/verdicts.json --html --md --card`
   Exit code 1 here means at least one claim is contradicted. It is a finding, not a
   failure.
7. **Tell the user**, in this order:
   - how many claims were contradicted, then each one in a sentence with the
     computation, copied from what `provecheck` printed;
   - the suspect claims, each with its possible range;
   - the coverage line, and how many numbers were missed if any;
   - what was not checked and why (unverified claims, sources when offline, charts
     that could not be read);
   - the path of `prove-work/prove-report.html`.

## What to say about each verdict

- **contradicted**: "This cannot be right under any rounding." Show the numbers.
- **suspect**: "This only works if the inputs sit at the edge of their rounding." Show
  the range.
- **unverified**: "Not checked", with the reason. Never present it as a problem with
  the document.
- **verified**: mention the count; list them only if asked.

Chart verdicts rest on your reading of the image, and the report tags them `read`.
Say so, and keep them apart from the computed ones in your summary.

A clean report means the checked claims passed. Say how many were checked.

## More detail, loaded when needed

- `reference/claims-schema.md` — the claims file, field by field, with the list of
  relations and what each `unverified` reason means. Read before step 3.
- `reference/charts.md` — how to read a chart for Prove. Read before any chart claim.
- `reference/examples.md` — two complete worked examples.
