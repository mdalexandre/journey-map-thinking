#!/usr/bin/env bash
# CLI basic example: 5-stage pipeline with fake data.
# Run from this directory after: pip install journey-map-thinking
set -euo pipefail

OUTDIR="$(mktemp -d)"
echo "Writing artifacts to: $OUTDIR"

jm position \
  --raw "$(dirname "$0")/raw_goal.txt" \
  --output "$OUTDIR/journey_position.json" \
  --run-id "cli_basic_example"

jm select-lane \
  --position "$OUTDIR/journey_position.json" \
  --output "$OUTDIR/journey_lane.json"

jm align-gate \
  --lane "$OUTDIR/journey_lane.json" \
  --output "$OUTDIR/journey_gate_alignment.json"

# Simulate real progress: pass --tests-added to unblock the progress gate.
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
echo "Done. Update markdown:"
cat "$OUTDIR/journey_map_update.md"
