"""Vendored classifiers for request routing.

Deterministic, no LLM, no network. Implements classify_request() using
keyword matching over three frozen sets:

- TRIVIAL_MARKERS: requests too small to track on the journey map.
- SYSTEM_CLASS_KEYWORDS: signals that a request has system-class scope.
- EXPLORATION_KEYWORDS: additional signals for exploration mode.

The three-rule logic:
  1. If TRIVIAL_MARKERS match, return (False, False) immediately.
  2. If SYSTEM_CLASS_KEYWORDS match, should_activate = True.
  3. If EXPLORATION_KEYWORDS also match (only when rule 2 is True), exploration = True.

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

TRIVIAL_MARKERS: frozenset[str] = frozenset(
    {
        "fix a typo",
        "fix typo",
        "rename a variable",
        "rename variable",
        "add a comment",
        "add comment",
        "update readme",
        "update the readme",
        "whitespace",
        "formatting only",
        "format only",
        "reformat",
        "linting",
        "lint only",
        "trivial",
        "minor cleanup",
        "small cleanup",
        "quick fix",
        "one liner",
        "one-liner",
        "docstring only",
        "update docstring",
    }
)

SYSTEM_CLASS_KEYWORDS: frozenset[str] = frozenset(
    {
        "build",
        "create",
        "implement",
        "scaffold",
        "pipeline",
        "system",
        "service",
        "framework",
        "library",
        "benchmark",
        "harness",
        "deploy",
        "integrate",
        "train",
        "optimize",
        "research",
        "architecture",
        "design",
        "evaluate",
        "platform",
        "module",
        "component",
        "api",
        "cli",
        "database",
        "workflow",
        "agent",
    }
)

EXPLORATION_KEYWORDS: frozenset[str] = frozenset(
    {
        "explore",
        "investigate",
        "research",
        "survey",
        "study",
        "analyze",
        "compare",
        "evaluate",
        "benchmark",
        "understand",
        "discover",
        "probe",
        "examine",
        "assess",
    }
)


def classify_request(raw_request: str) -> tuple[bool, bool]:
    """Classify a raw request as (should_activate, exploration).

    Returns:
        (False, False): trivial request; do not activate journey tracking.
        (True, False): system-class request; activate journey tracking.
        (True, True): system-class exploration request; activate with exploration mode.

    The logic is deterministic and purely keyword-based. No LLM, no network.
    """
    text = raw_request.lower()

    # Rule 1: trivial wins first.
    if any(marker in text for marker in TRIVIAL_MARKERS):
        return (False, False)

    # Rule 2: system-class keyword check.
    should_activate = any(keyword in text for keyword in SYSTEM_CLASS_KEYWORDS)
    if not should_activate:
        return (False, False)

    # Rule 3: exploration modifier (only when rule 2 is True).
    exploration = any(keyword in text for keyword in EXPLORATION_KEYWORDS)
    return (True, exploration)
