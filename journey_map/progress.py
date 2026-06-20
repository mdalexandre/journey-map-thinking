"""Journey progress check: did REAL progress occur (anti-vague)?

Deterministic, no LLM. progress_made is True only when at least one concrete
signal is present: a changed file, a passed gate, a test added, a benchmark run,
a model trained/retired, a real dogfood, or a blocker turned into an unlock
packet. A summary-only run yields no progress and recommends BLOCKED_NO_PROGRESS.

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

from .schema import (
    RELEASE_BLOCKED_NO_PROGRESS,
    JourneyLaneSelection,
    JourneyProgressCheck,
)

_PASSING = ("PASS", "PASS_WITH_WARNINGS")


def check_progress(
    selection: JourneyLaneSelection,
    *,
    changed_files: list[str] | None = None,
    tests_added: bool = False,
    gate_passed: bool = False,
    benchmark_ran: bool = False,
    model_changed: bool = False,
    dogfood_ran: bool = False,
    unlock_packet: bool = False,
    qa_verdict: str = "",
    release_verdict: str = "",
    before_level: str = "",
    after_level: str = "",
    milestone: str = "",
) -> JourneyProgressCheck:
    """Decide whether real journey progress occurred for this run.

    At least one of the following must be True for progress_made to be True:
    changed_files (non-empty), gate_passed, tests_added, benchmark_ran,
    model_changed, dogfood_ran, unlock_packet, or a passing qa_verdict or
    release_verdict.

    Returns:
        A JourneyProgressCheck. When progress_made is False, recommended_release
        is BLOCKED_NO_PROGRESS and the CLI exits 1.
    """
    files = list(changed_files or [])
    gate = (
        gate_passed
        or release_verdict.upper() in _PASSING
        or qa_verdict.upper().startswith("PASS")
    )

    signals: dict[str, bool] = {
        "artifact_changed": bool(files),
        "gate_passed": gate,
        "test_added": tests_added,
        "benchmark_ran": benchmark_ran,
        "model_changed": model_changed,
        "dogfood_ran": dogfood_ran,
        "unlock_packet": unlock_packet,
    }
    evidence = [name for name, on in signals.items() if on]
    if files:
        evidence.append(f"changed_files={len(files)}")
    progress_made = any(signals.values())

    if progress_made:
        progress_type = selection.progress_type
        if unlock_packet and not gate:
            progress_type = "CREATE_OWNER_PACKET"
        blocker: str | None = None
        recommended = ""
        next_unlock = (
            f"advance {selection.primary_lane!r} toward {selection.target_gate}"
        )
    else:
        progress_type = "BLOCKED_NO_SAFE_ACTION"
        blocker = (
            "no_progress: no artifact, gate, test, benchmark, model, dogfood, or unlock packet"
        )
        recommended = RELEASE_BLOCKED_NO_PROGRESS
        next_unlock = (
            "produce a concrete artifact or report a true blocker; never record a summary"
        )

    return JourneyProgressCheck(
        lane=selection.primary_lane,
        milestone=milestone or selection.selected_milestone,
        before_level=before_level,
        after_level=after_level,
        progress_made=progress_made,
        progress_type=progress_type,
        next_unlock=next_unlock,
        evidence=evidence,
        blocker=blocker,
        recommended_release=recommended,
    )
