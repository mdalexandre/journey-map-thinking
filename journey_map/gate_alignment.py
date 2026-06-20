"""Gate alignment: tell the Planner what milestone, evidence, and claim limits apply.

Deterministic, no LLM. Translates a lane selection into the gate the Planner must
hit: planned artifacts, required tests, QA checks, blocked claims, and the
success/failure conditions.

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

from typing import Any

from . import lanes as _lanes
from .schema import JourneyGateAlignment, JourneyLaneSelection

_BUILD_TESTS = [
    "ruff check <changed>",
    "mypy <changed>",
    "pytest <related>",
]

_GLOBAL_BLOCKED_CLAIMS = (
    "no pipeline-vision milestone is reached unless its gate passes",
    "no progress unless a real artifact, gate, test, benchmark, or dogfood is produced",
)


def align_gate(
    selection: JourneyLaneSelection,
    spec_text: str = "",
    ambition: dict[str, Any] | None = None,
    catalog: dict | None = None,
) -> JourneyGateAlignment:
    """Align the journey gate for the Planner from a lane selection.

    Args:
        selection: The JourneyLaneSelection returned by select_lane().
        spec_text: Optional spec text (used for context; not parsed).
        ambition: Optional ambition dict (unused in this version; reserved).
        catalog: Optional custom lane catalog. If None, the built-in default is used.

    Returns:
        A JourneyGateAlignment dataclass.
    """
    lane_id = selection.primary_lane
    cat = catalog if catalog is not None else _lanes.LANE_CATALOG
    lane = cat.get(lane_id)

    planned_artifacts = [selection.artifact_that_proves_progress]
    qa_checks = ["QA inspects the ACTUAL built artifact, not the spec or intent"]
    blocked_claims = list(_GLOBAL_BLOCKED_CLAIMS)
    required_tests: list[str] = []

    if lane is not None:
        planned_artifacts = list(
            dict.fromkeys(lane.progress_artifacts + planned_artifacts)
        )
        qa_checks = lane.gates + qa_checks
        if lane.claim_boundary:
            blocked_claims.append(lane.claim_boundary)
        # Build/code lanes carry the Python gate; other lanes carry their own.
        if lane_id in ("build", "fix"):
            required_tests = list(_BUILD_TESTS)
        else:
            required_tests = [
                lane.gates[0] if lane.gates else "lane gate measurement"
            ]
    else:
        # Vision or ordinary/maintenance selection: no catalog lane.
        required_tests = ["a read-back or a single relevant check"]

    release_gate = selection.target_gate
    success_condition = (
        f"the milestone {selection.selected_milestone!r} is met and "
        f"{selection.artifact_that_proves_progress!r} exists with passing checks"
    )
    failure_condition = (
        "no artifact produced or the gate did not pass -> BLOCKED_NO_PROGRESS; "
        "never record fake progress"
    )

    return JourneyGateAlignment(
        lane=lane_id,
        release_gate=release_gate,
        success_condition=success_condition,
        failure_condition=failure_condition,
        planned_artifacts=planned_artifacts,
        required_tests=required_tests,
        qa_checks=qa_checks,
        blocked_claims=blocked_claims,
    )
