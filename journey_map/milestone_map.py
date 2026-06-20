"""Generic milestone map: ordered steps from current state toward the pipeline vision.

This module provides the dataclasses and functions for tracking milestones
in a journey pipeline. It is a generic, public-safe version of the milestone
tracking concept. The default milestone map is empty; populate it by calling
build_milestone_map(lanes) with your catalog.

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .lanes import Lane
from .schema import CAPABILITY_LEVELS, HONEST_SCOPE

__all__ = [
    "MilestoneStatus",
    "Milestone",
    "PipelineVerdictResult",
    "ordered_milestone_map",
    "next_executable_step",
    "pipeline_verdict",
    "build_milestone_map",
]


class MilestoneStatus(str, Enum):
    DONE = "DONE"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    NOT_STARTED = "NOT_STARTED"


@dataclass(frozen=True)
class Milestone:
    """One ordered step on the path from current state toward the pipeline vision."""

    id: str
    lane: str
    name: str
    capability_level: str
    gate: str
    artifact: str
    status: MilestoneStatus
    evidence_basis: str
    honest_blocker: str
    owner_dependent: bool
    honest_scope: str = field(default=HONEST_SCOPE, init=False, compare=False)

    def __post_init__(self) -> None:
        if self.capability_level not in CAPABILITY_LEVELS:
            raise ValueError(
                f"Milestone {self.id}: capability_level {self.capability_level!r} "
                f"not in CAPABILITY_LEVELS"
            )
        if not self.evidence_basis:
            raise ValueError(f"Milestone {self.id}: evidence_basis must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lane": self.lane,
            "name": self.name,
            "capability_level": self.capability_level,
            "gate": self.gate,
            "artifact": self.artifact,
            "status": self.status.value,
            "evidence_basis": self.evidence_basis,
            "honest_blocker": self.honest_blocker,
            "owner_dependent": self.owner_dependent,
            "honest_scope": self.honest_scope,
        }


@dataclass(frozen=True)
class PipelineVerdictResult:
    """Result of evaluating whether all required pipeline gates are met."""

    verdict: str
    required_gates_passed: list[str]
    required_gates_missing: list[str]
    reason: str
    honest_scope: str = field(default=HONEST_SCOPE, init=False, compare=False)
    scope_walls_certified: bool = field(default=False, init=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "scope_walls_certified", False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "required_gates_passed": list(self.required_gates_passed),
            "required_gates_missing": list(self.required_gates_missing),
            "reason": self.reason,
            "honest_scope": self.honest_scope,
            "scope_walls_certified": self.scope_walls_certified,
        }


# The default milestone map is empty. Populate it with build_milestone_map().
_DEFAULT_MILESTONE_MAP: tuple[Milestone, ...] = ()


def build_milestone_map(lanes: list[Lane]) -> tuple[Milestone, ...]:
    """Build a placeholder milestone per lane.

    This generates a minimal milestone for each lane in the catalog, useful
    as a starting point. Replace with hand-authored milestones for production use.

    Args:
        lanes: The list of Lane objects from the catalog.

    Returns:
        A tuple of Milestone objects, one per lane, all NOT_STARTED.
    """
    milestones = []
    for i, lane in enumerate(lanes, start=1):
        mid = f"M{i:02d}"
        m_name = lane.milestones[0] if lane.milestones else f"first milestone: {lane.name}"
        gate = lane.gates[0] if lane.gates else f"lane {lane.lane_id} gate"
        artifact = (
            lane.progress_artifacts[0] if lane.progress_artifacts else "release_verdict.json"
        )
        milestones.append(
            Milestone(
                id=mid,
                lane=lane.lane_id,
                name=m_name,
                capability_level=lane.provisional_level,
                gate=gate,
                artifact=artifact,
                status=MilestoneStatus.NOT_STARTED,
                evidence_basis=f"placeholder: lane {lane.lane_id!r} exists in catalog",
                honest_blocker="not started; populate with real evidence to update status",
                owner_dependent=lane.owner_dependent,
            )
        )
    return tuple(milestones)


def ordered_milestone_map(
    extra: tuple[Milestone, ...] | None = None,
) -> tuple[Milestone, ...]:
    """Return the ordered milestone map.

    Args:
        extra: Optional additional milestones to append after the defaults.

    Returns:
        A tuple of Milestone objects in order.
    """
    base = _DEFAULT_MILESTONE_MAP
    if extra:
        base = base + extra
    return base


def next_executable_step(
    milestones: tuple[Milestone, ...],
) -> Milestone | None:
    """Return the first NOT_STARTED, owner-independent milestone, or None.

    If all milestones are DONE, BLOCKED (owner-dependent), or none exist,
    returns None.
    """
    for m in milestones:
        if m.status == MilestoneStatus.NOT_STARTED and not m.owner_dependent:
            return m
    return None


def pipeline_verdict(
    evidence: dict[str, Any],
    required_milestones: tuple[Milestone, ...] | None = None,
) -> PipelineVerdictResult:
    """Evaluate whether all required pipeline gates are met.

    Args:
        evidence: A dict mapping milestone ID to a verdict string.
            A milestone gate is considered passed when its verdict is
            "GATE_PASSED" or "DONE".
        required_milestones: The milestones that must all pass.
            If None or empty, the verdict is always NOT_MET with reason
            "no required milestones defined".

    Returns:
        A PipelineVerdictResult.

    The only passing verdict is "ALL_GATES_MET". Any other outcome is "NOT_MET".
    This function has no code path that returns ALL_GATES_MET unless every
    required milestone has a passing evidence entry.
    """
    if not required_milestones:
        return PipelineVerdictResult(
            verdict="NOT_MET",
            required_gates_passed=[],
            required_gates_missing=[],
            reason="no required milestones defined; build_milestone_map() first",
        )

    passed: list[str] = []
    missing: list[str] = []
    _PASSING = {"GATE_PASSED", "DONE"}

    for m in required_milestones:
        e = str(evidence.get(m.id, "")).upper()
        if e in _PASSING:
            passed.append(m.id)
        else:
            missing.append(m.id)

    if missing:
        return PipelineVerdictResult(
            verdict="NOT_MET",
            required_gates_passed=passed,
            required_gates_missing=missing,
            reason=(
                f"{len(missing)} required gate(s) not yet passed: {missing}. "
                "Each must have evidence verdict 'GATE_PASSED' or 'DONE'."
            ),
        )

    return PipelineVerdictResult(
        verdict="ALL_GATES_MET",
        required_gates_passed=passed,
        required_gates_missing=[],
        reason=f"all {len(passed)} required gate(s) passed",
    )
