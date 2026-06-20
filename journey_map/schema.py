"""Schemas and vocabularies for the Journey Map Thinking layer.

Deterministic dataclasses, validators, and the closed vocabularies (capability
levels L0-L10, progress types, relevance). No LLM, no I/O.

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

HONEST_SCOPE = "PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE"

# The pipeline vision: a generic description of what this pipeline aims toward.
PIPELINE_VISION = "a capable, honest, testable agent pipeline"

# Vision meta-lane for pure-ambition asks that must pick a concrete first slice.
VISION_LANE = "vision/ground-to-first-slice"

# Default lane IDs for the built-in catalog. Overridden when a custom catalog is loaded.
LANE_IDS = ("build", "research", "fix", "blocked", "vision")

RELEVANCE = ("none", "low", "medium", "high", "direct")

CAPABILITY_LEVELS = (
    "L0_CONCEPT",
    "L1_CALLABLE",
    "L2_ARTIFACT_PRODUCING",
    "L3_TESTED",
    "L4_SHADOW_READY",
    "L5_ASSISTIVE_READY",
    "L6_SCOPED_PRODUCTION_READY",
    "L7_REAL_PROJECT_OPERATOR",
    "L8_OPEN_WORLD_MEASURED",
    "L9_SPECIALIST_MODEL_OS",
    "L10_AMBITION_TO_REALITY_OS",
)

PROGRESS_TYPES = (
    "BUILD_ARTIFACT",
    "FIX_DEFECT",
    "PASS_GATE",
    "FAIL_GATE_WITH_UNLOCK",
    "TRAIN_MODEL",
    "RETIRE_MODEL",
    "RUN_BENCHMARK",
    "UPDATE_RUNTIME",
    "CREATE_OWNER_PACKET",
    "INTEGRATE_IN_GO",
    "DOGFOOD_REAL_TASK",
    "QA_VERIFY",
    "REFLECT_LESSON",
    "BLOCKED_NO_SAFE_ACTION",
)

# The release outcome the progress check uses when no real progress occurred.
RELEASE_BLOCKED_NO_PROGRESS = "BLOCKED_NO_PROGRESS"


@dataclass
class JourneyPosition:
    """Where a task sits on the journey map before execution."""

    run_id: str
    raw_goal: str
    goal_relevance: str
    current_capability_level: str
    likely_lanes: list[str] = field(default_factory=list)
    known_related_components: list[str] = field(default_factory=list)
    known_blockers: list[str] = field(default_factory=list)
    owner_dependent: bool = False
    can_advance_now: bool = True
    anti_loop_warning: str | None = None
    must_pick_concrete_slice: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "raw_goal": self.raw_goal,
            "goal_relevance": self.goal_relevance,
            "current_capability_level": self.current_capability_level,
            "likely_lanes": list(self.likely_lanes),
            "known_related_components": list(self.known_related_components),
            "known_blockers": list(self.known_blockers),
            "owner_dependent": self.owner_dependent,
            "can_advance_now": self.can_advance_now,
            "anti_loop_warning": self.anti_loop_warning,
            "must_pick_concrete_slice": self.must_pick_concrete_slice,
            "honest_scope": HONEST_SCOPE,
        }


@dataclass
class JourneyLaneSelection:
    """The chosen lane and the artifact that would prove progress."""

    primary_lane: str
    selected_milestone: str
    target_gate: str
    progress_type: str
    why_this_lane: str
    artifact_that_proves_progress: str
    secondary_lanes: list[str] = field(default_factory=list)
    what_not_to_repeat: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_lane": self.primary_lane,
            "secondary_lanes": list(self.secondary_lanes),
            "selected_milestone": self.selected_milestone,
            "target_gate": self.target_gate,
            "progress_type": self.progress_type,
            "why_this_lane": self.why_this_lane,
            "what_not_to_repeat": list(self.what_not_to_repeat),
            "artifact_that_proves_progress": self.artifact_that_proves_progress,
            "honest_scope": HONEST_SCOPE,
        }


@dataclass
class JourneyGateAlignment:
    """Tells the Planner what milestone, evidence, and claim boundaries apply."""

    lane: str
    release_gate: str
    success_condition: str
    failure_condition: str
    planned_artifacts: list[str] = field(default_factory=list)
    required_tests: list[str] = field(default_factory=list)
    qa_checks: list[str] = field(default_factory=list)
    blocked_claims: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lane": self.lane,
            "planned_artifacts": list(self.planned_artifacts),
            "required_tests": list(self.required_tests),
            "qa_checks": list(self.qa_checks),
            "release_gate": self.release_gate,
            "blocked_claims": list(self.blocked_claims),
            "success_condition": self.success_condition,
            "failure_condition": self.failure_condition,
            "honest_scope": HONEST_SCOPE,
        }


@dataclass
class JourneyProgressCheck:
    """Whether real journey progress occurred (anti-vague)."""

    lane: str
    milestone: str
    before_level: str
    after_level: str
    progress_made: bool
    progress_type: str
    next_unlock: str
    evidence: list[str] = field(default_factory=list)
    blocker: str | None = None
    recommended_release: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "lane": self.lane,
            "milestone": self.milestone,
            "before_level": self.before_level,
            "after_level": self.after_level,
            "progress_made": self.progress_made,
            "progress_type": self.progress_type,
            "evidence": list(self.evidence),
            "blocker": self.blocker,
            "next_unlock": self.next_unlock,
            "recommended_release": self.recommended_release,
            "honest_scope": HONEST_SCOPE,
        }


# ---------------------------------------------------------------------------
# Validators (return a list of error strings; empty list means valid)
# ---------------------------------------------------------------------------


def validate_position(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("run_id", "raw_goal", "goal_relevance", "current_capability_level"):
        if key not in data:
            errors.append(f"missing key: {key}")
    rel = data.get("goal_relevance")
    if rel not in RELEVANCE:
        errors.append(f"goal_relevance not in {RELEVANCE}: {rel!r}")
    if "likely_lanes" in data and not isinstance(data["likely_lanes"], list):
        errors.append("likely_lanes must be a list")
    if "owner_dependent" in data and not isinstance(data["owner_dependent"], bool):
        errors.append("owner_dependent must be a bool")
    if "can_advance_now" in data and not isinstance(data["can_advance_now"], bool):
        errors.append("can_advance_now must be a bool")
    return errors


def validate_lane_selection(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in (
        "primary_lane",
        "selected_milestone",
        "target_gate",
        "progress_type",
        "artifact_that_proves_progress",
    ):
        val = data.get(key)
        if not isinstance(val, str) or not val.strip():
            errors.append(f"{key} must be a non-empty string")
    if data.get("progress_type") and data["progress_type"] not in PROGRESS_TYPES:
        errors.append(
            f"progress_type not in PROGRESS_TYPES: {data.get('progress_type')!r}"
        )
    return errors


def validate_gate_alignment(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("lane", "release_gate", "success_condition", "failure_condition"):
        val = data.get(key)
        if not isinstance(val, str) or not val.strip():
            errors.append(f"{key} must be a non-empty string")
    for key in ("planned_artifacts", "required_tests", "qa_checks", "blocked_claims"):
        if key in data and not isinstance(data[key], list):
            errors.append(f"{key} must be a list")
    return errors


def validate_progress_check(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(data.get("progress_made"), bool):
        errors.append("progress_made must be a bool")
    if data.get("progress_type") and data["progress_type"] not in PROGRESS_TYPES:
        errors.append(
            f"progress_type not in PROGRESS_TYPES: {data.get('progress_type')!r}"
        )
    if data.get("before_level") and data["before_level"] not in CAPABILITY_LEVELS:
        errors.append(
            f"before_level not in CAPABILITY_LEVELS: {data.get('before_level')!r}"
        )
    if data.get("after_level") and data["after_level"] not in CAPABILITY_LEVELS:
        errors.append(
            f"after_level not in CAPABILITY_LEVELS: {data.get('after_level')!r}"
        )
    return errors
