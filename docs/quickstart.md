# Quickstart

## Install

```bash
pip install journey-map-thinking
```

## 5-stage CLI pipeline

Given a raw goal file:

```bash
echo "build a CSV ingestion pipeline" > raw_goal.txt

jm position --raw raw_goal.txt --output journey_position.json
jm select-lane --position journey_position.json --output journey_lane.json
jm align-gate --lane journey_lane.json --output journey_gate_alignment.json
jm progress --lane journey_lane.json --output journey_progress_check.json --tests-added
jm update --progress journey_progress_check.json --lane journey_lane.json \
    --output journey_map_update.md
```

## Python API

```python
from journey_map import position, select_lane, align_gate, check_progress, update_map

pos = position("build a CSV ingestion pipeline")
sel = select_lane(pos)
gate = align_gate(sel)
chk = check_progress(sel, changed_files=["ingestion.py"], tests_added=True)
md = update_map(chk, sel)
print(md)
```

## Custom lane catalog

```bash
jm position --raw raw_goal.txt --catalog my_lanes.json --output journey_position.json
```

Or via environment variable:

```bash
export JOURNEY_MAP_CATALOG=my_lanes.json
jm position --raw raw_goal.txt --output journey_position.json
```

## No-fake-progress gate

`jm progress` exits 1 when no real progress signal is present:

```bash
jm progress --lane journey_lane.json --output check.json
echo "exit=$?"  # prints exit=1 when no evidence
```

This is intentional. The gate prevents summary-only runs from recording progress.

## Global map

The global map stores history under `~/.journey_map/` by default.
Override with `--global-root` or `JOURNEY_MAP_ROOT`.

```bash
jm seed --global-root /tmp/my_map
```

See `docs/cli.md` for full flag reference.
