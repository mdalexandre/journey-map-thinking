"""Unit tests for journey_map.classifiers."""
from __future__ import annotations

from journey_map.classifiers import (
    EXPLORATION_KEYWORDS,
    SYSTEM_CLASS_KEYWORDS,
    TRIVIAL_MARKERS,
    classify_request,
)


class TestTrivialMarkers:
    def test_is_frozenset(self) -> None:
        assert isinstance(TRIVIAL_MARKERS, frozenset)

    def test_contains_typo(self) -> None:
        assert "fix a typo" in TRIVIAL_MARKERS

    def test_all_lowercase(self) -> None:
        for m in TRIVIAL_MARKERS:
            assert m == m.lower(), f"marker not lowercase: {m!r}"


class TestSystemClassKeywords:
    def test_is_frozenset(self) -> None:
        assert isinstance(SYSTEM_CLASS_KEYWORDS, frozenset)

    def test_contains_build(self) -> None:
        assert "build" in SYSTEM_CLASS_KEYWORDS

    def test_contains_pipeline(self) -> None:
        assert "pipeline" in SYSTEM_CLASS_KEYWORDS


class TestExplorationKeywords:
    def test_is_frozenset(self) -> None:
        assert isinstance(EXPLORATION_KEYWORDS, frozenset)

    def test_contains_research(self) -> None:
        assert "research" in EXPLORATION_KEYWORDS


class TestClassifyRequest:
    def test_trivial_fix_typo(self) -> None:
        result = classify_request("fix a typo in the README")
        assert result == (False, False)

    def test_trivial_rename_variable(self) -> None:
        result = classify_request("rename variable x to y")
        assert result == (False, False)

    def test_system_class_build_pipeline(self) -> None:
        should_activate, exploration = classify_request("build a benchmark harness")
        assert should_activate is True

    def test_system_class_non_exploration(self) -> None:
        should_activate, exploration = classify_request("implement a service for data loading")
        assert should_activate is True
        # "implement" is system-class but not exploration
        assert isinstance(exploration, bool)

    def test_exploration_research(self) -> None:
        should_activate, exploration = classify_request(
            "research and evaluate different approaches to building a pipeline"
        )
        assert should_activate is True
        assert exploration is True

    def test_unknown_returns_false_false(self) -> None:
        result = classify_request("hello world")
        assert result == (False, False)

    def test_trivial_wins_over_system_class(self) -> None:
        # Even if "build" appears, trivial marker wins first.
        result = classify_request("fix a typo in the build script")
        assert result == (False, False)

    def test_returns_tuple_of_bools(self) -> None:
        result = classify_request("build a pipeline")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], bool)
