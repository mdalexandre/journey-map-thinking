"""Unit tests for journey_map.update."""
from __future__ import annotations

from pathlib import Path

from journey_map.position import position
from journey_map.progress import check_progress
from journey_map.selector import select_lane
from journey_map.update import render_update_md, update_map


def _pipeline(
    raw_goal: str = "build a CSV ingestion pipeline",
    changed_files: list[str] | None = None,
    tests_added: bool = False,
):  # type: ignore[return]
    pos = position(raw_goal)
    sel = select_lane(pos)
    chk = check_progress(sel, changed_files=changed_files, tests_added=tests_added)
    return sel, chk


class TestRenderUpdateMd:
    def test_renders_progress_status(self) -> None:
        sel, chk = _pipeline(changed_files=["a.py"])
        md = render_update_md(chk, sel)
        assert "PROGRESS" in md

    def test_renders_no_progress_status(self) -> None:
        sel, chk = _pipeline()
        md = render_update_md(chk, sel)
        assert "NO_PROGRESS" in md

    def test_renders_lane(self) -> None:
        sel, chk = _pipeline(changed_files=["a.py"])
        md = render_update_md(chk, sel)
        assert chk.lane in md

    def test_renders_evidence(self) -> None:
        sel, chk = _pipeline(tests_added=True)
        md = render_update_md(chk, sel)
        assert "test_added" in md

    def test_renders_honest_scope(self) -> None:
        sel, chk = _pipeline(changed_files=["a.py"])
        md = render_update_md(chk, sel)
        assert "honest_scope" in md

    def test_renders_scope_walls_certified_false(self) -> None:
        sel, chk = _pipeline(changed_files=["a.py"])
        md = render_update_md(chk, sel)
        assert "scope_walls_certified: false" in md

    def test_renders_blocker_when_no_progress(self) -> None:
        sel, chk = _pipeline()
        md = render_update_md(chk, sel)
        assert "Blocker" in md


class TestUpdateMap:
    def test_update_creates_files(self, tmp_path: Path) -> None:
        sel, chk = _pipeline(changed_files=["a.py"])
        root = tmp_path / "test_map"
        update_map(chk, sel, global_root=str(root))
        assert (root / "journey_history.jsonl").exists()
        assert (root / "current_position.md").exists()
        assert (root / "next_unlocks.json").exists()

    def test_update_appends_history(self, tmp_path: Path) -> None:
        sel, chk = _pipeline(changed_files=["a.py"])
        root = tmp_path / "test_map"
        update_map(chk, sel, global_root=str(root))
        update_map(chk, sel, global_root=str(root))
        lines = (root / "journey_history.jsonl").read_text().strip().splitlines()
        assert len(lines) == 2

    def test_update_writes_completed_milestone_on_progress(self, tmp_path: Path) -> None:
        sel, chk = _pipeline(changed_files=["a.py"])
        root = tmp_path / "test_map"
        update_map(chk, sel, global_root=str(root))
        if chk.progress_made:
            assert (root / "completed_milestones.jsonl").exists()

    def test_update_no_completed_milestone_on_no_progress(self, tmp_path: Path) -> None:
        sel, chk = _pipeline()
        root = tmp_path / "test_map"
        update_map(chk, sel, global_root=str(root))
        p = root / "completed_milestones.jsonl"
        if p.exists():
            assert p.read_text().strip() == ""

    def test_update_returns_markdown_string(self, tmp_path: Path) -> None:
        sel, chk = _pipeline(changed_files=["a.py"])
        md = update_map(chk, sel, global_root=str(tmp_path / "map"))
        assert isinstance(md, str)
        assert "Journey Map Update" in md

    def test_update_with_run_id(self, tmp_path: Path) -> None:
        sel, chk = _pipeline(changed_files=["a.py"])
        root = tmp_path / "test_map"
        md = update_map(chk, sel, global_root=str(root), run_id="my_run_42")
        assert "my_run_42" in md
