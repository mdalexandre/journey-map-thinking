# Python Basic Example

Runs the full 5-stage pipeline via the Python API with fake data.

## Usage

```bash
python examples/python_basic/run.py
```

## What it does

Calls all five pipeline functions in sequence:
`position`, `select_lane`, `align_gate`, `check_progress`, `update_map`.

Uses fake evidence (a changed file and tests-added) to demonstrate the
progress gate passing.
