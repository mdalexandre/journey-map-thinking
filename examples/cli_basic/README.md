# CLI Basic Example

Runs the full 5-stage pipeline on a fake build goal using the default lane
catalog.

## Usage

```bash
cd examples/cli_basic
bash run.sh
```

## What it does

1. `jm position`: routes the goal "build a data pipeline for CSV ingestion"
   to the "build" lane.
2. `jm select-lane`: selects the first milestone for the build lane.
3. `jm align-gate`: aligns the planner gate (required tests, blocked claims).
4. `jm progress --tests-added`: records progress (tests-added is the evidence).
5. `jm update`: writes the update markdown and appends to the history log.

## Expected output

The update markdown appears at the end of the run, showing PROGRESS status and
the next unlock step.
