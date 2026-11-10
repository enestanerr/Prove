# Notes on this run

Command:

```
uv run python evals/synth/generate.py --seed 1 --n 30 --out evals/corpus
uv run python evals/run_e2e.py --model claude-sonnet-5-5 --effort medium --n 30 --jobs 3
```

Machine: Windows 11, Claude Code 2.1.319, PDFs as input.

## Two documents were run twice

`doc-012` and `doc-013` did not start on the first attempt. On this machine `python3` is
only the Microsoft Store shortcut. The skill said to use `python` instead, but in these
two runs Claude tried to find an interpreter with compound shell commands, which the
permission mode refused, and it stopped without auditing. The records of those attempts
are kept as `run.first-attempt.json`.

The skill text was then made explicit ("run the very same command with `python`, then
`py -3`; do not search the machine for an interpreter") and the two documents were run
again with `--resume`. The other 28 documents ran with the earlier wording. Nothing
about what is checked or how it is judged changed between the two attempts.

## Things to know when reading the numbers

- `pp_vs_pct` is the weak row. The corpus writes "improved from 46.4% to 52.0%, an
  increase of 5.6%". Claude usually reads that as a gain in points and proposes
  `pp_diff`, which is verified, instead of the relative change the planted error is
  about. The judge is given no claim to contradict.
- Chart marks: the corpus draws 300 marks. Claude read 106 of them, the ones its claims
  needed. All 106 final readings contain the true value.
- Cited sources were resolved live against Crossref, DataCite, doi.org and the quoted
  page.
- Sessions load the user's own global `CLAUDE.md`; `--setting-sources project` does not
  exclude it. It had no visible effect on claims or verdicts.
- Transcripts and the answers Claude gave are kept locally and are not committed,
  because they contain local paths.
