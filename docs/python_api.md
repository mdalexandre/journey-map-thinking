# Python API Reference

## Pipeline functions

### `position(raw_goal, *, run_id="", component_levels=None, catalog=None)`

Locate a raw goal on the journey map.

Returns a `JourneyPosition` with:
- `goal_relevance`: one of `none`, `low`, `medium`, `high`, `direct`.
- `likely_lanes`: list of matching lane IDs in priority order.
- `known_related_components`: list of component labels from matched lanes.
- `known_blockers`: list of blocker strings from matched lanes.
- `owner_dependent`: True when the top lane requires owner action.
- `can_advance_now`: True when no blocker and not status-only.
- `anti_loop_warning`: non-None when the request is status-only.
- `must_pick_concrete_slice`: True when the request is a pure-vision ask.

### `select_lane(position, ambition=None, catalog=None)`

Select the journey lane for a positioned task.

Returns a `JourneyLaneSelection` with:
- `primary_lane`: the selected lane ID.
- `selected_milestone`: the first milestone in the selected lane.
- `target_gate`: the gate the planner must pass.
- `progress_type`: one of the PROGRESS_TYPES vocab strings.
- `artifact_that_proves_progress`: the artifact that proves the milestone.
- `secondary_lanes`: additional matched lanes.
- `what_not_to_repeat`: claim boundaries.

### `align_gate(selection, spec_text="", ambition=None, catalog=None)`

Align the planner gate from a lane selection.

Returns a `JourneyGateAlignment` with:
- `planned_artifacts`, `required_tests`, `qa_checks`, `blocked_claims`.
- `success_condition`, `failure_condition`.
- `release_gate`: the gate string from the lane selection.

### `check_progress(selection, *, changed_files=None, tests_added=False, gate_passed=False, benchmark_ran=False, model_changed=False, dogfood_ran=False, unlock_packet=False, qa_verdict="", release_verdict="", before_level="", after_level="", milestone="")`

Decide whether real journey progress occurred.

At least one evidence signal must be True for `progress_made` to be True.
When no signal is present, `progress_made` is False and `recommended_release`
is `BLOCKED_NO_PROGRESS`.

Returns a `JourneyProgressCheck`.

### `update_map(progress, selection, *, global_root="", run_id="", release_verdict="")`

Update the global journey map from a progress check.

Appends to `journey_history.jsonl`, optionally to `completed_milestones.jsonl`,
updates `next_unlocks.json` and `current_position.md`.

Returns the markdown string of the update.

### `render_update_md(progress, selection, *, run_id="", release_verdict="")`

Render the journey map update as a markdown string without writing to disk.

## Catalog functions

### `all_lanes()`

Return all lanes in the current built-in catalog as a list.

### `get_lane(lane_id)`

Return the `Lane` for `lane_id`, or `None` if not found.

### `matched_lanes(text, catalog=None)`

Return lane IDs whose markers appear in `text` (already lowered),
in MATCH_PRIORITY order.

## Artifact helpers

### `seed_global_map(root="")`

Create the global journey-map files (idempotent). Returns a dict of file names
to paths.

### `journey_required()`

True when `JOURNEY_MAP_ENABLED` is set truthy.

### `read_raw_goal(path)`

Extract the verbatim idea from a raw_request.md or return the whole text.

### `read_component_levels(root="")`

Read component capability levels from the global map. Returns `{}` if absent.

## Schema / validators

### `validate_position(data)`, `validate_lane_selection(data)`, `validate_gate_alignment(data)`, `validate_progress_check(data)`

Each returns a list of error strings (empty list means valid).

## Vocabulary constants

- `HONEST_SCOPE`: the honest scope string.
- `PIPELINE_VISION`: the generic pipeline vision string.
- `VISION_LANE`: the vision meta-lane identifier.
- `LANE_IDS`: tuple of default lane IDs.
- `RELEVANCE`: tuple of relevance values.
- `CAPABILITY_LEVELS`: tuple of L0-L10 capability level strings.
- `PROGRESS_TYPES`: tuple of progress type strings.
