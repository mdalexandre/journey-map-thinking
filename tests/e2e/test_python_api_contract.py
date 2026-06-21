"""In-process e2e tests for the journey_map Python API contract.

Tests run against the INSTALLED package using the real check_progress
signature from progress.py. All filesystem writes use pytest tmp_path.
All catalog fixtures are FAKE data only.

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from journey_map import (
    align_gate,
    check_progress,
    position,
    run,
    select_lane,
    update_map,
)
from journey_map.catalog_loader import load_catalog
from journey_map.schema import RELEVANCE

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_GOAL = "build a fake data ingestion component for testing"

# Shared lane selection built once per test via a module-level setup.
# Tests that need a JourneyLaneSelection get it from this helper.
def _make_selection():
    pos = position(_FAKE_GOAL)
    return select_lane(pos)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


def test_five_functions_importable():
    """All five pipeline functions must be importable and callable."""
    for fn in (position, select_lane, align_gate, check_progress, update_map):
        assert callable(fn), f"{fn!r} is not callable"


def test_full_pipeline_happy_path():
    """Full pipeline with real evidence signals must produce progress_made=True."""
    pos = position(_FAKE_GOAL)
    sel = select_lane(pos)
    _ = align_gate(sel)
    chk = check_progress(
        sel,
        changed_files=["fake_ingestion.py"],
        tests_added=True,
    )
    assert chk.progress_made is True
    assert chk.blocker is None


def test_summary_only_is_blocked():
    """No signals at all must yield progress_made=False and BLOCKED_NO_PROGRESS."""
    sel = _make_selection()
    chk = check_progress(sel)
    assert chk.progress_made is False
    assert chk.recommended_release == "BLOCKED_NO_PROGRESS"
    assert chk.blocker is not None


def test_gate_passed_signal_triggers_progress():
    """gate_passed=True alone is sufficient for progress_made=True."""
    sel = _make_selection()
    chk = check_progress(sel, gate_passed=True)
    assert chk.progress_made is True


def test_passing_release_verdict_triggers_progress():
    """release_verdict='PASS' must trigger progress_made=True."""
    sel = _make_selection()
    chk = check_progress(sel, release_verdict="PASS")
    assert chk.progress_made is True


def test_passing_qa_verdict_triggers_progress():
    """qa_verdict starting with 'PASS' must trigger progress_made=True."""
    sel = _make_selection()
    chk = check_progress(sel, qa_verdict="PASS_WITH_WARNINGS")
    assert chk.progress_made is True


def test_non_passing_verdict_does_not_trigger():
    """A verdict string that does not start with PASS must not trigger progress."""
    sel = _make_selection()
    chk = check_progress(sel, release_verdict="SUMMARY_ONLY_NO_SIGNALS")
    assert chk.progress_made is False


def test_resume_pattern_skips_position():
    """A saved JourneyPosition dict can be reconstructed to skip re-running position."""
    pos = position(_FAKE_GOAL)
    pos_dict = pos.to_dict()
    # Reconstruct from the dict (same pattern the CLI uses via _position_from_dict).
    from journey_map.schema import JourneyPosition
    resumed_pos = JourneyPosition(
        run_id=pos_dict.get("run_id", "resumed"),
        raw_goal=pos_dict.get("raw_goal", ""),
        goal_relevance=pos_dict.get("goal_relevance", "low"),
        current_capability_level=pos_dict.get("current_capability_level", "NA"),
        likely_lanes=list(pos_dict.get("likely_lanes", [])),
        known_related_components=list(pos_dict.get("known_related_components", [])),
        known_blockers=list(pos_dict.get("known_blockers", [])),
        owner_dependent=bool(pos_dict.get("owner_dependent", False)),
        can_advance_now=bool(pos_dict.get("can_advance_now", True)),
        anti_loop_warning=pos_dict.get("anti_loop_warning"),
        must_pick_concrete_slice=bool(pos_dict.get("must_pick_concrete_slice", False)),
    )
    sel = select_lane(resumed_pos)
    assert sel.primary_lane, "primary_lane must be non-empty after resume"


def test_custom_json_catalog():
    """Loading the custom JSON catalog fixture must return a non-empty dict."""
    here = Path(__file__).parent.parent / "fixtures" / "custom_lane_catalog.json"
    catalog = load_catalog(str(here))
    assert isinstance(catalog, dict)
    assert len(catalog) >= 1


def test_custom_yaml_catalog():
    """Loading the custom YAML catalog fixture must return a non-empty dict."""
    here = Path(__file__).parent.parent / "fixtures" / "custom_lane_catalog.yaml"
    catalog = load_catalog(str(here))
    assert isinstance(catalog, dict)
    assert len(catalog) >= 1


def test_invalid_json_catalog_raises():
    """A malformed JSON catalog must raise ValueError."""
    here = Path(__file__).parent.parent / "fixtures" / "invalid.json"
    with pytest.raises(ValueError):
        load_catalog(str(here))


def test_malformed_yaml_catalog_raises():
    """A YAML catalog missing the required 'markers' field must raise ValueError."""
    here = Path(__file__).parent.parent / "fixtures" / "malformed_catalog.yaml"
    with pytest.raises(ValueError):
        load_catalog(str(here))


def test_update_map_returns_markdown(tmp_path: Path):
    """update_map must return a string containing at least one '#' heading."""
    sel = _make_selection()
    chk = check_progress(sel, changed_files=["fake_component.py"])
    md = update_map(chk, sel, global_root=str(tmp_path), run_id="e2e_test")
    assert isinstance(md, str)
    assert "#" in md, "update_map result must contain at least one markdown heading"


def test_run_shortcut():
    """The run() convenience wrapper must return a lane and a valid relevance."""
    result = run(_FAKE_GOAL)
    assert result.lane, "lane must be non-empty"
    assert result.relevance in RELEVANCE, f"relevance {result.relevance!r} not in RELEVANCE"


def test_no_network_flag_set():
    """JOURNEY_MAP_NO_NETWORK must be '1' when running inside the Docker container."""
    val = os.environ.get("JOURNEY_MAP_NO_NETWORK")
    if val is None:
        pytest.skip("JOURNEY_MAP_NO_NETWORK not set (not running inside Docker container)")
    assert val == "1", f"expected JOURNEY_MAP_NO_NETWORK=1, got {val!r}"
