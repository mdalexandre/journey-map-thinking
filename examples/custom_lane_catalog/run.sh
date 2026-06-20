#!/usr/bin/env bash
# Custom lane catalog example: pipeline driven by a user-defined catalog.
# Run from the repo root after: pip install journey-map-thinking
set -euo pipefail

CATALOG="$(dirname "$0")/lanes.json"
OUTDIR="$(mktemp -d)"
echo "Using catalog: $CATALOG"
echo "Writing artifacts to: $OUTDIR"

echo "ingest csv data from a file source" > "$OUTDIR/raw_goal.txt"

jm position \
  --raw "$OUTDIR/raw_goal.txt" \
  --catalog "$CATALOG" \
  --output "$OUTDIR/journey_position.json"

jm select-lane \
  --position "$OUTDIR/journey_position.json" \
  --catalog "$CATALOG" \
  --output "$OUTDIR/journey_lane.json"

jm align-gate \
  --lane "$OUTDIR/journey_lane.json" \
  --catalog "$CATALOG" \
  --output "$OUTDIR/journey_gate_alignment.json"

jm progress \
  --lane "$OUTDIR/journey_lane.json" \
  --output "$OUTDIR/journey_progress_check.json" \
  --tests-added

jm update \
  --progress "$OUTDIR/journey_progress_check.json" \
  --lane "$OUTDIR/journey_lane.json" \
  --output "$OUTDIR/journey_map_update.md" \
  --global-root "$OUTDIR/global_map"

echo ""
echo "Lane used:"
python3 -c "import json; d=json.load(open('$OUTDIR/journey_position.json')); print(' ', d['likely_lanes'])"
echo ""
echo "Update:"
cat "$OUTDIR/journey_map_update.md"
