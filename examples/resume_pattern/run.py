"""Resume pattern example: pick up from a saved position JSON.

The resume pattern is structured state: save the position artifact and resume
from select-lane without re-running position. This prevents re-derivation of
context on subsequent runs.

Honesty note: this pattern is NOT empirically proven to improve next-action
quality. See docs/research_result.md for the null result (96 trials, delta 0.000,
p=1.000).
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from journey_map import align_gate, check_progress, position, select_lane, update_map


def main() -> None:
    # Simulate saving a position artifact on run 1.
    raw_goal = "build a transform module for the CSV ingestion pipeline"
    run_id = "resume_example_run_2"

    print("=== Run 1: position and save ===")
    pos = position(raw_goal, run_id="resume_example_run_1")
    pos_dict = pos.to_dict()

    with tempfile.TemporaryDirectory() as tmp:
        saved_pos = Path(tmp) / "saved_position.json"
        saved_pos.write_text(json.dumps(pos_dict, indent=2), encoding="utf-8")
        print(f"Saved position to: {saved_pos}")

        print()
        print("=== Run 2: resume from saved position ===")
        # Load the saved position.
        loaded_dict = json.loads(saved_pos.read_text())
        print(f"Resuming from lane: {loaded_dict.get('likely_lanes', [])}")

        # Reconstruct the JourneyPosition from the dict.
        from journey_map.schema import JourneyPosition

        resumed_pos = JourneyPosition(
            run_id=run_id,
            raw_goal=loaded_dict["raw_goal"],
            goal_relevance=loaded_dict["goal_relevance"],
            current_capability_level=loaded_dict["current_capability_level"],
            likely_lanes=loaded_dict.get("likely_lanes", []),
            known_related_components=loaded_dict.get("known_related_components", []),
            known_blockers=loaded_dict.get("known_blockers", []),
            owner_dependent=loaded_dict.get("owner_dependent", False),
            can_advance_now=loaded_dict.get("can_advance_now", True),
            anti_loop_warning=loaded_dict.get("anti_loop_warning"),
            must_pick_concrete_slice=loaded_dict.get("must_pick_concrete_slice", False),
        )

        # Resume from select-lane (skip re-running position).
        sel = select_lane(resumed_pos)
        align_gate(sel)  # validate gate alignment; result unused in this example
        chk = check_progress(sel, changed_files=["transform.py"])

        root = Path(tmp) / "journey_map"
        md = update_map(chk, sel, global_root=str(root), run_id=run_id)
        print(md)


if __name__ == "__main__":
    main()
