"""journey_map runner: convenience wrapper around the 3-stage position pipeline.

Calls position() -> select_lane() -> align_gate() in a single call and returns
a JourneyRunResult with flat convenience fields and the underlying stage objects.
No I/O, no filesystem writes, no subprocess calls, no network calls.

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

from dataclasses import dataclass

from .gate_alignment import align_gate as _align_gate
from .position import position as _position
from .schema import (
    HONEST_SCOPE,
    JourneyGateAlignment,
    JourneyLaneSelection,
    JourneyPosition,
)
from .selector import select_lane as _select_lane


@dataclass
class JourneyRunResult:
    """Flat convenience result from a single run() call.

    Flat fields (top-level contract):
        relevance:       goal relevance string from JourneyPosition.
        lane:            primary lane from JourneyLaneSelection.
        next_move:       selected milestone from JourneyLaneSelection.
        target_gate:     target gate from JourneyLaneSelection.
        can_advance_now: whether the task can advance without owner action.

    Underlying stage objects (full fidelity):
        position:       the JourneyPosition from stage 1.
        lane_selection: the JourneyLaneSelection from stage 2.
        gate_alignment: the JourneyGateAlignment from stage 3.
    """

    relevance: str
    lane: str
    next_move: str
    target_gate: str
    can_advance_now: bool
    position: JourneyPosition
    lane_selection: JourneyLaneSelection
    gate_alignment: JourneyGateAlignment

    def summary(self) -> str:
        """Return 4 to 6 lines of plain English describing the run result.

        The last line is always the honest_scope tag. No em-dashes or en-dashes
        are used as prose punctuation (prose style rule).
        """
        can_advance = "yes" if self.can_advance_now else "no"
        lines = [
            f"Goal relevance: {self.relevance}",
            f"Lane: {self.lane}",
            f"Next move: {self.next_move}",
            f"Gate: {self.target_gate}",
            f"Can advance now: {can_advance}",
            f"honest_scope: {HONEST_SCOPE}",
        ]
        return "\n".join(lines)


def run(
    goal: str,
    *,
    catalog: dict | None = None,
    run_id: str = "run",
) -> JourneyRunResult:
    """Locate a goal on the journey map and return a convenience result.

    Calls position() -> select_lane() -> align_gate() internally. No I/O,
    no filesystem writes, no subprocess calls, no network calls.

    Args:
        goal:    Raw goal string describing the task.
        catalog: Optional pre-loaded lane catalog dict (lane_id -> Lane).
                 If None, the built-in default catalog is used.
        run_id:  Optional run identifier written to the position artifact.

    Returns:
        A JourneyRunResult with flat fields and underlying stage objects.
    """
    pos = _position(goal, run_id=run_id, catalog=catalog)
    sel = _select_lane(pos, catalog=catalog)
    gate = _align_gate(sel, catalog=catalog)

    return JourneyRunResult(
        relevance=pos.goal_relevance,
        lane=sel.primary_lane,
        next_move=sel.selected_milestone,
        target_gate=sel.target_gate,
        can_advance_now=pos.can_advance_now,
        position=pos,
        lane_selection=sel,
        gate_alignment=gate,
    )
