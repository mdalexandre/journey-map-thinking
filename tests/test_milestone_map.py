"""Unit tests for journey_map.milestone_map."""
from __future__ import annotations

import pytest

from journey_map.lanes import all_lanes
from journey_map.milestone_map import (
    Milestone,
    MilestoneStatus,
    build_milestone_map,
    next_executable_step,
    ordered_milestone_map,
    pipeline_verdict,
)


class TestMilestoneStatus:
    def test_values(self) -> None:
        assert MilestoneStatus.DONE.value == "DONE"
        assert MilestoneStatus.NOT_STARTED.value == "NOT_STARTED"


class TestMilestone:
    def test_valid_milestone(self) -> None:
        m = Milestone(
            id="M01",
            lane="build",
            name="First milestone",
            capability_level="L2_ARTIFACT_PRODUCING",
            gate="artifact exists",
            artifact="artifact.py",
            status=MilestoneStatus.NOT_STARTED,
            evidence_basis="placeholder: lane exists",
            honest_blocker="",
            owner_dependent=False,
        )
        assert m.id == "M01"

    def test_invalid_capability_level_raises(self) -> None:
        with pytest.raises(ValueError, match="capability_level"):
            Milestone(
                id="M01",
                lane="build",
                name="X",
                capability_level="NOT_A_LEVEL",
                gate="g",
                artifact="a",
                status=MilestoneStatus.NOT_STARTED,
                evidence_basis="has evidence",
                honest_blocker="",
                owner_dependent=False,
            )

    def test_empty_evidence_basis_raises(self) -> None:
        with pytest.raises(ValueError, match="evidence_basis"):
            Milestone(
                id="M01",
                lane="build",
                name="X",
                capability_level="L0_CONCEPT",
                gate="g",
                artifact="a",
                status=MilestoneStatus.NOT_STARTED,
                evidence_basis="",
                honest_blocker="",
                owner_dependent=False,
            )

    def test_to_dict(self) -> None:
        m = Milestone(
            id="M01",
            lane="build",
            name="First",
            capability_level="L0_CONCEPT",
            gate="g",
            artifact="a",
            status=MilestoneStatus.DONE,
            evidence_basis="observed",
            honest_blocker="",
            owner_dependent=False,
        )
        d = m.to_dict()
        assert d["id"] == "M01"
        assert d["status"] == "DONE"
        assert "honest_scope" in d


class TestBuildMilestoneMap:
    def test_build_generates_one_per_lane(self) -> None:
        lanes = all_lanes()
        milestones = build_milestone_map(lanes)
        assert len(milestones) == len(lanes)

    def test_all_milestones_not_started(self) -> None:
        milestones = build_milestone_map(all_lanes())
        for m in milestones:
            assert m.status == MilestoneStatus.NOT_STARTED

    def test_milestone_ids_are_unique(self) -> None:
        milestones = build_milestone_map(all_lanes())
        ids = [m.id for m in milestones]
        assert len(ids) == len(set(ids))

    def test_empty_lanes_returns_empty_tuple(self) -> None:
        assert build_milestone_map([]) == ()


class TestOrderedMilestoneMap:
    def test_default_is_empty(self) -> None:
        assert ordered_milestone_map() == ()

    def test_extra_appended(self) -> None:
        m = Milestone(
            id="M01",
            lane="build",
            name="x",
            capability_level="L0_CONCEPT",
            gate="g",
            artifact="a",
            status=MilestoneStatus.NOT_STARTED,
            evidence_basis="e",
            honest_blocker="",
            owner_dependent=False,
        )
        result = ordered_milestone_map(extra=(m,))
        assert len(result) == 1


class TestNextExecutableStep:
    def test_returns_first_not_started_owner_independent(self) -> None:
        milestones = build_milestone_map(all_lanes())
        step = next_executable_step(milestones)
        if step is not None:
            assert step.status == MilestoneStatus.NOT_STARTED
            assert not step.owner_dependent

    def test_returns_none_when_empty(self) -> None:
        assert next_executable_step(()) is None

    def test_skips_owner_dependent(self) -> None:
        m_owner = Milestone(
            id="M01",
            lane="blocked",
            name="owner milestone",
            capability_level="L0_CONCEPT",
            gate="g",
            artifact="a",
            status=MilestoneStatus.NOT_STARTED,
            evidence_basis="e",
            honest_blocker="",
            owner_dependent=True,
        )
        m_free = Milestone(
            id="M02",
            lane="build",
            name="free milestone",
            capability_level="L0_CONCEPT",
            gate="g",
            artifact="a",
            status=MilestoneStatus.NOT_STARTED,
            evidence_basis="e",
            honest_blocker="",
            owner_dependent=False,
        )
        step = next_executable_step((m_owner, m_free))
        assert step is not None
        assert step.id == "M02"


class TestPipelineVerdict:
    def test_no_required_milestones_returns_not_met(self) -> None:
        result = pipeline_verdict({})
        assert result.verdict == "NOT_MET"

    def test_all_passed_returns_all_gates_met(self) -> None:
        m = Milestone(
            id="M01",
            lane="build",
            name="x",
            capability_level="L0_CONCEPT",
            gate="g",
            artifact="a",
            status=MilestoneStatus.DONE,
            evidence_basis="e",
            honest_blocker="",
            owner_dependent=False,
        )
        result = pipeline_verdict({"M01": "GATE_PASSED"}, required_milestones=(m,))
        assert result.verdict == "ALL_GATES_MET"

    def test_partial_pass_returns_not_met(self) -> None:
        m1 = Milestone(
            id="M01",
            lane="build",
            name="x",
            capability_level="L0_CONCEPT",
            gate="g",
            artifact="a",
            status=MilestoneStatus.DONE,
            evidence_basis="e",
            honest_blocker="",
            owner_dependent=False,
        )
        m2 = Milestone(
            id="M02",
            lane="build",
            name="y",
            capability_level="L0_CONCEPT",
            gate="g",
            artifact="a",
            status=MilestoneStatus.NOT_STARTED,
            evidence_basis="e",
            honest_blocker="",
            owner_dependent=False,
        )
        result = pipeline_verdict(
            {"M01": "GATE_PASSED"}, required_milestones=(m1, m2)
        )
        assert result.verdict == "NOT_MET"
        assert "M02" in result.required_gates_missing

    def test_scope_walls_certified_always_false(self) -> None:
        result = pipeline_verdict({})
        assert result.scope_walls_certified is False

    def test_to_dict(self) -> None:
        result = pipeline_verdict({})
        d = result.to_dict()
        assert "verdict" in d
        assert d["scope_walls_certified"] is False
