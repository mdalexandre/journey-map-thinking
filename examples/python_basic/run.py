"""Python API basic example: full 5-stage pipeline with fake data."""
from __future__ import annotations

import tempfile
from pathlib import Path

from journey_map import (
    align_gate,
    check_progress,
    position,
    select_lane,
    update_map,
)


def main() -> None:
    # Fake goal: no real project names or private paths.
    raw_goal = "build a CSV ingestion pipeline for sample data"
    run_id = "python_basic_example"

    print(f"Goal: {raw_goal!r}")
    print()

    # Stage 1: Position.
    pos = position(raw_goal, run_id=run_id)
    print("Stage 1 - Position:")
    print(f"  goal_relevance: {pos.goal_relevance}")
    print(f"  likely_lanes: {pos.likely_lanes}")
    print(f"  can_advance_now: {pos.can_advance_now}")
    print()

    # Stage 2: Select lane.
    sel = select_lane(pos)
    print("Stage 2 - Select lane:")
    print(f"  primary_lane: {sel.primary_lane}")
    print(f"  milestone: {sel.selected_milestone!r}")
    print(f"  progress_type: {sel.progress_type}")
    print()

    # Stage 3: Align gate.
    gate = align_gate(sel)
    print("Stage 3 - Align gate:")
    print(f"  release_gate: {gate.release_gate!r}")
    print(f"  required_tests: {gate.required_tests}")
    print()

    # Stage 4: Check progress.
    # Fake evidence: pretend ingestion.py was changed and tests were added.
    chk = check_progress(
        sel,
        changed_files=["ingestion.py", "test_ingestion.py"],
        tests_added=True,
    )
    print("Stage 4 - Progress:")
    print(f"  progress_made: {chk.progress_made}")
    print(f"  evidence: {chk.evidence}")
    print()

    # Stage 5: Update map.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "journey_map"
        md = update_map(chk, sel, global_root=str(root), run_id=run_id)
        print("Stage 5 - Update:")
        print(md)


if __name__ == "__main__":
    main()
