"""Unit tests for journey_map.lanes."""
from __future__ import annotations

from journey_map.lanes import (
    LANE_CATALOG,
    MATCH_PRIORITY,
    Lane,
    all_lanes,
    get_lane,
    is_vision,
    matched_lanes,
)


class TestLaneCatalog:
    def test_catalog_has_five_default_lanes(self) -> None:
        assert len(LANE_CATALOG) == 5

    def test_default_lane_ids_are_generic(self) -> None:
        expected = {"build", "research", "fix", "blocked", "vision"}
        assert set(LANE_CATALOG.keys()) == expected

    def test_lane_components_are_generic(self) -> None:
        # The default catalog must expose only the generic lanes. This positive
        # assertion replaces an earlier denylist of private component names so
        # the public test never has to name them.
        generic = {"build", "research", "fix", "blocked", "vision"}
        for lane in LANE_CATALOG.values():
            assert lane.lane_id in generic, (
                f"Unexpected lane id {lane.lane_id!r} in the default catalog"
            )

    def test_no_lane_id_is_single_uppercase_letter(self) -> None:
        # Old-style A-N lane IDs should not appear.
        for lid in LANE_CATALOG:
            assert not (len(lid) == 1 and lid.isupper()), (
                f"Old-style lane ID {lid!r} found"
            )

    def test_all_lanes_have_markers(self) -> None:
        for lane in LANE_CATALOG.values():
            assert len(lane.markers) > 0, f"lane {lane.lane_id!r} has no markers"

    def test_all_lanes_have_description(self) -> None:
        for lane in LANE_CATALOG.values():
            assert lane.description.strip(), f"lane {lane.lane_id!r} has empty description"

    def test_build_lane_exists(self) -> None:
        assert "build" in LANE_CATALOG

    def test_fix_lane_exists(self) -> None:
        assert "fix" in LANE_CATALOG


class TestMatchPriority:
    def test_match_priority_contains_all_catalog_ids(self) -> None:
        for lid in MATCH_PRIORITY:
            assert lid in LANE_CATALOG, f"MATCH_PRIORITY has unknown lane {lid!r}"

    def test_match_priority_length(self) -> None:
        assert len(MATCH_PRIORITY) == len(LANE_CATALOG)


class TestAllLanes:
    def test_returns_list(self) -> None:
        lanes = all_lanes()
        assert isinstance(lanes, list)
        assert len(lanes) == 5

    def test_all_are_lane_instances(self) -> None:
        for lane in all_lanes():
            assert isinstance(lane, Lane)


class TestGetLane:
    def test_get_existing_lane(self) -> None:
        lane = get_lane("build")
        assert lane is not None
        assert lane.lane_id == "build"

    def test_get_nonexistent_lane(self) -> None:
        assert get_lane("NONEXISTENT_LANE_XYZ") is None

    def test_get_lane_returns_lane_instance(self) -> None:
        lane = get_lane("fix")
        assert isinstance(lane, Lane)


class TestMatchedLanes:
    def test_build_marker_matches_build_lane(self) -> None:
        hits = matched_lanes("build a csv ingestion pipeline")
        assert "build" in hits

    def test_fix_marker_matches_fix_lane(self) -> None:
        hits = matched_lanes("fix the failing test in module x")
        assert "fix" in hits

    def test_research_marker_matches_research_lane(self) -> None:
        hits = matched_lanes("research and evaluate approaches")
        assert "research" in hits

    def test_no_match_returns_empty(self) -> None:
        hits = matched_lanes("the quick brown fox jumps over the lazy dog")
        assert hits == []

    def test_custom_catalog_used_when_provided(self) -> None:
        from journey_map.lanes import Lane

        custom_cat = {
            "data": Lane(
                lane_id="data",
                name="Data",
                component="data",
                description="Data work.",
                provisional_level="L2_ARTIFACT_PRODUCING",
                markers=("data ingestion", "csv loading"),
            )
        }
        hits = matched_lanes("data ingestion pipeline", catalog=custom_cat)
        assert "data" in hits


class TestIsVision:
    def test_push_humanity_forward(self) -> None:
        assert is_vision("push humanity forward")

    def test_change_the_world(self) -> None:
        assert is_vision("change the world")

    def test_normal_text_not_vision(self) -> None:
        assert not is_vision("build a CSV ingestion pipeline")
