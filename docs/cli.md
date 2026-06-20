# CLI Reference

The `jm` command provides 6 subcommands. Each reads JSON input and writes JSON
(or markdown) output. Exit codes: 0 ok, 1 no-progress, 2 error, 3 usage.

## jm position

Locate a raw goal on the journey map.

```
jm position --raw <file> --output <file>
            [--run-id <str>]
            [--global-root <dir>]
            [--catalog <file>]
```

Input: a plain text or markdown file with the raw goal (or a `> quoted` idea).
Output: `journey_position.json` with `goal_relevance`, `likely_lanes`,
`known_blockers`, `owner_dependent`, `can_advance_now`, `anti_loop_warning`.

## jm select-lane

Select the journey lane for a positioned task.

```
jm select-lane --position <file> --output <file>
               [--ambition <file>]
               [--catalog <file>]
```

Input: `journey_position.json`.
Output: `journey_lane.json` with `primary_lane`, `selected_milestone`,
`target_gate`, `progress_type`, `artifact_that_proves_progress`.

## jm align-gate

Align the planner gate from a lane selection.

```
jm align-gate --lane <file> --output <file>
              [--spec <file>]
              [--catalog <file>]
```

Input: `journey_lane.json`.
Output: `journey_gate_alignment.json` with `planned_artifacts`,
`required_tests`, `qa_checks`, `blocked_claims`, `success_condition`,
`failure_condition`.

## jm progress

Check whether real progress occurred. Exits 1 when no evidence is present.

```
jm progress --lane <file> --output <file>
            [--release-verdict <file>]
            [--generator-log <file>]
            [--tests-added]
            [--dogfood-ran]
            [--before-level <str>]
            [--after-level <str>]
```

Input: `journey_lane.json`, optional release-verdict JSON and generator-log.
Output: `journey_progress_check.json` with `progress_made`, `progress_type`,
`evidence`, `blocker`, `recommended_release`.

Exit codes:
- 0: progress_made is True.
- 1: progress_made is False (BLOCKED_NO_PROGRESS).
- 2: error (bad input file, parse error).

## jm update

Update the global journey map and write the update markdown.

```
jm update --progress <file> --lane <file> --output <file>
          [--run-id <str>]
          [--release-verdict <file>]
          [--global-root <dir>]
```

Input: `journey_progress_check.json` and `journey_lane.json`.
Output: `journey_map_update.md`; also appends to `journey_history.jsonl` and
updates `current_position.md` under `--global-root`.

## jm seed

Seed the global journey map files (idempotent for append-only logs).

```
jm seed [--global-root <dir>]
```

Creates: `pipeline_vision.json`, `journey_lanes.json`, `component_levels.json`,
`blocker_map.json`, `next_unlocks.json`, `completed_milestones.jsonl`,
`journey_history.jsonl`, `current_position.md`.

## Global flags

- `--catalog <file>`: path to a custom lane catalog (JSON or YAML).
  Also readable from the `JOURNEY_MAP_CATALOG` environment variable.
- `--global-root <dir>`: override the default `~/.journey_map/` root.
  Also readable from the `JOURNEY_MAP_ROOT` environment variable.

## Note: --generator-log and the Python changed_files parameter

The Python API accepts `changed_files: list[str]` directly in `check_progress()`.
The CLI equivalent is `--generator-log <file>`, where the file is a JSON object
that may contain a `changed_files` key (a list of strings). The CLI reads that
key and populates the same field internally. The two paths produce identical
results; the asymmetry in naming is intentional (the CLI accepts a richer log
blob rather than a bare file list).
