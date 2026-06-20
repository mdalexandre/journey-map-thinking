# Changelog

## Unreleased (0.2.0-dev)

### Fixed (round 2)

- README Quickstart: replaced broken `pip install journey-map-thinking` (not on PyPI)
  with a `git clone ... && pip install -e .` local editable install, so a genuine
  fresh user can actually install the package.
- `tests/test_cli.py` line 201: split long tuple (104 chars) across multiple lines
  to satisfy the E501 ruff rule (max 100 chars).
- `tests/test_runner.py` line 4: removed unused `import pytest` (ruff F401).

### Added

- `journey_map.run(goal, *, catalog=None, run_id="run")`: single-call convenience
  function that chains position() -> select_lane() -> align_gate() and returns a
  `JourneyRunResult` dataclass with flat fields (`relevance`, `lane`, `next_move`,
  `target_gate`, `can_advance_now`) plus the underlying stage objects and a
  `summary()` method returning 4 to 6 plain-English lines.
- `journey_map.JourneyRunResult`: exported in `__all__`.
- `jm run "<goal>"` CLI subcommand: orientation shortcut with `--catalog FILE`,
  `--out DIR` (writes the 3 intermediate JSON artifacts), and `--json` flag.
- `tests/test_runner.py`: 15 unit and integration tests for `run()` and
  `JourneyRunResult`.
- 10 new CLI tests in `TestJmRunSubcommand` class in `tests/test_cli.py`.
- README rewritten to lead with a 30-second Quickstart section (real output
  pasted from actual run) followed by the existing advanced pipeline content.
- `CHANGELOG.md` (this file).

### Changed

- `journey_map/__init__.py`: `run` and `JourneyRunResult` added to `__all__`
  (purely additive).
- `journey_map/cli.py`: `run` subcommand added to `build_parser()` (additive).
- `README.md`: Quickstart section now leads; existing content moved under
  "Advanced: the full pipeline". "What this does NOT claim" preserved verbatim
  (delta = 0.000, p = 1.000).

### Not changed

- All 5 existing pipeline functions: `position`, `select_lane`, `align_gate`,
  `check_progress`, `update_map`.
- All 6 existing CLI subcommands: `position`, `select-lane`, `align-gate`,
  `progress`, `update`, `seed`.
- `pyproject.toml` dependencies (still `[]`).
- No new external dependencies.
