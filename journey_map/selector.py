"""Lane selector: choose the lane that moves a task forward.

Deterministic, no LLM. Handles four special cases before the normal path:
vision asks (must pick a concrete first slice), owner-dependent blockers (emit an
owner-packet lane plus a parallel owner-independent lane), trivial/status-only
tasks (no journey inflation), and the normal matched path.

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

import re
from typing import Any

from . import lanes as _lanes
from .schema import VISION_LANE, JourneyLaneSelection, JourneyPosition

# Default progress type per lane ID (for the built-in catalog).
_LANE_PROGRESS: dict[str, str] = {
    "build": "BUILD_ARTIFACT",
    "research": "RUN_BENCHMARK",
    "fix": "FIX_DEFECT",
    "blocked": "BLOCKED_NO_SAFE_ACTION",
    "vision": "BUILD_ARTIFACT",
}


def _has_metric_target(text: str) -> bool:
    return bool(re.search(r"\d+\s?%", text)) or bool(re.search(r"\b\d+x\b", text))


def select_lane(
    pos: JourneyPosition,
    ambition: dict[str, Any] | None = None,
    catalog: dict | None = None,
) -> JourneyLaneSelection:
    """Select the journey lane for a positioned task.

    Args:
        pos: The JourneyPosition returned by position().
        ambition: Optional ambition dict (e.g. from a latent-ambition step).
        catalog: Optional custom lane catalog. If None, the built-in default is used.

    Returns:
        A JourneyLaneSelection dataclass.
    """
    matched = list(pos.likely_lanes)
    cat = catalog if catalog is not None else _lanes.LANE_CATALOG

    # 1. Vision ask: force a concrete first slice.
    if pos.must_pick_concrete_slice:
        return JourneyLaneSelection(
            primary_lane=VISION_LANE,
            selected_milestone="choose and spec ONE concrete, buildable first slice",
            target_gate="a concrete first slice is selected and routed to a real lane",
            progress_type="BUILD_ARTIFACT",
            why_this_lane=(
                "pure-vision ask; the only honest move is to pick a concrete first slice"
            ),
            artifact_that_proves_progress="first_slice_spec.md naming one real lane task",
            secondary_lanes=[],
            what_not_to_repeat=[
                "restating the vision without a concrete slice",
                "claiming a pipeline-vision milestone is reached",
            ],
        )

    # 2. Status-only request (anti-loop): refuse to manufacture progress.
    if pos.anti_loop_warning:
        return JourneyLaneSelection(
            primary_lane="ordinary/blocked",
            selected_milestone="choose a concrete artifact or report a true blocker",
            target_gate="a concrete artifact is chosen, or a true blocker is reported",
            progress_type="BLOCKED_NO_SAFE_ACTION",
            why_this_lane=(
                "status-only request advances no lane; refuse to manufacture progress"
            ),
            artifact_that_proves_progress="a concrete chosen artifact (none yet)",
            what_not_to_repeat=["repeating the readiness summary"],
        )

    # 3. Owner-dependent blocker: keep the domain lane's milestone and gate,
    #    but the honest immediate move is the unlock packet.
    if pos.owner_dependent and matched:
        primary = matched[0]
        lane = cat.get(primary)
        owner_independent = [lid for lid in matched if not _owner_dependent(lid, cat)]
        milestone = lane.milestones[0] if lane and lane.milestones else "owner opt-in packet"
        gate = lane.gates[0] if lane and lane.gates else "owner reviews and approves"
        domain_artifact = (
            lane.progress_artifacts[0] if lane and lane.progress_artifacts else "a release verdict"
        )
        boundary = lane.claim_boundary if lane else "do not overclaim"
        return JourneyLaneSelection(
            primary_lane=primary,
            selected_milestone=milestone,
            target_gate=gate,
            progress_type="CREATE_OWNER_PACKET",
            why_this_lane=(
                f"lane {primary!r} is owner-dependent; produce the unlock packet and do "
                "owner-independent work in parallel rather than waiting idle"
            ),
            artifact_that_proves_progress=(
                f"owner_unlock_packet.md + owner-independent {domain_artifact}"
            ),
            secondary_lanes=owner_independent or ["build"],
            what_not_to_repeat=["claiming done before owner approval", boundary],
        )

    # 4. No matched lane: trivial or unmapped task.
    if not matched:
        return JourneyLaneSelection(
            primary_lane="ordinary/maintenance",
            selected_milestone="complete the small task and read it back",
            target_gate="the small task is done and a read-back confirms it",
            progress_type="FIX_DEFECT",
            why_this_lane="trivial task; not on a journey lane and not inflated into one",
            artifact_that_proves_progress="the edited file (read-back confirmed)",
            what_not_to_repeat=["inflating a trivial task into a major undertaking"],
        )

    # 5. Normal path.
    primary = matched[0]
    secondary = [lid for lid in matched if lid != primary][:3]
    lane = cat.get(primary)
    assert lane is not None, f"primary lane {primary!r} not found in catalog"
    milestone = lane.milestones[0] if lane.milestones else f"advance {lane.name}"
    target_gate = lane.gates[0] if lane.gates else "independent QA + release verdict"
    artifact = lane.progress_artifacts[0] if lane.progress_artifacts else "a release verdict"
    why = f"markers route to lane {primary!r} ({lane.name})"
    if ambition and ambition.get("ambition_archetype"):
        why += f"; latent archetype {ambition['ambition_archetype']}"
    return JourneyLaneSelection(
        primary_lane=primary,
        selected_milestone=milestone,
        target_gate=target_gate,
        progress_type=_LANE_PROGRESS.get(primary, "BUILD_ARTIFACT"),
        why_this_lane=why,
        artifact_that_proves_progress=artifact,
        secondary_lanes=secondary,
        what_not_to_repeat=[lane.claim_boundary or "do not overclaim", "do not restate readiness"],
    )


def _owner_dependent(lane_id: str, cat: dict) -> bool:  # type: ignore[type-arg]
    lane = cat.get(lane_id)
    return bool(lane and lane.owner_dependent)
