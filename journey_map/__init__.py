"""journey_map: Journey Map Thinking layer for agent pipelines.

A deterministic, no-LLM layer that locates a task on a configurable lane catalog,
selects a lane, aligns the planner gate, checks for REAL progress (refusing
summary-only runs), and updates a persistent global map. Flag-gated by
JOURNEY_MAP_ENABLED so that an integrating pipeline is unchanged when the flag is off.

Install::

    pip install journey-map-thinking

Quickstart::

    from journey_map import position, select_lane, align_gate, check_progress, update_map

    pos = position("build a CSV ingestion pipeline")
    sel = select_lane(pos)
    gate = align_gate(sel)
    chk = check_progress(sel, changed_files=["ingestion.py"], tests_added=True)
    md = update_map(chk, sel)
    print(md)

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

from .artifacts import (
    DEFAULT_GLOBAL_ROOT,
    journey_required,
    read_component_levels,
    read_raw_goal,
    seed_global_map,
)
from .gate_alignment import align_gate
from .lanes import LANE_CATALOG, MATCH_PRIORITY, Lane, all_lanes, get_lane, matched_lanes
from .position import position
from .progress import check_progress
from .runner import JourneyRunResult, run
from .schema import (
    CAPABILITY_LEVELS,
    HONEST_SCOPE,
    LANE_IDS,
    PIPELINE_VISION,
    PROGRESS_TYPES,
    RELEVANCE,
    VISION_LANE,
    JourneyGateAlignment,
    JourneyLaneSelection,
    JourneyPosition,
    JourneyProgressCheck,
    validate_gate_alignment,
    validate_lane_selection,
    validate_position,
    validate_progress_check,
)
from .selector import select_lane
from .update import render_update_md, update_map

__all__ = [
    # convenience wrapper
    "run",
    "JourneyRunResult",
    # pipeline
    "position",
    "select_lane",
    "align_gate",
    "check_progress",
    "update_map",
    "render_update_md",
    # catalog
    "Lane",
    "LANE_CATALOG",
    "MATCH_PRIORITY",
    "all_lanes",
    "get_lane",
    "matched_lanes",
    # artifacts
    "seed_global_map",
    "journey_required",
    "read_raw_goal",
    "read_component_levels",
    "DEFAULT_GLOBAL_ROOT",
    # schema
    "JourneyPosition",
    "JourneyLaneSelection",
    "JourneyGateAlignment",
    "JourneyProgressCheck",
    "validate_position",
    "validate_lane_selection",
    "validate_gate_alignment",
    "validate_progress_check",
    # vocab
    "HONEST_SCOPE",
    "PIPELINE_VISION",
    "VISION_LANE",
    "LANE_IDS",
    "RELEVANCE",
    "CAPABILITY_LEVELS",
    "PROGRESS_TYPES",
]
