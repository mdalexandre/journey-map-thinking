"""journey_map CLI: position -> select-lane -> align-gate -> progress -> update.

Deterministic; chains the per-session journey artifacts. Each subcommand reads
its inputs and writes one artifact. `seed` creates the global map.

Usage::

    jm position --raw raw_request.md --output journey_position.json
    jm select-lane --position journey_position.json --output journey_lane.json
    jm align-gate --lane journey_lane.json --output journey_gate_alignment.json
    jm progress --lane journey_lane.json --output journey_progress_check.json
    jm update --progress journey_progress_check.json --lane journey_lane.json \\
        --output journey_map_update.md
    jm seed

Exit codes: 0 ok, 1 no-progress (for `progress`), 2 error, 3 usage.

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from . import artifacts as _art
from .catalog_loader import load_catalog
from .gate_alignment import align_gate as _align_gate
from .position import position as _position
from .progress import check_progress as _check_progress
from .runner import run as _run
from .schema import JourneyLaneSelection, JourneyPosition, JourneyProgressCheck
from .selector import select_lane as _select_lane
from .update import update_map as _update_map


def _load_catalog_from_args(catalog_path: str) -> dict | None:  # type: ignore[type-arg]
    if catalog_path:
        return load_catalog(catalog_path)
    # load_catalog will check JOURNEY_MAP_CATALOG env var and fall back to default.
    return load_catalog()


def _position_from_dict(d: dict[str, Any]) -> JourneyPosition:
    return JourneyPosition(
        run_id=d.get("run_id", "journey_position"),
        raw_goal=d.get("raw_goal", ""),
        goal_relevance=d.get("goal_relevance", "low"),
        current_capability_level=d.get("current_capability_level", "NA"),
        likely_lanes=list(d.get("likely_lanes", [])),
        known_related_components=list(d.get("known_related_components", [])),
        known_blockers=list(d.get("known_blockers", [])),
        owner_dependent=bool(d.get("owner_dependent", False)),
        can_advance_now=bool(d.get("can_advance_now", True)),
        anti_loop_warning=d.get("anti_loop_warning"),
        must_pick_concrete_slice=bool(d.get("must_pick_concrete_slice", False)),
    )


def _selection_from_dict(d: dict[str, Any]) -> JourneyLaneSelection:
    return JourneyLaneSelection(
        primary_lane=d.get("primary_lane", ""),
        selected_milestone=d.get("selected_milestone", ""),
        target_gate=d.get("target_gate", ""),
        progress_type=d.get("progress_type", "BUILD_ARTIFACT"),
        why_this_lane=d.get("why_this_lane", ""),
        artifact_that_proves_progress=d.get("artifact_that_proves_progress", ""),
        secondary_lanes=list(d.get("secondary_lanes", [])),
        what_not_to_repeat=list(d.get("what_not_to_repeat", [])),
    )


def _progress_from_dict(d: dict[str, Any]) -> JourneyProgressCheck:
    return JourneyProgressCheck(
        lane=d.get("lane", ""),
        milestone=d.get("milestone", ""),
        before_level=d.get("before_level", ""),
        after_level=d.get("after_level", ""),
        progress_made=bool(d.get("progress_made", False)),
        progress_type=d.get("progress_type", "BLOCKED_NO_SAFE_ACTION"),
        next_unlock=d.get("next_unlock", ""),
        evidence=list(d.get("evidence", [])),
        blocker=d.get("blocker"),
        recommended_release=d.get("recommended_release", ""),
    )


def _cmd_position(args: argparse.Namespace) -> int:
    catalog = _load_catalog_from_args(getattr(args, "catalog", ""))
    raw_goal = _art.read_raw_goal(args.raw)
    levels = _art.read_component_levels(args.global_root)
    pos = _position(raw_goal, run_id=args.run_id, component_levels=levels, catalog=catalog)
    _art.write_json(args.output, pos.to_dict())
    print(
        f"OK: relevance={pos.goal_relevance} lanes={pos.likely_lanes} "
        f"owner_dependent={pos.owner_dependent} anti_loop={bool(pos.anti_loop_warning)}"
    )
    return 0


def _cmd_select_lane(args: argparse.Namespace) -> int:
    catalog = _load_catalog_from_args(getattr(args, "catalog", ""))
    pos = _position_from_dict(_art.read_json(args.position))
    ambition = None
    if args.ambition and Path(args.ambition).exists():
        ambition = _art.read_json(args.ambition)
    sel = _select_lane(pos, ambition, catalog=catalog)
    _art.write_json(args.output, sel.to_dict())
    print(
        f"OK: primary_lane={sel.primary_lane} milestone={sel.selected_milestone!r} "
        f"progress_type={sel.progress_type}"
    )
    return 0


def _cmd_align_gate(args: argparse.Namespace) -> int:
    catalog = _load_catalog_from_args(getattr(args, "catalog", ""))
    sel = _selection_from_dict(_art.read_json(args.lane))
    spec_text = (
        _art.read_text(args.spec) if args.spec and Path(args.spec).exists() else ""
    )
    gate = _align_gate(sel, spec_text, catalog=catalog)
    _art.write_json(args.output, gate.to_dict())
    print(f"OK: lane={gate.lane} release_gate={gate.release_gate!r}")
    return 0


def _cmd_progress(args: argparse.Namespace) -> int:
    sel = _selection_from_dict(_art.read_json(args.lane))
    release_verdict = ""
    if args.release_verdict and Path(args.release_verdict).exists():
        rv = _art.read_json(args.release_verdict)
        release_verdict = str(rv.get("verdict", "")) if isinstance(rv, dict) else ""
    changed: list[str] = []
    if args.generator_log and Path(args.generator_log).exists():
        text = _art.read_text(args.generator_log)
        # Conservative signal: a non-empty generator log reporting changed files.
        if "changed" in text.lower() or "| change" in text.lower():
            changed = ["generator_log reports changed files"]
    chk = _check_progress(
        sel,
        changed_files=changed,
        release_verdict=release_verdict,
        tests_added=args.tests_added,
        dogfood_ran=args.dogfood_ran,
        before_level=args.before_level,
        after_level=args.after_level,
    )
    _art.write_json(args.output, chk.to_dict())
    print(
        f"OK: progress_made={chk.progress_made} type={chk.progress_type} "
        f"recommended_release={chk.recommended_release or 'n/a'}"
    )
    return 0 if chk.progress_made else 1


def _cmd_update(args: argparse.Namespace) -> int:
    chk = _progress_from_dict(_art.read_json(args.progress))
    sel = _selection_from_dict(_art.read_json(args.lane))
    release_verdict = ""
    if args.release_verdict and Path(args.release_verdict).exists():
        rv = _art.read_json(args.release_verdict)
        release_verdict = str(rv.get("verdict", "")) if isinstance(rv, dict) else ""
    md = _update_map(
        chk,
        sel,
        global_root=args.global_root,
        run_id=args.run_id,
        release_verdict=release_verdict,
    )
    Path(args.output).write_text(md, encoding="utf-8")
    print(f"OK: wrote {args.output}; history appended at {args.global_root}")
    return 0


def _cmd_seed(args: argparse.Namespace) -> int:
    files = _art.seed_global_map(args.global_root)
    print(f"OK: seeded {len(files)} global files at {args.global_root}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    """Run the 3-stage orientation pipeline and print prose or JSON."""
    catalog: dict | None = None
    if getattr(args, "catalog", ""):
        catalog = load_catalog(args.catalog)

    result = _run(args.goal, catalog=catalog)

    if getattr(args, "out", ""):
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        _art.write_json(str(out_dir / "journey_position.json"), result.position.to_dict())
        _art.write_json(str(out_dir / "journey_lane.json"), result.lane_selection.to_dict())
        _art.write_json(
            str(out_dir / "journey_gate_alignment.json"), result.gate_alignment.to_dict()
        )

    if getattr(args, "json", False):
        import json as _json

        payload = {
            "relevance": result.relevance,
            "lane": result.lane,
            "next_move": result.next_move,
            "target_gate": result.target_gate,
            "can_advance_now": result.can_advance_now,
            "honest_scope": "PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE",
        }
        print(_json.dumps(payload))
    else:
        print(result.summary())

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the jm CLI."""
    parser = argparse.ArgumentParser(
        prog="jm",
        description="Journey Map Thinking layer CLI (deterministic, no LLM).",
    )
    sub = parser.add_subparsers(dest="command")
    default_root = str(_art.DEFAULT_GLOBAL_ROOT)

    p = sub.add_parser("position", help="Locate a task on the journey map.")
    p.add_argument("--raw", required=True, help="Path to a raw goal file.")
    p.add_argument("--output", required=True, help="Output path for journey_position.json.")
    p.add_argument("--run-id", default="", dest="run_id")
    p.add_argument("--global-root", default=default_root, dest="global_root")
    p.add_argument("--catalog", default="", help="Path to a custom lane catalog (JSON or YAML).")
    p.set_defaults(func=_cmd_position)

    s = sub.add_parser("select-lane", help="Select the journey lane.")
    s.add_argument("--position", required=True, help="Path to journey_position.json.")
    s.add_argument("--ambition", default="", help="Optional path to a latent-ambition JSON.")
    s.add_argument("--output", required=True, help="Output path for journey_lane.json.")
    s.add_argument("--catalog", default="", help="Path to a custom lane catalog (JSON or YAML).")
    s.set_defaults(func=_cmd_select_lane)

    a = sub.add_parser("align-gate", help="Align the Planner gate.")
    a.add_argument("--lane", required=True, help="Path to journey_lane.json.")
    a.add_argument("--spec", default="", help="Optional path to a spec file.")
    a.add_argument("--output", required=True, help="Output path for journey_gate_alignment.json.")
    a.add_argument("--catalog", default="", help="Path to a custom lane catalog (JSON or YAML).")
    a.set_defaults(func=_cmd_align_gate)

    pr = sub.add_parser("progress", help="Check whether real progress occurred.")
    pr.add_argument("--lane", required=True, help="Path to journey_lane.json.")
    pr.add_argument("--release-verdict", default="", dest="release_verdict")
    pr.add_argument("--generator-log", default="", dest="generator_log")
    pr.add_argument("--tests-added", action="store_true", dest="tests_added")
    pr.add_argument("--dogfood-ran", action="store_true", dest="dogfood_ran")
    pr.add_argument("--before-level", default="", dest="before_level")
    pr.add_argument("--after-level", default="", dest="after_level")
    pr.add_argument("--output", required=True, help="Output path for journey_progress_check.json.")
    pr.set_defaults(func=_cmd_progress)

    u = sub.add_parser("update", help="Update the global journey map.")
    u.add_argument("--progress", required=True, help="Path to journey_progress_check.json.")
    u.add_argument("--lane", required=True, help="Path to journey_lane.json.")
    u.add_argument("--output", required=True, help="Output path for journey_map_update.md.")
    u.add_argument("--run-id", default="", dest="run_id")
    u.add_argument("--release-verdict", default="", dest="release_verdict")
    u.add_argument("--global-root", default=default_root, dest="global_root")
    u.set_defaults(func=_cmd_update)

    sd = sub.add_parser("seed", help="Seed the global journey map files.")
    sd.add_argument("--global-root", default=default_root, dest="global_root")
    sd.set_defaults(func=_cmd_seed)

    rn = sub.add_parser(
        "run",
        help="Orientation shortcut: position -> select-lane -> align-gate in one command.",
    )
    rn.add_argument("goal", help="Raw goal string (what do you want to do?).")
    rn.add_argument(
        "--catalog",
        default="",
        help="Path to a custom lane catalog (JSON or YAML).",
    )
    rn.add_argument(
        "--out",
        default="",
        help=(
            "If set, write journey_position.json, journey_lane.json, and "
            "journey_gate_alignment.json into this directory."
        ),
    )
    rn.add_argument(
        "--json",
        action="store_true",
        dest="json",
        help="Print machine-readable JSON instead of prose summary.",
    )
    rn.set_defaults(func=_cmd_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the jm CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 3
    try:
        return int(args.func(args))
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
