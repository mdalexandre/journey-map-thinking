# Privacy Policy

## Local-first, zero telemetry

`journey-map-thinking` is a local-first tool. It:

- Reads and writes files on your local filesystem only.
- Makes no network requests.
- Sends no telemetry, analytics, or usage data anywhere.
- Does not read, store, or transmit personal information.

## What is stored locally

The global map under `~/.journey_map/` (or your `JOURNEY_MAP_ROOT`) stores:

- `journey_history.jsonl`: append-only log of pipeline runs (lane, milestone,
  progress signals, run ID). Contains whatever raw goal text you pass in.
- `current_position.md`: the most recent pipeline position.
- `component_levels.json`, `next_unlocks.json`: derived state from your runs.

None of these files are sent anywhere. They exist only on your machine.

## Do not commit private history

If you use `journey-map-thinking` on a private project, do not commit
`journey_history.jsonl` or other pipeline run files to a public repository.
The `.gitignore` in this template excludes `*.jsonl` and `pipeline_runs/`.

## JSON-in/JSON-out

The pipeline is JSON-in, JSON-out. Every artifact file is plain JSON or
markdown that you control. You can inspect, delete, or archive them at any time.

## No PII in the package itself

The `journey_map/` package source contains no personal information, email
addresses, usernames, API keys, or private paths.
