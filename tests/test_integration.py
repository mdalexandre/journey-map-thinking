"""Integration tests: full 5-stage pipeline via CLI and Python API."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_JM = [sys.executable, "-m", "journey_map.cli"]


def run_jm(*args: str):  # type: ignore[return]
    result = subprocess.run(_JM + list(args), capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


class TestFullPipelineCLI:
    """Full 5-stage CLI pipeline with default catalog and fake data."""

    def test_full_pipeline_exits_zero_with_tests_added(self, tmp_path: Path) -> None:
        raw = tmp_path / "raw_goal.txt"
        raw.write_text("build a CSV ingestion pipeline for sample data", encoding="utf-8")
        root = tmp_path / "jm_map"

        pos_json = tmp_path / "journey_position.json"
        code, out, err = run_jm(
            "position", "--raw", str(raw), "--output", str(pos_json), "--global-root", str(root)
        )
        assert code == 0, f"position failed: {err}"
        assert pos_json.exists()

        lane_json = tmp_path / "journey_lane.json"
        code, out, err = run_jm(
            "select-lane", "--position", str(pos_json), "--output", str(lane_json)
        )
        assert code == 0, f"select-lane failed: {err}"

        gate_json = tmp_path / "journey_gate.json"
        code, out, err = run_jm(
            "align-gate", "--lane", str(lane_json), "--output", str(gate_json)
        )
        assert code == 0, f"align-gate failed: {err}"

        progress_json = tmp_path / "journey_progress.json"
        code, out, err = run_jm(
            "progress",
            "--lane", str(lane_json),
            "--output", str(progress_json),
            "--tests-added",
        )
        assert code == 0, f"progress failed: {err}"

        update_md = tmp_path / "journey_update.md"
        code, out, err = run_jm(
            "update",
            "--progress", str(progress_json),
            "--lane", str(lane_json),
            "--output", str(update_md),
            "--global-root", str(root),
        )
        assert code == 0, f"update failed: {err}"
        assert update_md.exists()
        assert "Journey Map Update" in update_md.read_text()

    def test_no_evidence_pipeline_exits_1_at_progress(self, tmp_path: Path) -> None:
        raw = tmp_path / "raw_goal.txt"
        raw.write_text("build a data pipeline", encoding="utf-8")
        root = tmp_path / "jm_map"

        pos_json = tmp_path / "journey_position.json"
        run_jm("position", "--raw", str(raw), "--output", str(pos_json), "--global-root", str(root))

        lane_json = tmp_path / "journey_lane.json"
        run_jm("select-lane", "--position", str(pos_json), "--output", str(lane_json))

        progress_json = tmp_path / "journey_progress.json"
        code, _, _ = run_jm(
            "progress", "--lane", str(lane_json), "--output", str(progress_json)
        )
        assert code == 1, "no-evidence progress must exit 1"


class TestFullPipelineCustomCatalog:
    """Full 5-stage pipeline with a custom lane catalog."""

    def test_custom_catalog_routes_correctly(
        self, tmp_path: Path, custom_catalog_json: Path
    ) -> None:
        raw = tmp_path / "raw_goal.txt"
        raw.write_text("ingest csv data from a file source", encoding="utf-8")

        pos_json = tmp_path / "pos.json"
        code, out, err = run_jm(
            "position",
            "--raw", str(raw),
            "--output", str(pos_json),
            "--catalog", str(custom_catalog_json),
        )
        assert code == 0, f"position with custom catalog failed: {err}"
        data = json.loads(pos_json.read_text())
        assert "ingest" in data.get("likely_lanes", [])

    def test_custom_catalog_full_pipeline(
        self, tmp_path: Path, custom_catalog_json: Path
    ) -> None:
        raw = tmp_path / "raw_goal.txt"
        raw.write_text("ingest csv data from a file source", encoding="utf-8")
        root = tmp_path / "jm_map"

        pos_json = tmp_path / "pos.json"
        run_jm(
            "position", "--raw", str(raw), "--output", str(pos_json),
            "--catalog", str(custom_catalog_json), "--global-root", str(root),
        )

        lane_json = tmp_path / "lane.json"
        run_jm(
            "select-lane", "--position", str(pos_json), "--output", str(lane_json),
            "--catalog", str(custom_catalog_json),
        )

        gate_json = tmp_path / "gate.json"
        run_jm(
            "align-gate", "--lane", str(lane_json), "--output", str(gate_json),
            "--catalog", str(custom_catalog_json),
        )

        progress_json = tmp_path / "progress.json"
        code, _, _ = run_jm(
            "progress", "--lane", str(lane_json), "--output", str(progress_json),
            "--tests-added",
        )
        assert code == 0

        update_md = tmp_path / "update.md"
        code, _, _ = run_jm(
            "update",
            "--progress", str(progress_json),
            "--lane", str(lane_json),
            "--output", str(update_md),
            "--global-root", str(root),
        )
        assert code == 0


class TestFullPipelinePythonAPI:
    """Full 5-stage pipeline via Python API."""

    def test_python_api_pipeline(self, tmp_path: Path) -> None:
        from journey_map import (
            align_gate,
            check_progress,
            position,
            select_lane,
            update_map,
        )

        raw_goal = "build a CSV ingestion pipeline for sample data"

        pos = position(raw_goal, run_id="api_test")
        assert pos.goal_relevance in ("low", "medium", "high", "direct", "none")

        sel = select_lane(pos)
        assert sel.primary_lane.strip()

        gate = align_gate(sel)
        assert gate.release_gate.strip()

        chk = check_progress(sel, changed_files=["ingestion.py"], tests_added=True)
        assert chk.progress_made is True

        root = tmp_path / "jm_map"
        md = update_map(chk, sel, global_root=str(root), run_id="api_test")
        assert "Journey Map Update" in md

    def test_python_api_no_progress_gate(self) -> None:
        from journey_map import check_progress, position, select_lane

        pos = position("build a new service component")
        sel = select_lane(pos)
        chk = check_progress(sel)
        assert chk.progress_made is False
        assert "BLOCKED_NO_PROGRESS" in chk.recommended_release
