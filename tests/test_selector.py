"""Unit tests for journey_map.selector."""
from __future__ import annotations

from journey_map.position import position
from journey_map.schema import VISION_LANE
from journey_map.selector import select_lane


class TestSelectLaneVision:
    def test_vision_primary_lane_is_vision_lane(self) -> None:
        pos = position("push humanity forward with better software")
        sel = select_lane(pos)
        assert sel.primary_lane == VISION_LANE

    def test_vision_progress_type_is_build_artifact(self) -> None:
        pos = position("change the world")
        sel = select_lane(pos)
        assert sel.progress_type == "BUILD_ARTIFACT"

    def test_vision_artifact_is_first_slice_spec(self) -> None:
        pos = position("push humanity forward")
        sel = select_lane(pos)
        assert "first_slice_spec" in sel.artifact_that_proves_progress


class TestSelectLaneStatusOnly:
    def test_status_only_primary_lane_is_blocked(self) -> None:
        pos = position("give me the readiness summary")
        sel = select_lane(pos)
        assert "blocked" in sel.primary_lane or sel.progress_type == "BLOCKED_NO_SAFE_ACTION"

    def test_status_only_refuses_to_inflate(self) -> None:
        pos = position("show me the readiness summary again")
        sel = select_lane(pos)
        assert sel.progress_type == "BLOCKED_NO_SAFE_ACTION"


class TestSelectLaneNormalPath:
    def test_build_goal_routes_to_build_lane(self) -> None:
        pos = position("build a CSV ingestion pipeline")
        sel = select_lane(pos)
        assert sel.primary_lane == "build"

    def test_fix_goal_routes_to_fix_lane(self) -> None:
        pos = position("fix the failing test")
        sel = select_lane(pos)
        assert sel.primary_lane == "fix"

    def test_research_goal_routes_to_research_lane(self) -> None:
        pos = position("research and compare approaches to CSV ingestion")
        sel = select_lane(pos)
        assert sel.primary_lane == "research"

    def test_selection_has_milestone(self) -> None:
        pos = position("build a CSV ingestion pipeline")
        sel = select_lane(pos)
        assert sel.selected_milestone.strip()

    def test_selection_has_artifact(self) -> None:
        pos = position("build a CSV ingestion pipeline")
        sel = select_lane(pos)
        assert sel.artifact_that_proves_progress.strip()

    def test_what_not_to_repeat_non_empty(self) -> None:
        pos = position("build a CSV ingestion pipeline")
        sel = select_lane(pos)
        assert len(sel.what_not_to_repeat) > 0


class TestSelectLaneTrivialUnmapped:
    def test_unmapped_goal_routes_to_maintenance(self) -> None:
        pos = position("the quick brown fox")
        sel = select_lane(pos)
        assert "maintenance" in sel.primary_lane or sel.progress_type == "FIX_DEFECT"


class TestSelectLaneOwnerDependent:
    def test_owner_dependent_lane_creates_owner_packet(self) -> None:
        pos = position("blocked waiting for approval from owner")
        if pos.owner_dependent:
            sel = select_lane(pos)
            assert sel.progress_type == "CREATE_OWNER_PACKET"
