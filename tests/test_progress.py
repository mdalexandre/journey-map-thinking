"""Unit tests for journey_map.progress."""
from __future__ import annotations

from journey_map.position import position
from journey_map.progress import check_progress
from journey_map.schema import RELEASE_BLOCKED_NO_PROGRESS
from journey_map.selector import select_lane


def _make_selection():  # type: ignore[return]
    pos = position("build a CSV ingestion pipeline")
    return select_lane(pos)


class TestCheckProgressNoEvidence:
    def test_no_signals_means_no_progress(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel)
        assert chk.progress_made is False

    def test_no_progress_recommends_blocked(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel)
        assert chk.recommended_release == RELEASE_BLOCKED_NO_PROGRESS

    def test_no_progress_has_blocker(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel)
        assert chk.blocker is not None

    def test_no_progress_next_unlock_mentions_artifact(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel)
        assert "artifact" in chk.next_unlock.lower()

    def test_no_progress_type_is_blocked(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel)
        assert chk.progress_type == "BLOCKED_NO_SAFE_ACTION"


class TestCheckProgressWithEvidence:
    def test_changed_files_means_progress(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel, changed_files=["ingestion.py"])
        assert chk.progress_made is True

    def test_tests_added_means_progress(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel, tests_added=True)
        assert chk.progress_made is True

    def test_gate_passed_means_progress(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel, gate_passed=True)
        assert chk.progress_made is True

    def test_benchmark_ran_means_progress(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel, benchmark_ran=True)
        assert chk.progress_made is True

    def test_unlock_packet_means_progress(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel, unlock_packet=True)
        assert chk.progress_made is True

    def test_passing_release_verdict_means_progress(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel, release_verdict="PASS")
        assert chk.progress_made is True

    def test_passing_qa_verdict_means_progress(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel, qa_verdict="PASS_WITH_WARNINGS")
        assert chk.progress_made is True

    def test_progress_has_evidence_list(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel, changed_files=["a.py", "b.py"])
        assert "artifact_changed" in chk.evidence

    def test_progress_no_blocker(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel, gate_passed=True)
        assert chk.blocker is None

    def test_progress_no_recommended_release(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel, gate_passed=True)
        assert chk.recommended_release == ""

    def test_unlock_packet_without_gate_is_owner_packet(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel, unlock_packet=True, gate_passed=False)
        assert chk.progress_type == "CREATE_OWNER_PACKET"

    def test_milestone_override(self) -> None:
        sel = _make_selection()
        chk = check_progress(sel, changed_files=["x.py"], milestone="custom milestone")
        assert chk.milestone == "custom milestone"


class TestCheckProgressLevels:
    def test_before_after_level_propagated(self) -> None:
        sel = _make_selection()
        chk = check_progress(
            sel,
            gate_passed=True,
            before_level="L1_CALLABLE",
            after_level="L2_ARTIFACT_PRODUCING",
        )
        assert chk.before_level == "L1_CALLABLE"
        assert chk.after_level == "L2_ARTIFACT_PRODUCING"
