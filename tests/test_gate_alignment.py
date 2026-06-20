"""Unit tests for journey_map.gate_alignment."""
from __future__ import annotations

from journey_map.gate_alignment import align_gate
from journey_map.position import position
from journey_map.selector import select_lane


class TestAlignGate:
    def test_returns_gate_alignment(self) -> None:
        from journey_map.schema import JourneyGateAlignment

        pos = position("build a CSV ingestion pipeline")
        sel = select_lane(pos)
        gate = align_gate(sel)
        assert isinstance(gate, JourneyGateAlignment)

    def test_build_lane_has_build_tests(self) -> None:
        pos = position("build a CSV ingestion pipeline")
        sel = select_lane(pos)
        gate = align_gate(sel)
        required = " ".join(gate.required_tests)
        assert "ruff" in required or "pytest" in required or "mypy" in required

    def test_gate_has_blocked_claims(self) -> None:
        pos = position("build a CSV ingestion pipeline")
        sel = select_lane(pos)
        gate = align_gate(sel)
        assert len(gate.blocked_claims) > 0

    def test_gate_success_condition_references_milestone(self) -> None:
        pos = position("build a CSV ingestion pipeline")
        sel = select_lane(pos)
        gate = align_gate(sel)
        assert sel.selected_milestone in gate.success_condition

    def test_gate_failure_condition_mentions_no_progress(self) -> None:
        pos = position("build a CSV ingestion pipeline")
        sel = select_lane(pos)
        gate = align_gate(sel)
        assert "progress" in gate.failure_condition.lower()

    def test_vision_selection_has_read_back_test(self) -> None:
        pos = position("push humanity forward")
        sel = select_lane(pos)
        gate = align_gate(sel)
        assert len(gate.required_tests) > 0

    def test_qa_checks_always_present(self) -> None:
        pos = position("build a CSV ingestion pipeline")
        sel = select_lane(pos)
        gate = align_gate(sel)
        assert len(gate.qa_checks) > 0

    def test_global_blocked_claims_present(self) -> None:
        pos = position("build a CSV ingestion pipeline")
        sel = select_lane(pos)
        gate = align_gate(sel)
        combined = " ".join(gate.blocked_claims)
        assert "no progress unless" in combined or "gate passes" in combined

    def test_fix_lane_has_build_tests(self) -> None:
        pos = position("fix the failing test in ingestion")
        sel = select_lane(pos)
        gate = align_gate(sel)
        required = " ".join(gate.required_tests)
        assert "ruff" in required or "pytest" in required or "mypy" in required
