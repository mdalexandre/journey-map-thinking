"""Stub: wiring the progress check to a real run for study reproduction.

This stub shows the interface. Populate `run_trial` with your own evidence
collection logic. The pipeline itself is deterministic and has no LLM calls.
"""
from __future__ import annotations

from journey_map import check_progress, position, select_lane


def run_trial(raw_goal: str, changed_files: list[str], tests_added: bool) -> bool:
    """Return True when the pipeline records real progress, False otherwise.

    Args:
        raw_goal: The raw task description (fake data in tests).
        changed_files: List of files changed during execution (may be empty).
        tests_added: True when at least one test was added.

    Returns:
        True when the progress gate passes (progress_made is True).
    """
    pos = position(raw_goal)
    sel = select_lane(pos)
    chk = check_progress(sel, changed_files=changed_files, tests_added=tests_added)
    return chk.progress_made


def baseline_trial(raw_goal: str) -> bool:
    """Baseline: no pipeline; always returns False (no structured state).

    Replace this with whatever your baseline does. This stub returns False
    because the baseline does not use the progress gate.
    """
    return False


def main() -> None:
    # Example trial with fake data.
    goals = [
        "build a CSV ingestion pipeline",
        "fix the failing schema validation test",
        "research approaches to data normalization",
    ]

    print("Trial results (fake data):")
    for goal in goals:
        pipeline_result = run_trial(goal, changed_files=["fake_module.py"], tests_added=True)
        base_result = baseline_trial(goal)
        print(f"  goal: {goal!r}")
        print(f"    pipeline: {pipeline_result}, baseline: {base_result}")


if __name__ == "__main__":
    main()
