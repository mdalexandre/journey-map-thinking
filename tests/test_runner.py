"""Tests for journey_map.runner: JourneyRunResult and run()."""
from __future__ import annotations

from journey_map import (
    JourneyGateAlignment,
    JourneyLaneSelection,
    JourneyPosition,
    JourneyRunResult,
    run,
)
from journey_map.catalog_loader import load_catalog


class TestJourneyRunResult:
    def test_run_returns_result_type(self) -> None:
        result = run("build a CSV ingestion pipeline")
        assert isinstance(result, JourneyRunResult)

    def test_run_fields_populated(self) -> None:
        result = run("build a CSV ingestion pipeline")
        assert result.lane
        assert result.next_move
        assert result.target_gate
        assert result.relevance

    def test_summary_line_count_between_4_and_6(self) -> None:
        result = run("build a CSV ingestion pipeline")
        lines = result.summary().strip().splitlines()
        n = len(lines)
        assert 4 <= n <= 6, f"expected 4-6 lines, got {n}"

    def test_summary_last_line_is_honest_scope(self) -> None:
        result = run("build a csv pipeline")
        lines = result.summary().strip().splitlines()
        assert lines[-1].startswith("honest_scope:")

    def test_summary_contains_lane_and_next_move(self) -> None:
        result = run("build a CSV ingestion pipeline")
        summary = result.summary()
        assert "Lane:" in summary
        assert "Next move:" in summary

    def test_summary_no_em_dash(self) -> None:
        result = run("build a pipeline")
        s = result.summary()
        assert "—" not in s, "em-dash found in summary"
        assert "–" not in s, "en-dash found in summary"

    def test_underlying_objects_are_correct_types(self) -> None:
        result = run("build a csv pipeline")
        assert isinstance(result.position, JourneyPosition)
        assert isinstance(result.lane_selection, JourneyLaneSelection)
        assert isinstance(result.gate_alignment, JourneyGateAlignment)

    def test_run_with_catalog_dict_matches_default(self) -> None:
        cat = load_catalog()
        r1 = run("build csv", catalog=cat)
        r2 = run("build csv")
        assert r1.lane == r2.lane

    def test_run_is_deterministic_same_goal(self) -> None:
        r1 = run("implement data ingestion module")
        r2 = run("implement data ingestion module")
        assert r1.lane == r2.lane
        assert r1.next_move == r2.next_move

    def test_run_status_only_goal_sets_can_advance_now_false(self) -> None:
        result = run("give me the status summary again")
        assert result.can_advance_now is False

    def test_run_blocked_goal_owner_dependent(self) -> None:
        result = run("deploy to production now")
        assert isinstance(result.can_advance_now, bool)

    def test_run_vision_goal_routes_to_vision_lane(self) -> None:
        result = run("change the world with AI agents")
        assert "vision" in result.lane.lower() or result.position.must_pick_concrete_slice

    def test_run_trivial_goal_low_relevance(self) -> None:
        result = run("fix a typo in the readme")
        assert result.relevance in ("low", "none")

    def test_run_custom_run_id_propagates(self) -> None:
        result = run("build a csv pipeline", run_id="test_run_001")
        assert result.position.run_id == "test_run_001"

    def test_result_position_and_run_result_can_advance_now_agree(self) -> None:
        result = run("build a module")
        assert result.can_advance_now == result.position.can_advance_now
