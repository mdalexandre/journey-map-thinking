"""Journey positioner: locate a task on the map before execution.

Deterministic, no LLM. Uses the vendored classifiers for the system-class signal
and the lane catalog for routing. Trivial tasks stay low-relevance; status-only
tasks get an anti_loop_warning; vision asks must pick a concrete first slice.

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

import re

from . import lanes as _lanes
from .classifiers import TRIVIAL_MARKERS, classify_request
from .schema import VISION_LANE, JourneyPosition

# Lanes that denote substantial (build/research/system) work -> high relevance.
_CORE_LANES = {"build", "research", "fix"}

# Markers that signal a status-only / repeat-the-summary request (anti-loop).
_STATUS_MARKERS = (
    "status",
    "summary",
    "readiness summary",
    "where are we",
    "show me the readiness",
    "give me the readiness",
    "progress report",
    "readiness report",
    "again",
)

# Verbs that mean the task does real work (so it is not status-only).
_WORK_VERBS = (
    "build",
    "create",
    "implement",
    "fix",
    "train",
    "deploy",
    "integrate",
    "add",
    "write",
    "make",
    "reduce",
    "optimize",
    "run",
    "scaffold",
    "repair",
)

_TRIVIAL_EXTRA = ("readme", "typo", "comment", "whitespace")


def _phrase_in(phrase: str, text: str) -> bool:
    if " " in phrase:
        return phrase in text
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None


def _is_trivial(text: str) -> bool:
    if any(_phrase_in(m, text) for m in TRIVIAL_MARKERS):
        return True
    return any(m in text for m in _TRIVIAL_EXTRA)


def _is_status_only(text: str) -> bool:
    if not any(m in text for m in _STATUS_MARKERS):
        return False
    return not any(_phrase_in(v, text) for v in _WORK_VERBS)


def position(
    raw_goal: str,
    *,
    run_id: str = "",
    component_levels: dict[str, str] | None = None,
    catalog: dict | None = None,
) -> JourneyPosition:
    """Locate raw_goal on the journey map.

    Args:
        raw_goal: The raw task description.
        run_id: Optional identifier for this run (written to output JSON).
        component_levels: Optional mapping of component name to capability level,
            used to override the lane's provisional_level with a measured value.
        catalog: Optional custom lane catalog (dict[lane_id, Lane]).
            If None, the built-in default catalog is used.

    Returns:
        A JourneyPosition dataclass.
    """
    text = raw_goal.lower().strip()
    levels = component_levels or {}

    vision = _lanes.is_vision(text)
    trivial = _is_trivial(text) and not vision
    status_only = _is_status_only(text) and not vision
    matched = _lanes.matched_lanes(text, catalog)
    should_activate, _ = classify_request(raw_goal)

    anti_loop_warning: str | None = None
    if status_only:
        anti_loop_warning = (
            "status-only request: no lane is advanced by repeating a summary; "
            "pick a concrete artifact to produce or report a true blocker"
        )

    # Relevance.
    if vision:
        relevance = "direct"
    elif status_only or trivial:
        relevance = "low"
    elif matched:
        is_core = any(lid in _CORE_LANES for lid in matched)
        relevance = "high" if (should_activate or is_core) else "medium"
    else:
        relevance = "low"

    # Related components, blockers, owner dependence, capability level.
    likely_lanes: list[str] = []
    components: list[str] = []
    blockers: list[str] = []
    owner_dependent = False
    capability_level = "NA_TRIVIAL_OR_UNMAPPED"

    cat = catalog if catalog is not None else _lanes.LANE_CATALOG

    if vision:
        likely_lanes = [VISION_LANE]
        capability_level = "L10_AMBITION_TO_REALITY_OS"
    elif matched:
        likely_lanes = list(matched)
        top_lane = cat.get(matched[0])
        if top_lane is not None:
            capability_level = levels.get(top_lane.component, top_lane.provisional_level)
        for lid in matched:
            lane = cat.get(lid)
            if lane is None:
                continue
            components.append(lane.component)
            blockers.extend(lane.blockers)
            owner_dependent = owner_dependent or lane.owner_dependent

    can_advance_now = (not owner_dependent) and (not status_only)

    return JourneyPosition(
        run_id=run_id or "journey_position",
        raw_goal=raw_goal,
        goal_relevance=relevance,
        current_capability_level=capability_level,
        likely_lanes=likely_lanes,
        known_related_components=components,
        known_blockers=blockers,
        owner_dependent=owner_dependent,
        can_advance_now=can_advance_now,
        anti_loop_warning=anti_loop_warning,
        must_pick_concrete_slice=vision,
    )
