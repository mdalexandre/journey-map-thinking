"""Unit tests for journey_map.catalog_loader."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from journey_map.catalog_loader import load_catalog
from journey_map.lanes import LANE_CATALOG, Lane


class TestLoadCatalogDefault:
    def test_returns_default_when_no_path(self) -> None:
        cat = load_catalog()
        assert isinstance(cat, dict)
        assert len(cat) == len(LANE_CATALOG)

    def test_default_contains_build_lane(self) -> None:
        cat = load_catalog(None)
        assert "build" in cat

    def test_returns_lane_instances(self) -> None:
        cat = load_catalog()
        for lane in cat.values():
            assert isinstance(lane, Lane)


class TestLoadCatalogJSON:
    def test_load_valid_json_file(self, tmp_path: Path, custom_catalog_json: Path) -> None:
        cat = load_catalog(str(custom_catalog_json))
        assert "ingest" in cat
        assert "transform" in cat
        assert "load" in cat

    def test_loaded_lane_has_correct_fields(
        self, tmp_path: Path, custom_catalog_json: Path
    ) -> None:
        cat = load_catalog(str(custom_catalog_json))
        lane = cat["ingest"]
        assert lane.name == "Data Ingestion"
        assert "csv pipeline" in lane.markers

    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_catalog(str(tmp_path / "nonexistent.json"))

    def test_invalid_json_raises_value_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("not valid json at all {{{{", encoding="utf-8")
        with pytest.raises(ValueError, match="not valid JSON"):
            load_catalog(str(bad))

    def test_json_not_array_raises_value_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad_shape.json"
        bad.write_text(json.dumps({"lane_id": "x"}), encoding="utf-8")
        with pytest.raises(ValueError, match="JSON array"):
            load_catalog(str(bad))

    def test_invalid_catalog_missing_required_field_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        # Missing 'description' field.
        lanes = [{"lane_id": "x", "name": "X", "markers": ["x"]}]
        p = tmp_path / "missing_field.json"
        p.write_text(json.dumps(lanes), encoding="utf-8")
        with pytest.raises(ValueError, match="description"):
            load_catalog(str(p))

    def test_invalid_catalog_missing_lane_id_raises(self, tmp_path: Path) -> None:
        lanes = [{"name": "X", "description": "d", "markers": ["x"]}]
        p = tmp_path / "no_id.json"
        p.write_text(json.dumps(lanes), encoding="utf-8")
        with pytest.raises(ValueError, match="lane_id"):
            load_catalog(str(p))

    def test_invalid_catalog_markers_not_list_raises(self, tmp_path: Path) -> None:
        lanes = [
            {
                "lane_id": "x",
                "name": "X",
                "description": "d",
                "markers": "should-be-a-list",
            }
        ]
        p = tmp_path / "bad_markers.json"
        p.write_text(json.dumps(lanes), encoding="utf-8")
        with pytest.raises(ValueError, match="'markers'"):
            load_catalog(str(p))


class TestLoadCatalogEnvVar:
    def test_env_var_loads_catalog(
        self, tmp_path: Path, custom_catalog_json: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("JOURNEY_MAP_CATALOG", str(custom_catalog_json))
        cat = load_catalog()
        assert "ingest" in cat

    def test_explicit_path_overrides_env_var(
        self, tmp_path: Path, custom_catalog_json: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Set env var to one catalog but pass a different path explicitly.
        other_lanes = [
            {
                "lane_id": "override",
                "name": "Override",
                "description": "Override lane.",
                "markers": ["override marker"],
            }
        ]
        other_path = tmp_path / "other.json"
        other_path.write_text(json.dumps(other_lanes), encoding="utf-8")
        monkeypatch.setenv("JOURNEY_MAP_CATALOG", str(custom_catalog_json))
        cat = load_catalog(str(other_path))
        assert "override" in cat
        assert "ingest" not in cat


class TestLoadCatalogYAML:
    def test_yaml_without_pyyaml_raises_import_error(self, tmp_path: Path) -> None:
        p = tmp_path / "catalog.yaml"
        p.write_text("- lane_id: x\n  name: X\n  description: d\n  markers: [x]\n")
        # We need to simulate pyyaml being absent. Try to import it first.
        try:
            import yaml  # noqa: F401
            pytest.skip("pyyaml is installed; cannot test missing-pyyaml path")
        except ImportError:
            with pytest.raises(ImportError, match="journey-map-thinking"):
                load_catalog(str(p))
