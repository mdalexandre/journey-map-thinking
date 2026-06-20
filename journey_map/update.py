"""Journey map update: record real progress into the persistent global map.

Append-only history and milestones; updates next_unlocks and current_position.
Never records progress the progress check did not establish.

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

from pathlib import Path

from . import artifacts as _art
from .schema import HONEST_SCOPE, JourneyLaneSelection, JourneyProgressCheck


def update_map(
    progress: JourneyProgressCheck,
    selection: JourneyLaneSelection,
    *,
    global_root: str | Path = "",
    run_id: str = "",
    release_verdict: str = "",
) -> str:
    """Update the global journey map from a progress check.

    Args:
        progress: The JourneyProgressCheck from check_progress().
        selection: The JourneyLaneSelection from select_lane().
        global_root: Directory for the global map files. Defaults to
            artifacts.DEFAULT_GLOBAL_ROOT.
        run_id: Optional identifier for this run.
        release_verdict: Optional release verdict string.

    Returns:
        The markdown text of the journey map update.
    """
    root = global_root or _art.DEFAULT_GLOBAL_ROOT
    base = Path(root)
    base.mkdir(parents=True, exist_ok=True)

    history_entry = {
        "run_id": run_id or "journey_update",
        "lane": progress.lane,
        "milestone": progress.milestone,
        "progress_made": progress.progress_made,
        "progress_type": progress.progress_type,
        "evidence": progress.evidence,
        "blocker": progress.blocker,
        "release_verdict": release_verdict,
    }
    _art.append_jsonl(base / "journey_history.jsonl", history_entry)

    if progress.progress_made:
        _art.append_jsonl(
            base / "completed_milestones.jsonl",
            {
                "run_id": run_id or "journey_update",
                "lane": progress.lane,
                "milestone": progress.milestone,
                "progress_type": progress.progress_type,
            },
        )

    # Update next_unlocks for this lane.
    next_path = base / "next_unlocks.json"
    if next_path.exists():
        data = _art.read_json(next_path)
        unlocks = data.get("next_unlocks", {}) if isinstance(data, dict) else {}
    else:
        unlocks = {}
    unlocks[progress.lane] = progress.next_unlock
    _art.write_json(next_path, {"next_unlocks": unlocks, "honest_scope": HONEST_SCOPE})

    md = render_update_md(
        progress, selection, run_id=run_id, release_verdict=release_verdict
    )
    (base / "current_position.md").write_text(md, encoding="utf-8")
    return md


def render_update_md(
    progress: JourneyProgressCheck,
    selection: JourneyLaneSelection,
    *,
    run_id: str = "",
    release_verdict: str = "",
) -> str:
    """Render the journey map update as a markdown string."""
    status = "PROGRESS" if progress.progress_made else "NO_PROGRESS"
    lines = [
        "# Journey Map Update",
        "",
        f"Run: {run_id or 'journey_update'}",
        f"Lane: {progress.lane} ({selection.primary_lane})",
        f"Milestone: {progress.milestone}",
        f"Status: **{status}** (progress_type={progress.progress_type})",
        (
            f"Capability level: "
            f"{progress.before_level or 'n/a'} -> {progress.after_level or 'n/a'}"
        ),
        f"Release verdict: {release_verdict or 'n/a'}",
        "",
        "## Evidence",
        "",
    ]
    lines += [f"- {e}" for e in progress.evidence] or ["- (none)"]
    if progress.blocker:
        lines += ["", "## Blocker", "", progress.blocker]
    lines += [
        "",
        "## Next unlock",
        "",
        progress.next_unlock,
        "",
        f"honest_scope: {HONEST_SCOPE}",
        "scope_walls_certified: false",
    ]
    return "\n".join(lines) + "\n"
