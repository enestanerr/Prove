## What this changes

<!-- One or two sentences. Link the issue if there is one. -->

## Checks

- [ ] `uv run pytest -q` passes (no network)
- [ ] `uv run ruff check . && uv run ruff format --check .` is clean
- [ ] `uv run python reference/test_reference.py` prints `10/10 passed`
- [ ] `uv run python evals/run_judge.py` prints `false alarms: 0`
- [ ] `uv run python tools/build_pyz.py` was run if anything under `src/` changed
- [ ] `docs/SPEC.md` is updated if behaviour changed on purpose
- [ ] A line in `CHANGELOG.md`

## If this touches a verdict

<!-- Say which claims change verdict and why. A change may move a verdict away from
     `contradicted`; it must never create a false alarm. For a wrong-verdict fix, the
     failing case was added first. -->
