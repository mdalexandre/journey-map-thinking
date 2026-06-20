"""Unit tests for journey_map.artifacts."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from journey_map.artifacts import (
    DEFAULT_GLOBAL_ROOT,
    append_jsonl,
    journey_required,
    read_component_levels,
    read_json,
    read_raw_goal,
    read_text,
    seed_global_map,
    write_json,
)


class TestJourneyRequired:
    def test_false_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("JOURNEY_MAP_ENABLED", raising=False)
        assert journey_required() is False

    def test_true_when_set_to_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("JOURNEY_MAP_ENABLED", "1")
        assert journey_required() is True

    def test_true_when_set_to_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("JOURNEY_MAP_ENABLED", "true")
        assert journey_required() is True

    def test_false_when_set_to_0(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("JOURNEY_MAP_ENABLED", "0")
        assert journey_required() is False

    def test_reads_journey_map_enabled_only(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # journey_required must read JOURNEY_MAP_ENABLED only; an unrelated
        # environment flag must not enable it.
        monkeypatch.delenv("JOURNEY_MAP_ENABLED", raising=False)
        monkeypatch.setenv("UNRELATED_ENABLE_FLAG", "1")
        assert journey_required() is False


class TestDefaultGlobalRoot:
    def test_default_root_is_dot_journey_map(self) -> None:
        root_str = str(DEFAULT_GLOBAL_ROOT).replace("\\", "/").rstrip("/")
        assert root_str.endswith(".journey_map"), (
            f"default global root should end with .journey_map, got {root_str!r}"
        )


class TestReadWriteJSON:
    def test_write_then_read_json(self, tmp_path: Path) -> None:
        p = tmp_path / "test.json"
        obj = {"key": "value", "n": 42}
        write_json(p, obj)
        result = read_json(p)
        assert result == obj

    def test_write_json_is_atomic(self, tmp_path: Path) -> None:
        p = tmp_path / "atomic.json"
        write_json(p, {"x": 1})
        assert p.exists()
        # No .tmp files remain.
        assert not list(tmp_path.glob("*.tmp"))


class TestAppendJsonl:
    def test_append_creates_file(self, tmp_path: Path) -> None:
        p = tmp_path / "log.jsonl"
        append_jsonl(p, {"event": "a"})
        assert p.exists()

    def test_append_adds_lines(self, tmp_path: Path) -> None:
        p = tmp_path / "log.jsonl"
        append_jsonl(p, {"event": "a"})
        append_jsonl(p, {"event": "b"})
        lines = p.read_text().strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["event"] == "a"
        assert json.loads(lines[1])["event"] == "b"


class TestReadText:
    def test_read_text(self, tmp_path: Path) -> None:
        p = tmp_path / "file.txt"
        p.write_text("hello world", encoding="utf-8")
        assert read_text(p) == "hello world"


class TestReadRawGoal:
    def test_extracts_quoted_idea(self, tmp_path: Path) -> None:
        p = tmp_path / "raw.md"
        p.write_text("# Task\n\n> build a CSV ingestion pipeline\n\nContext.\n")
        goal = read_raw_goal(p)
        assert goal == "build a CSV ingestion pipeline"

    def test_returns_whole_text_when_no_quote(self, tmp_path: Path) -> None:
        p = tmp_path / "raw.txt"
        p.write_text("build a CSV ingestion pipeline", encoding="utf-8")
        goal = read_raw_goal(p)
        assert "build a CSV ingestion pipeline" in goal

    def test_multiple_quoted_lines_joined(self, tmp_path: Path) -> None:
        p = tmp_path / "raw.md"
        p.write_text("> build a pipeline\n> for CSV data\n")
        goal = read_raw_goal(p)
        assert "build a pipeline" in goal
        assert "for CSV data" in goal


class TestReadComponentLevels:
    def test_returns_empty_when_no_file(self, tmp_path: Path) -> None:
        result = read_component_levels(tmp_path)
        assert result == {}

    def test_reads_levels_from_file(self, tmp_path: Path) -> None:
        data = {"levels": {"build": "L3_TESTED"}, "honest_scope": "x"}
        write_json(tmp_path / "component_levels.json", data)
        result = read_component_levels(tmp_path)
        assert result["build"] == "L3_TESTED"


class TestSeedGlobalMap:
    def test_seed_creates_expected_files(self, tmp_path: Path) -> None:
        root = tmp_path / "global_map"
        files = seed_global_map(root)
        assert len(files) >= 6
        assert (root / "pipeline_vision.json").exists()
        assert (root / "journey_lanes.json").exists()

    def test_seed_idempotent(self, tmp_path: Path) -> None:
        root = tmp_path / "global_map"
        seed_global_map(root)
        seed_global_map(root)
        # Append-only logs should still exist.
        assert (root / "journey_history.jsonl").exists()

    def test_pipeline_vision_is_generic(self, tmp_path: Path) -> None:
        root = tmp_path / "global_map"
        seed_global_map(root)
        data = read_json(root / "pipeline_vision.json")
        vision_str = str(data).lower()
        # No absolute user-home paths leak into the seeded vision content.
        assert "/home/" not in vision_str
        assert "/users/" not in vision_str
