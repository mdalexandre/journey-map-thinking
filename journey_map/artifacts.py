"""I/O helpers, global-map seeding, and the feature flag for journey_map.

Atomic writes; the global map under ~/.journey_map/ is append-only for
history and milestones. journey_required() reads JOURNEY_MAP_ENABLED so that
when the flag is off an integrating pipeline can skip journey tracking.

The default root is ~/.journey_map/. Override with the JOURNEY_MAP_ROOT env var
or the --global-root CLI flag.

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from . import lanes as _lanes
from .schema import HONEST_SCOPE, PIPELINE_VISION

# Default location for the global map files (~/.journey_map).
# Override with the JOURNEY_MAP_ROOT environment variable.
# Note: Path("") is PosixPath("."), which is truthy, so an empty/unset env var
# must be checked explicitly; otherwise the home fallback would be dead code.
_ENV_GLOBAL_ROOT = os.environ.get("JOURNEY_MAP_ROOT", "").strip()
DEFAULT_GLOBAL_ROOT = (
    Path(_ENV_GLOBAL_ROOT) if _ENV_GLOBAL_ROOT else Path.home() / ".journey_map"
)

_GLOBAL_FILES = (
    "pipeline_vision.json",
    "journey_lanes.json",
    "component_levels.json",
    "blocker_map.json",
    "completed_milestones.jsonl",
    "journey_history.jsonl",
    "next_unlocks.json",
    "current_position.md",
)


def journey_required() -> bool:
    """True only when JOURNEY_MAP_ENABLED is set truthy (else pipeline is unchanged)."""
    val = os.environ.get("JOURNEY_MAP_ENABLED", "").strip().lower()
    return val in ("1", "true", "yes", "on")


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_json(path: str | Path, obj: Any) -> str:
    """Write obj as JSON to path atomically. Returns the path as a string."""
    p = Path(path)
    _atomic_write(p, json.dumps(obj, indent=2) + "\n")
    return str(p)


def read_json(path: str | Path) -> Any:
    """Read and parse JSON from path."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def append_jsonl(path: str | Path, obj: Any) -> None:
    """Append obj as a JSON line to path (creates the file if absent)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj) + "\n")


def read_text(path: str | Path) -> str:
    """Read and return text from path."""
    return Path(path).read_text(encoding="utf-8")


def read_raw_goal(raw_request_path: str | Path) -> str:
    """Extract the verbatim idea from a raw_request.md, else return the whole text.

    Lines starting with "> " are treated as the quoted idea. If none are found,
    the full file text is returned trimmed.
    """
    text = read_text(raw_request_path)
    quoted = [line[2:].strip() for line in text.splitlines() if line.startswith("> ")]
    if quoted:
        return " ".join(quoted).strip()
    return text.strip()


def read_component_levels(
    root: str | Path = "",
) -> dict[str, str]:
    """Read component capability levels from the global map.

    Returns an empty dict if the file does not exist.
    """
    base = Path(root) if root else DEFAULT_GLOBAL_ROOT
    p = base / "component_levels.json"
    if not p.exists():
        return {}
    data = read_json(p)
    levels = data.get("levels", data) if isinstance(data, dict) else {}
    return {str(k): str(v) for k, v in levels.items()} if isinstance(levels, dict) else {}


def seed_global_map(
    root: str | Path = "",
) -> dict[str, str]:
    """Create the global journey-map files (idempotent for the append-only logs).

    Returns:
        A dict mapping file names to their absolute paths.
    """
    base = Path(root) if root else DEFAULT_GLOBAL_ROOT
    base.mkdir(parents=True, exist_ok=True)

    write_json(
        base / "pipeline_vision.json",
        {
            "pipeline_vision": PIPELINE_VISION,
            "meaning": [
                "the user gives a small idea",
                "the pipeline understands the deeper goal",
                "the pipeline writes the prompt it needs and executes it",
                "the pipeline builds real artifacts and verifies them",
                "the pipeline learns from failure and safely promotes components",
                "the pipeline pushes the journey forward",
            ],
            "honest_scope": HONEST_SCOPE,
        },
    )

    write_json(
        base / "journey_lanes.json",
        {
            "lanes": [lane.to_dict() for lane in _lanes.all_lanes()],
            "honest_scope": HONEST_SCOPE,
        },
    )

    write_json(
        base / "component_levels.json",
        {
            "note": "PROVISIONAL level estimates per lane component; not certified facts.",
            "levels": {
                lane.component: lane.provisional_level for lane in _lanes.all_lanes()
            },
            "honest_scope": HONEST_SCOPE,
        },
    )

    write_json(
        base / "blocker_map.json",
        {
            "blockers": {
                lane.lane_id: {
                    "blockers": lane.blockers,
                    "owner_dependent": lane.owner_dependent,
                    "next_unlocks": lane.next_unlocks,
                }
                for lane in _lanes.all_lanes()
                if lane.blockers
            },
            "honest_scope": HONEST_SCOPE,
        },
    )

    write_json(
        base / "next_unlocks.json",
        {
            "next_unlocks": {
                lane.lane_id: (lane.next_unlocks[0] if lane.next_unlocks else "")
                for lane in _lanes.all_lanes()
            },
            "honest_scope": HONEST_SCOPE,
        },
    )

    # Append-only logs: create only if absent.
    for name in ("completed_milestones.jsonl", "journey_history.jsonl"):
        p = base / name
        if not p.exists():
            p.write_text("", encoding="utf-8")

    _atomic_write(
        base / "current_position.md",
        (
            "# Current Journey Position\n\n"
            f"Pipeline vision: {PIPELINE_VISION}\n\n"
            "Seeded global map. Per-run positions are written by the journey_map CLI.\n\n"
            f"honest_scope: {HONEST_SCOPE}\nscope_walls_certified: false\n"
        ),
    )

    return {name: str(base / name) for name in _GLOBAL_FILES}
