"""Catalog loader: load a lane catalog from a file or return the built-in default.

Resolution order:
  1. catalog_path argument (if provided).
  2. JOURNEY_MAP_CATALOG environment variable.
  3. Built-in default catalog from lanes.py.

Format detection:
  - .json or JSON content: parsed with stdlib json.
  - .yaml or .yml: requires pyyaml (optional extra). An actionable ImportError
    is raised if pyyaml is not installed.

Validation:
  Each entry must have: lane_id (str), name (str), description (str), markers (list[str]).
  Optional: milestones, gates, blockers, owner_dependent, next_unlocks,
  claim_boundary, progress_artifacts, provisional_level, component.
  Missing required fields raise ValueError naming the field and entry.

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .lanes import LANE_CATALOG, Lane

_REQUIRED_FIELDS = ("lane_id", "name", "description", "markers")
_OPTIONAL_FIELDS = (
    "component",
    "provisional_level",
    "milestones",
    "gates",
    "blockers",
    "owner_dependent",
    "next_unlocks",
    "claim_boundary",
    "progress_artifacts",
)


def _parse_json(text: str, source: str) -> list[dict]:  # type: ignore[type-arg]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"catalog at {source!r} is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(
            f"catalog at {source!r} must be a JSON array of lane objects; got {type(data).__name__}"
        )
    return data  # type: ignore[return-value]


def _parse_yaml(text: str, source: str) -> list[dict]:  # type: ignore[type-arg]
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required to load YAML catalogs. "
            "Install it with: pip install 'journey-map-thinking[yaml]'"
        ) from exc
    data = yaml.safe_load(text)
    if not isinstance(data, list):
        raise ValueError(
            f"catalog at {source!r} must be a YAML sequence of lane objects; "
            f"got {type(data).__name__}"
        )
    return data  # type: ignore[return-value]


def _validate_entry(entry: dict, index: int) -> None:  # type: ignore[type-arg]
    for field in _REQUIRED_FIELDS:
        if field not in entry:
            raise ValueError(
                f"catalog entry [{index}] (lane_id={entry.get('lane_id', '?')!r}) "
                f"is missing required field: {field!r}"
            )
    markers = entry.get("markers")
    if not isinstance(markers, list):
        raise ValueError(
            f"catalog entry [{index}] (lane_id={entry.get('lane_id', '?')!r}): "
            f"'markers' must be a list of strings, got {type(markers).__name__}"
        )
    if not all(isinstance(m, str) for m in markers):
        raise ValueError(
            f"catalog entry [{index}] (lane_id={entry.get('lane_id', '?')!r}): "
            "all items in 'markers' must be strings"
        )


def _entry_to_lane(entry: dict) -> Lane:  # type: ignore[type-arg]
    return Lane(
        lane_id=str(entry["lane_id"]),
        name=str(entry["name"]),
        component=str(entry.get("component", entry["lane_id"])),
        description=str(entry["description"]),
        provisional_level=str(entry.get("provisional_level", "L0_CONCEPT")),
        markers=tuple(str(m) for m in entry["markers"]),
        milestones=list(entry.get("milestones", [])),
        gates=list(entry.get("gates", [])),
        blockers=list(entry.get("blockers", [])),
        owner_dependent=bool(entry.get("owner_dependent", False)),
        next_unlocks=list(entry.get("next_unlocks", [])),
        claim_boundary=str(entry.get("claim_boundary", "")),
        progress_artifacts=list(entry.get("progress_artifacts", [])),
    )


def load_catalog(catalog_path: str | None = None) -> dict[str, Lane]:
    """Load a lane catalog from catalog_path, env var, or the built-in default.

    Args:
        catalog_path: Path to a JSON or YAML file containing a list of lane objects.
            If None, the JOURNEY_MAP_CATALOG environment variable is checked.
            If that is also absent, the built-in default catalog is returned.

    Returns:
        A dict mapping lane_id to Lane.

    Raises:
        ValueError: if the file is malformed or missing required fields.
        ImportError: if a .yaml/.yml file is requested but pyyaml is not installed.
        FileNotFoundError: if the path does not exist.
    """
    path_str = catalog_path or os.environ.get("JOURNEY_MAP_CATALOG", "").strip()
    if not path_str:
        return dict(LANE_CATALOG)

    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"catalog file not found: {path}")

    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix in (".yaml", ".yml"):
        entries = _parse_yaml(text, path_str)
    else:
        entries = _parse_json(text, path_str)

    for i, entry in enumerate(entries):
        _validate_entry(entry, i)

    catalog = {}
    for entry in entries:
        lane = _entry_to_lane(entry)
        catalog[lane.lane_id] = lane
    return catalog
