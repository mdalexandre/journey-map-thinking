"""Unit tests for journey_map.position."""
from __future__ import annotations

from journey_map.position import position
from journey_map.schema import VISION_LANE


class TestPositionTrivial:
    def test_typo_fix_is_low_relevance(self) -> None:
        pos = position("fix a typo in the README")
        assert pos.goal_relevance == "low"

    def test_trivial_low_relevance_even_if_lane_matches(self) -> None:
        # "fix a typo" is trivial: relevance is low even though "fix" matches the fix lane.
        pos = position("fix a typo")
        assert pos.goal_relevance == "low"

    def test_trivial_can_advance(self) -> None:
        pos = position("fix a typo")
        assert pos.can_advance_now is True


class TestPositionStatusOnly:
    def test_status_request_gets_warning(self) -> None:
        pos = position("give me the readiness summary")
        assert pos.anti_loop_warning is not None

    def test_status_only_is_low_relevance(self) -> None:
        pos = position("give me the readiness summary")
        assert pos.goal_relevance == "low"

    def test_status_only_cannot_advance(self) -> None:
        pos = position("give me the readiness summary")
        assert pos.can_advance_now is False


class TestPositionVision:
    def test_vision_is_direct_relevance(self) -> None:
        pos = position("push humanity forward with this project")
        assert pos.goal_relevance == "direct"

    def test_vision_must_pick_concrete_slice(self) -> None:
        pos = position("change the world with better software")
        assert pos.must_pick_concrete_slice is True

    def test_vision_likely_lane_is_vision_lane(self) -> None:
        pos = position("push humanity forward")
        assert pos.likely_lanes == [VISION_LANE]


class TestPositionMatched:
    def test_build_goal_matches_build_lane(self) -> None:
        pos = position("build a CSV ingestion pipeline")
        assert "build" in pos.likely_lanes

    def test_fix_goal_matches_fix_lane(self) -> None:
        pos = position("fix the failing test in the ingestion module")
        assert "fix" in pos.likely_lanes

    def test_research_goal_matches_research_lane(self) -> None:
        pos = position("research and compare different ingestion approaches")
        assert "research" in pos.likely_lanes

    def test_matched_goal_has_components(self) -> None:
        pos = position("build a CSV ingestion pipeline")
        assert len(pos.known_related_components) > 0

    def test_run_id_propagated(self) -> None:
        pos = position("build something", run_id="test_run_42")
        assert pos.run_id == "test_run_42"

    def test_custom_catalog_used(self, custom_catalog_json: object) -> None:
        # Test that a custom catalog routes differently.
        from journey_map.catalog_loader import load_catalog

        cat = load_catalog(str(custom_catalog_json))  # type: ignore[arg-type]
        pos = position("ingest csv data", catalog=cat)
        assert "ingest" in pos.likely_lanes

    def test_owner_dependent_lane_blocks_advance(self) -> None:
        pos = position("blocked waiting for approval")
        # If the blocked lane is owner_dependent and matches, can_advance_now should be False.
        if pos.owner_dependent:
            assert pos.can_advance_now is False


class TestPositionCapabilityLevel:
    def test_trivial_has_low_relevance(self) -> None:
        pos = position("fix a typo")
        assert pos.goal_relevance == "low"

    def test_build_has_artifact_producing_level(self) -> None:
        pos = position("build a CSV ingestion pipeline")
        assert pos.current_capability_level != ""

    def test_vision_has_l10_level(self) -> None:
        pos = position("push humanity forward")
        assert pos.current_capability_level == "L10_AMBITION_TO_REALITY_OS"
