# Contributing

## Setup

```bash
git clone <your-fork>
cd journey-map
pip install -e '.[dev]'
```

## Before opening a PR

1. Run the linter: `ruff check journey_map/ tests/`
2. Run type checking: `mypy journey_map/`
3. Run tests: `pytest tests/ -q`
4. Run the CI privacy grep step locally to confirm no private tokens:
   ```bash
   # The full pattern and the files it checks are defined in .github/workflows/ci.yml.
   # Run the privacy step there, or use the test suite: pytest tests/test_security_privacy.py
   ```
5. All examples must use fake data only (no real names, paths, or keys).

## Adding lanes

To add lanes to the default catalog, edit `journey_map/lanes.py`. Add the lane
to `_DEFAULT_LANES`, update `MATCH_PRIORITY`, and add tests in
`tests/test_lanes.py`.

To document a custom catalog format, update `docs/lane_catalog.md`.

## Adding tests

One test per new behavior. Use `tmp_path` (pytest fixture) for file I/O.
Use fake goals and fake project names in all fixtures.

## Commit style

Short subject line (under 72 chars), imperative mood. Reference an issue if one
exists. No emojis in commit messages.

## PR checklist

- [ ] All tests pass.
- [ ] Ruff reports no issues.
- [ ] Mypy reports no issues.
- [ ] Privacy grep returns 0.
- [ ] New behavior is covered by at least one test.
- [ ] Docs updated if the public API changed.
