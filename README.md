# journey-map-thinking

A deterministic, no-LLM journey map thinking layer for agent pipelines.

It locates a task on a configurable lane catalog, selects a lane, aligns the
planner gate, checks for REAL progress (refusing summary-only runs), and updates
a persistent global map. JSON-in, JSON-out. Zero hard dependencies.

## Quickstart (30 seconds)

This package is not yet published on PyPI. Install from source:

```bash
git clone https://github.com/mdalexandre/journey-map-thinking.git
cd journey-map-thinking
pip install -e .
```

Then run:

```bash
jm run "fix the failing auth test"
```

Actual output:

```
Goal relevance: high
Lane: fix
Next move: root cause identified
Gate: test passes
Can advance now: yes
honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
```

Python equivalent:

```python
from journey_map import run

r = run("fix the failing auth test")
print(r.summary())
```

## Refuse fake progress

`jm run` is an orientation tool: it tells you which lane you are in and what the
next concrete move is. It does not record progress. `jm progress` is the progress
gate and exits non-zero on a summary-only run, requiring at least one real evidence
signal (changed files, tests added, a release verdict) before `progress_made` is
set to True.

## Who this is for

Teams building agent pipelines who want structured state tracking without
hallucinated progress. The pipeline is a thin layer that:
- routes tasks to lanes (build, research, fix, blocked, vision, or your own),
- enforces a no-fake-progress gate (exits 1 when no evidence is present),
- writes append-only history and a readable current position.

## Advanced: the full pipeline

### 5-stage CLI pipeline

```bash
jm position   --raw raw_goal.txt --output journey_position.json
jm select-lane --position journey_position.json --output journey_lane.json
jm align-gate  --lane journey_lane.json --output journey_gate_alignment.json
jm progress    --lane journey_lane.json --output journey_progress_check.json \
               --tests-added
jm update      --progress journey_progress_check.json --lane journey_lane.json \
               --output journey_map_update.md
```

### Python API

```python
from journey_map import position, select_lane, align_gate, check_progress, update_map

pos  = position("build a CSV ingestion pipeline")
sel  = select_lane(pos)
gate = align_gate(sel)
chk  = check_progress(sel, changed_files=["ingestion.py"], tests_added=True)
md   = update_map(chk, sel)
print(md)
```

### `jm run` flags

| Flag | Meaning |
|---|---|
| `jm run "<goal>"` | Print prose orientation to stdout (exit 0). |
| `--catalog FILE` | Load a custom lane catalog (JSON or YAML). |
| `--out DIR` | Write `journey_position.json`, `journey_lane.json`, `journey_gate_alignment.json` into DIR. |
| `--json` | Print machine-readable JSON instead of prose. |

## Custom lane catalog

Replace the default 5 lanes with your own by passing `--catalog my_lanes.json`
(CLI) or `load_catalog("my_lanes.json")` (Python API).

```bash
jm position --raw raw_goal.txt --catalog my_lanes.json --output pos.json
```

See `docs/lane_catalog.md` for the JSON format and `examples/custom_lane_catalog/`
for a working example.

## No-fake-progress gate

`jm progress` exits 1 when no real evidence signal is present:

```bash
jm progress --lane journey_lane.json --output check.json
echo "exit=$?"  # exit=1 when no evidence
```

Evidence signals: `--tests-added`, `--dogfood-ran`, `--release-verdict`, a
non-empty `--generator-log` reporting changed files, or a `release_verdict.json`
with a PASS verdict. At least one must be present for progress_made to be True.

## Resume pattern

Save `journey_position.json` between runs and restart from `jm select-lane` to
avoid re-deriving the position. This is structured state persistence, not a
proven improvement. See `examples/resume_pattern/` and the honesty note there.

## Global map

The global map is stored under `~/.journey_map/` by default. Override with:

```bash
export JOURNEY_MAP_ROOT=/my/project/.jm
```

Or pass `--global-root` to any CLI command that writes to the map.

## What this does NOT claim

- It does NOT claim to improve next-action quality over a plain summary.
  The 96-trial comparison produced delta = 0.000, p = 1.000 on that metric.
  See `docs/research_result.md` for the full honest null result.
- It does NOT make network calls, spawn subprocesses, or require API keys.
- The milestones labeled M01-M11 in earlier design documents are future work,
  not completed features.

## Documentation

- `docs/quickstart.md`: full quickstart guide.
- `docs/lane_catalog.md`: default lanes and custom catalog format.
- `docs/cli.md`: full CLI reference.
- `docs/python_api.md`: Python API reference.
- `docs/research_result.md`: honest null result (96 trials, p=1.000).

## Examples

- `examples/cli_basic/`: full 5-stage CLI example with fake data.
- `examples/python_basic/`: Python API example.
- `examples/resume_pattern/`: resume from saved position.
- `examples/custom_lane_catalog/`: custom lane catalog.
- `examples/research_reproduction/`: stub for reproducing the study design.

## License

MIT. See `LICENSE`.
