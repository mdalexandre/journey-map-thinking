"""Unit tests for journey_map.schema."""
from __future__ import annotations

from journey_map.schema import (
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


class TestVocab:
    def test_honest_scope_set(self) -> None:
        assert "PROVISIONAL" in HONEST_SCOPE

    def test_pipeline_vision_generic(self) -> None:
        assert PIPELINE_VISION
        assert "pipeline" in PIPELINE_VISION.lower() or "agent" in PIPELINE_VISION.lower()

    def test_vision_lane_generic(self) -> None:
        assert "vision" in VISION_LANE.lower()

    def test_lane_ids_are_generic(self) -> None:
        for lid in LANE_IDS:
            assert lid.isalpha() or "_" in lid or "-" in lid, f"lane id {lid!r} looks numeric"

    def test_relevance_tuple(self) -> None:
        assert "none" in RELEVANCE
        assert "high" in RELEVANCE
        assert "direct" in RELEVANCE

    def test_capability_levels(self) -> None:
        assert "L0_CONCEPT" in CAPABILITY_LEVELS
        assert "L10_AMBITION_TO_REALITY_OS" in CAPABILITY_LEVELS

    def test_progress_types(self) -> None:
        assert "BUILD_ARTIFACT" in PROGRESS_TYPES
        assert "BLOCKED_NO_SAFE_ACTION" in PROGRESS_TYPES


class TestJourneyPosition:
    def test_to_dict_has_goal_relevance(self) -> None:
        pos = JourneyPosition(
            run_id="r1",
            raw_goal="build something",
            goal_relevance="high",
            current_capability_level="L2_ARTIFACT_PRODUCING",
        )
        d = pos.to_dict()
        assert "goal_relevance" in d
        assert d["goal_relevance"] == "high"

    def test_to_dict_uses_goal_relevance_key(self) -> None:
        pos = JourneyPosition(
            run_id="r1",
            raw_goal="build something",
            goal_relevance="high",
            current_capability_level="L2_ARTIFACT_PRODUCING",
        )
        d = pos.to_dict()
        assert "goal_relevance" in d
        # No legacy relevance key should survive under a different name.
        legacy = [k for k in d if k.endswith("_relevance") and k != "goal_relevance"]
        assert legacy == [], f"unexpected legacy relevance key(s): {legacy}"

    def test_to_dict_has_honest_scope(self) -> None:
        pos = JourneyPosition(
            run_id="r1",
            raw_goal="x",
            goal_relevance="low",
            current_capability_level="L0_CONCEPT",
        )
        assert pos.to_dict()["honest_scope"] == HONEST_SCOPE


class TestJourneyLaneSelection:
    def test_to_dict_roundtrip(self) -> None:
        sel = JourneyLaneSelection(
            primary_lane="build",
            selected_milestone="scaffold",
            target_gate="artifact exists",
            progress_type="BUILD_ARTIFACT",
            why_this_lane="test",
            artifact_that_proves_progress="file.py",
        )
        d = sel.to_dict()
        assert d["primary_lane"] == "build"
        assert d["honest_scope"] == HONEST_SCOPE


class TestJourneyGateAlignment:
    def test_to_dict_has_required_keys(self) -> None:
        gate = JourneyGateAlignment(
            lane="build",
            release_gate="gate1",
            success_condition="ok",
            failure_condition="fail",
        )
        d = gate.to_dict()
        for key in (
            "lane", "release_gate", "success_condition", "failure_condition", "honest_scope"
        ):
            assert key in d


class TestJourneyProgressCheck:
    def test_progress_made_true(self) -> None:
        chk = JourneyProgressCheck(
            lane="build",
            milestone="scaffold",
            before_level="L1_CALLABLE",
            after_level="L2_ARTIFACT_PRODUCING",
            progress_made=True,
            progress_type="BUILD_ARTIFACT",
            next_unlock="next step",
            evidence=["artifact_changed"],
        )
        d = chk.to_dict()
        assert d["progress_made"] is True
        assert "honest_scope" in d

    def test_progress_made_false(self) -> None:
        chk = JourneyProgressCheck(
            lane="build",
            milestone="scaffold",
            before_level="",
            after_level="",
            progress_made=False,
            progress_type="BLOCKED_NO_SAFE_ACTION",
            next_unlock="produce an artifact",
            blocker="no_progress",
        )
        assert chk.to_dict()["progress_made"] is False


class TestValidators:
    def test_validate_position_valid(self) -> None:
        d = {
            "run_id": "r1",
            "raw_goal": "build x",
            "goal_relevance": "high",
            "current_capability_level": "L2_ARTIFACT_PRODUCING",
        }
        assert validate_position(d) == []

    def test_validate_position_missing_key(self) -> None:
        d = {"run_id": "r1", "raw_goal": "build x", "goal_relevance": "high"}
        errors = validate_position(d)
        assert any("current_capability_level" in e for e in errors)

    def test_validate_position_bad_relevance(self) -> None:
        d = {
            "run_id": "r1",
            "raw_goal": "build x",
            "goal_relevance": "INVALID",
            "current_capability_level": "L2_ARTIFACT_PRODUCING",
        }
        errors = validate_position(d)
        assert any("goal_relevance" in e for e in errors)

    def test_validate_lane_selection_valid(self) -> None:
        d = {
            "primary_lane": "build",
            "selected_milestone": "scaffold",
            "target_gate": "gate",
            "progress_type": "BUILD_ARTIFACT",
            "artifact_that_proves_progress": "file.py",
        }
        assert validate_lane_selection(d) == []

    def test_validate_lane_selection_empty_primary(self) -> None:
        d = {
            "primary_lane": "",
            "selected_milestone": "scaffold",
            "target_gate": "gate",
            "progress_type": "BUILD_ARTIFACT",
            "artifact_that_proves_progress": "file.py",
        }
        errors = validate_lane_selection(d)
        assert any("primary_lane" in e for e in errors)

    def test_validate_gate_alignment_valid(self) -> None:
        d = {
            "lane": "build",
            "release_gate": "gate",
            "success_condition": "ok",
            "failure_condition": "fail",
        }
        assert validate_gate_alignment(d) == []

    def test_validate_progress_check_valid(self) -> None:
        d = {"progress_made": True, "progress_type": "BUILD_ARTIFACT"}
        assert validate_progress_check(d) == []

    def test_validate_progress_check_bad_type(self) -> None:
        d = {"progress_made": True, "progress_type": "NOT_A_REAL_TYPE"}
        errors = validate_progress_check(d)
        assert any("progress_type" in e for e in errors)

    def test_validate_with_generic_lane_id(self) -> None:
        # Validators must NOT reject generic lane IDs like "build", "fix".
        d = {
            "primary_lane": "build",
            "selected_milestone": "scaffold",
            "target_gate": "gate",
            "progress_type": "BUILD_ARTIFACT",
            "artifact_that_proves_progress": "file.py",
        }
        assert validate_lane_selection(d) == []
