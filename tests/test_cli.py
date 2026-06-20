"""CLI tests for the jm command."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_JM = [sys.executable, "-m", "journey_map.cli"]


def run_jm(*args: str, input_text: str | None = None, cwd: str | None = None):  # type: ignore[return]
    """Run jm CLI and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        _JM + list(args),
        capture_output=True,
        text=True,
        input=input_text,
        cwd=cwd,
    )
    return result.returncode, result.stdout, result.stderr


class TestJmHelp:
    def test_help_exits_zero(self) -> None:
        code, out, _ = run_jm("--help")
        assert code == 0

    def test_help_lists_subcommands(self) -> None:
        code, out, _ = run_jm("--help")
        for cmd in ("position", "select-lane", "align-gate", "progress", "update", "seed"):
            assert cmd in out

    def test_no_args_exits_3(self) -> None:
        code, _, _ = run_jm()
        assert code == 3

    def test_position_help(self) -> None:
        code, _, _ = run_jm("position", "--help")
        assert code == 0

    def test_select_lane_help(self) -> None:
        code, _, _ = run_jm("select-lane", "--help")
        assert code == 0

    def test_align_gate_help(self) -> None:
        code, _, _ = run_jm("align-gate", "--help")
        assert code == 0

    def test_progress_help(self) -> None:
        code, _, _ = run_jm("progress", "--help")
        assert code == 0

    def test_update_help(self) -> None:
        code, _, _ = run_jm("update", "--help")
        assert code == 0

    def test_seed_help(self) -> None:
        code, _, _ = run_jm("seed", "--help")
        assert code == 0


class TestJmPosition:
    def test_valid_input_exits_zero(self, fake_raw_goal_file: Path, tmp_path: Path) -> None:
        out_path = tmp_path / "pos.json"
        code, _, _ = run_jm(
            "position", "--raw", str(fake_raw_goal_file), "--output", str(out_path)
        )
        assert code == 0
        assert out_path.exists()

    def test_output_is_valid_json(self, fake_raw_goal_file: Path, tmp_path: Path) -> None:
        out_path = tmp_path / "pos.json"
        run_jm("position", "--raw", str(fake_raw_goal_file), "--output", str(out_path))
        data = json.loads(out_path.read_text())
        assert "goal_relevance" in data
        assert "likely_lanes" in data

    def test_missing_raw_file_exits_2(self, tmp_path: Path) -> None:
        out_path = tmp_path / "pos.json"
        code, _, _ = run_jm(
            "position",
            "--raw",
            str(tmp_path / "nonexistent.txt"),
            "--output",
            str(out_path),
        )
        assert code == 2

    def test_with_run_id(self, fake_raw_goal_file: Path, tmp_path: Path) -> None:
        out_path = tmp_path / "pos.json"
        run_jm(
            "position",
            "--raw", str(fake_raw_goal_file),
            "--output", str(out_path),
            "--run-id", "test_run_123",
        )
        data = json.loads(out_path.read_text())
        assert data["run_id"] == "test_run_123"


class TestJmSelectLane:
    def test_valid_position_exits_zero(
        self, fake_position_json: Path, tmp_path: Path
    ) -> None:
        out_path = tmp_path / "lane.json"
        code, _, _ = run_jm(
            "select-lane",
            "--position", str(fake_position_json),
            "--output", str(out_path),
        )
        assert code == 0

    def test_output_has_primary_lane(
        self, fake_position_json: Path, tmp_path: Path
    ) -> None:
        out_path = tmp_path / "lane.json"
        run_jm(
            "select-lane",
            "--position", str(fake_position_json),
            "--output", str(out_path),
        )
        data = json.loads(out_path.read_text())
        assert "primary_lane" in data
        assert data["primary_lane"].strip()

    def test_missing_position_file_exits_2(self, tmp_path: Path) -> None:
        out_path = tmp_path / "lane.json"
        code, _, _ = run_jm(
            "select-lane",
            "--position", str(tmp_path / "nonexistent.json"),
            "--output", str(out_path),
        )
        assert code == 2


class TestJmProgress:
    def test_no_evidence_exits_1(
        self, fake_progress_no_evidence_json: Path, tmp_path: Path
    ) -> None:
        out_path = tmp_path / "progress.json"
        code, out, _ = run_jm(
            "progress",
            "--lane", str(fake_progress_no_evidence_json),
            "--output", str(out_path),
        )
        assert code == 1

    def test_no_evidence_output_has_blocked(
        self, fake_progress_no_evidence_json: Path, tmp_path: Path
    ) -> None:
        out_path = tmp_path / "progress.json"
        run_jm(
            "progress",
            "--lane", str(fake_progress_no_evidence_json),
            "--output", str(out_path),
        )
        data = json.loads(out_path.read_text())
        assert data["progress_made"] is False

    def test_missing_lane_file_exits_2(self, tmp_path: Path) -> None:
        out_path = tmp_path / "progress.json"
        code, _, _ = run_jm(
            "progress",
            "--lane", str(tmp_path / "nonexistent.json"),
            "--output", str(out_path),
        )
        assert code == 2

    def test_tests_added_flag_exits_0(
        self, fake_lane_json: Path, tmp_path: Path
    ) -> None:
        out_path = tmp_path / "progress.json"
        code, _, _ = run_jm(
            "progress",
            "--lane", str(fake_lane_json),
            "--output", str(out_path),
            "--tests-added",
        )
        assert code == 0


class TestJmSeed:
    def test_seed_exits_zero(self, tmp_path: Path) -> None:
        root = tmp_path / "jm_map"
        code, out, _ = run_jm("seed", "--global-root", str(root))
        assert code == 0
        assert "seeded" in out.lower()

    def test_seed_creates_files(self, tmp_path: Path) -> None:
        root = tmp_path / "jm_map"
        run_jm("seed", "--global-root", str(root))
        assert (root / "pipeline_vision.json").exists()
        assert (root / "journey_lanes.json").exists()
