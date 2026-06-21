#!/usr/bin/env bash
# scripts/docker_e2e.sh
# End-to-end test script run inside the journey-map Docker container.
# Sections 1 through 9 each set PASS/FAIL; Section 10 prints the summary.
#
# honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
# scope_walls_certified: false

set -euo pipefail

RESULTS=()
OVERALL=0

pass() { RESULTS+=("[PASS] $1"); }
fail() { RESULTS+=("[FAIL] $1"); OVERALL=1; }

# -----------------------------------------------------------------------
# Section 1: pytest
# -----------------------------------------------------------------------
echo "=== Section 1: pytest ==="
if pytest -q; then
    pass "pytest all tests"
else
    fail "pytest exited non-zero"
fi

# -----------------------------------------------------------------------
# Section 2: Python import smoke
# -----------------------------------------------------------------------
echo "=== Section 2: import smoke ==="
python -c "from journey_map import position, select_lane, align_gate, check_progress, update_map; print('IMPORT_OK')"
pass "five-function import"

# -----------------------------------------------------------------------
# Section 3: CLI help coverage
# -----------------------------------------------------------------------
echo "=== Section 3: CLI help ==="
jm --help > /dev/null
for sub in position select-lane align-gate progress update seed run; do
    if jm "$sub" --help > /dev/null 2>&1; then
        pass "jm $sub --help"
    else
        fail "jm $sub --help exited non-zero"
    fi
done

# -----------------------------------------------------------------------
# Section 4: Full 5-stage pipeline on FAKE fixtures
# -----------------------------------------------------------------------
echo "=== Section 4: full pipeline ==="
mkdir -p /tmp/jm_e2e

jm position --raw tests/fixtures/task_build.md --output /tmp/jm_e2e/pos.json
pass "stage 1: position"

jm select-lane --position /tmp/jm_e2e/pos.json --output /tmp/jm_e2e/lane.json
pass "stage 2: select-lane"

jm align-gate --lane /tmp/jm_e2e/lane.json --spec tests/fixtures/spec_build.md --output /tmp/jm_e2e/gate.json
pass "stage 3: align-gate"

jm progress \
    --lane /tmp/jm_e2e/lane.json \
    --release-verdict tests/fixtures/release_verdict_pass.json \
    --output /tmp/jm_e2e/progress.json
pass "stage 4: progress (with release_verdict PASS)"

PROGRESS_MADE=$(python -c "import json; d=json.load(open('/tmp/jm_e2e/progress.json')); print(str(d.get('progress_made','')).lower())")
if [ "$PROGRESS_MADE" = "true" ]; then
    pass "stage 4: progress_made=true"
else
    fail "stage 4: progress_made was not true (got: $PROGRESS_MADE)"
fi

jm update \
    --progress /tmp/jm_e2e/progress.json \
    --lane /tmp/jm_e2e/lane.json \
    --output /tmp/jm_e2e/map_update.md

if [ -s /tmp/jm_e2e/map_update.md ]; then
    pass "stage 5: update produced non-empty markdown"
else
    fail "stage 5: update output missing or empty"
fi

# -----------------------------------------------------------------------
# Section 5: Summary-only BLOCKED path
# -----------------------------------------------------------------------
echo "=== Section 5: summary-only BLOCKED ==="
set +e
jm progress \
    --lane /tmp/jm_e2e/lane.json \
    --output /tmp/jm_e2e/progress_blocked.json
BLOCKED_EXIT=$?
set -e

if [ "$BLOCKED_EXIT" -eq 1 ]; then
    pass "summary-only progress exits 1"
else
    fail "summary-only progress expected exit 1, got $BLOCKED_EXIT"
fi

BLOCKED_MADE=$(python -c "import json; d=json.load(open('/tmp/jm_e2e/progress_blocked.json')); print(str(d.get('progress_made','')).lower())")
if [ "$BLOCKED_MADE" = "false" ]; then
    pass "summary-only: progress_made=false"
else
    fail "summary-only: expected progress_made=false, got $BLOCKED_MADE"
fi

BLOCKED_REC=$(python -c "import json; d=json.load(open('/tmp/jm_e2e/progress_blocked.json')); print(d.get('recommended_release',''))")
if [ "$BLOCKED_REC" = "BLOCKED_NO_PROGRESS" ]; then
    pass "summary-only: recommended_release=BLOCKED_NO_PROGRESS"
else
    fail "summary-only: expected BLOCKED_NO_PROGRESS, got $BLOCKED_REC"
fi

# -----------------------------------------------------------------------
# Section 6: Custom catalog (JSON)
# -----------------------------------------------------------------------
echo "=== Section 6: custom JSON catalog ==="
jm position \
    --raw tests/fixtures/task_build.md \
    --catalog tests/fixtures/custom_lane_catalog.json \
    --output /tmp/jm_e2e/custom_pos.json
pass "custom JSON catalog position"

# -----------------------------------------------------------------------
# Section 7: Custom catalog (YAML)
# -----------------------------------------------------------------------
echo "=== Section 7: custom YAML catalog ==="
jm position \
    --raw tests/fixtures/task_build.md \
    --catalog tests/fixtures/custom_lane_catalog.yaml \
    --output /tmp/jm_e2e/custom_yaml_pos.json
pass "custom YAML catalog position"

# -----------------------------------------------------------------------
# Section 8: Resume (re-read saved JSON)
# -----------------------------------------------------------------------
echo "=== Section 8: resume ==="
jm select-lane \
    --position /tmp/jm_e2e/pos.json \
    --output /tmp/jm_e2e/lane_resumed.json
if [ -s /tmp/jm_e2e/lane_resumed.json ]; then
    pass "resume: select-lane from saved pos.json"
else
    fail "resume: lane_resumed.json missing or empty"
fi

# -----------------------------------------------------------------------
# Section 9: Fake-HOME persistence check
# -----------------------------------------------------------------------
echo "=== Section 9: HOME persistence ==="
FAKE_HOME=$(mktemp -d)
HOME="$FAKE_HOME" jm position \
    --raw tests/fixtures/task_build.md \
    --output /tmp/jm_e2e/pos_home.json

UNEXPECTED=$(find "$FAKE_HOME" -mindepth 1 -type f | wc -l)
UNEXPECTED_DIRS=$(find "$FAKE_HOME" -mindepth 1 -type d | wc -l)
TOTAL_UNEXPECTED=$((UNEXPECTED + UNEXPECTED_DIRS))
if [ "$TOTAL_UNEXPECTED" -eq 0 ]; then
    pass "HOME persistence: no unexpected writes to fake HOME"
else
    echo "UNEXPECTED files/dirs in fake HOME:"
    find "$FAKE_HOME" -mindepth 1
    fail "HOME persistence: $TOTAL_UNEXPECTED unexpected items written to fake HOME"
fi
rm -rf "$FAKE_HOME"

# -----------------------------------------------------------------------
# Section 10: Summary
# -----------------------------------------------------------------------
echo ""
echo "=== Section 10: Summary ==="
for r in "${RESULTS[@]}"; do
    echo "$r"
done

if [ "$OVERALL" -eq 0 ]; then
    echo ""
    echo "ALL SECTIONS PASSED"
    exit 0
else
    echo ""
    echo "ONE OR MORE SECTIONS FAILED"
    exit 1
fi
