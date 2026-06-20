"""Shared pytest fixtures for journey_map tests.

All fixtures use fake data only. No real names, paths, or private tokens appear.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture()
def fake_raw_goal_file(tmp_path: Path) -> Path:
    """A fake raw goal text file."""
    p = tmp_path / "raw_goal.txt"
    p.write_text("build a CSV ingestion pipeline for sample data", encoding="utf-8")
    return p


@pytest.fixture()
def fake_raw_goal_md(tmp_path: Path) -> Path:
    """A fake raw_request.md with a quoted idea line."""
    p = tmp_path / "raw_request.md"
    p.write_text(
        "# Task\n\n> build a data pipeline for CSV ingestion\n\nSome context here.\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture()
def fake_position_json(tmp_path: Path) -> Path:
    """A minimal valid journey_position.json."""
    data = {
        "run_id": "test_run",
        "raw_goal": "build a CSV ingestion pipeline",
        "goal_relevance": "high",
        "current_capability_level": "L2_ARTIFACT_PRODUCING",
        "likely_lanes": ["build"],
        "known_related_components": ["build"],
        "known_blockers": [],
        "owner_dependent": False,
        "can_advance_now": True,
        "anti_loop_warning": None,
        "must_pick_concrete_slice": False,
        "honest_scope": "PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE",
    }
    p = tmp_path / "journey_position.json"
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


@pytest.fixture()
def fake_lane_json(tmp_path: Path) -> Path:
    """A minimal valid journey_lane.json."""
    data = {
        "primary_lane": "build",
        "secondary_lanes": [],
        "selected_milestone": "scaffold",
        "target_gate": "artifact exists",
        "progress_type": "BUILD_ARTIFACT",
        "why_this_lane": "markers route to lane 'build'",
        "what_not_to_repeat": ["do not overclaim"],
        "artifact_that_proves_progress": "artifact file",
        "honest_scope": "PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE",
    }
    p = tmp_path / "journey_lane.json"
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


@pytest.fixture()
def fake_progress_no_evidence_json(tmp_path: Path) -> Path:
    """A lane JSON that will produce no-progress when passed to check_progress."""
    data = {
        "primary_lane": "build",
        "secondary_lanes": [],
        "selected_milestone": "scaffold",
        "target_gate": "artifact exists",
        "progress_type": "BUILD_ARTIFACT",
        "why_this_lane": "markers route to lane 'build'",
        "what_not_to_repeat": [],
        "artifact_that_proves_progress": "artifact file",
        "honest_scope": "PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE",
    }
    p = tmp_path / "journey_lane_no_evidence.json"
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


@pytest.fixture()
def custom_catalog_json(tmp_path: Path) -> Path:
    """A minimal custom lane catalog JSON file with fake lanes."""
    lanes = [
        {
            "lane_id": "ingest",
            "name": "Data Ingestion",
            "description": "Build or fix data ingestion pipelines.",
            "component": "ingestion",
            "provisional_level": "L2_ARTIFACT_PRODUCING",
            "markers": ["ingest", "ingestion", "csv pipeline", "data pipeline"],
            "milestones": ["ingestion module"],
            "gates": ["end-to-end test passes"],
            "progress_artifacts": ["ingestion.py"],
        },
        {
            "lane_id": "transform",
            "name": "Data Transform",
            "description": "Transform and clean data.",
            "component": "transform",
            "provisional_level": "L1_CALLABLE",
            "markers": ["transform", "clean data", "normalize"],
            "milestones": ["transformer module"],
            "gates": ["schema validation passes"],
            "progress_artifacts": ["transformer.py"],
        },
        {
            "lane_id": "load",
            "name": "Data Load",
            "description": "Load data into a destination store.",
            "component": "load",
            "provisional_level": "L1_CALLABLE",
            "markers": ["load", "write to", "store", "sink"],
            "milestones": ["loader module"],
            "gates": ["write-round-trip test passes"],
            "progress_artifacts": ["loader.py"],
        },
    ]
    p = tmp_path / "custom_lanes.json"
    p.write_text(json.dumps(lanes, indent=2), encoding="utf-8")
    return p
