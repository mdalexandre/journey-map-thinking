"""Journey lane catalog: the default built-in lanes plus helpers.

The five built-in lanes (build, research, fix, blocked, vision) cover the common
request patterns. Replace them with your own catalog by passing --catalog to the
CLI or by setting the JOURNEY_MAP_CATALOG environment variable.

Each Lane has:
- lane_id: a short string key (e.g. "build", "fix").
- name: a human-readable label.
- component: a short category label (user-defined; not a private internal name).
- description: what tasks belong in this lane.
- provisional_level: starting capability level estimate (L0-L10).
- markers: substrings that route a raw goal to this lane.

honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Lane:
    """One route in the journey catalog."""

    lane_id: str
    name: str
    component: str  # a short category label for this lane; user-defined.
    description: str
    provisional_level: str
    markers: tuple[str, ...]
    milestones: list[str] = field(default_factory=list)
    gates: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    owner_dependent: bool = False
    next_unlocks: list[str] = field(default_factory=list)
    claim_boundary: str = ""
    progress_artifacts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lane_id": self.lane_id,
            "name": self.name,
            "component": self.component,
            "description": self.description,
            "provisional_level": self.provisional_level,
            "markers": list(self.markers),
            "milestones": list(self.milestones),
            "gates": list(self.gates),
            "blockers": list(self.blockers),
            "owner_dependent": self.owner_dependent,
            "next_unlocks": list(self.next_unlocks),
            "claim_boundary": self.claim_boundary,
            "progress_artifacts": list(self.progress_artifacts),
        }


# ---------------------------------------------------------------------------
# Default built-in catalog (5 generic lanes)
# ---------------------------------------------------------------------------

_DEFAULT_LANES: tuple[Lane, ...] = (
    Lane(
        lane_id="build",
        name="Build",
        component="build",
        description="Build a new artifact, project, feature, module, or service.",
        provisional_level="L2_ARTIFACT_PRODUCING",
        markers=(
            "build a",
            "build an",
            "build me",
            "create a",
            "create an",
            "implement",
            "scaffold",
            "write a",
            "make a",
            "make an",
            "develop",
            "ship",
            "produce",
        ),
        milestones=["scaffold", "working module", "release verdict"],
        gates=["artifact exists", "tests pass", "QA report"],
        claim_boundary="no done claim without an artifact-backed release verdict",
        progress_artifacts=["artifact file", "qa_report.md", "release_verdict.json"],
    ),
    Lane(
        lane_id="research",
        name="Research",
        component="research",
        description="Investigate, benchmark, evaluate, or compare an approach.",
        provisional_level="L2_ARTIFACT_PRODUCING",
        markers=(
            "research",
            "investigate",
            "evaluate",
            "compare",
            "benchmark",
            "analyze",
            "analyse",
            "study",
            "survey",
            "measure",
            "assess",
        ),
        milestones=["literature or data gathered", "evaluation report"],
        gates=["evidence gathered", "honest comparison with baseline"],
        claim_boundary="no superiority claim without a fair, reproduced comparison",
        progress_artifacts=["research_report.md", "benchmark_results.json"],
    ),
    Lane(
        lane_id="fix",
        name="Fix",
        component="fix",
        description="Repair a defect, regression, failing test, or broken behavior.",
        provisional_level="L3_TESTED",
        markers=(
            "fix",
            "repair",
            "patch",
            "debug",
            "regression",
            "failing test",
            "broken",
            "defect",
            "bug",
            "error",
            "wrong output",
        ),
        milestones=["root cause identified", "fix applied", "test passes"],
        gates=["test passes", "regression does not reappear"],
        claim_boundary="no fixed claim without a passing test that caught the defect",
        progress_artifacts=["changed files", "test output"],
    ),
    Lane(
        lane_id="blocked",
        name="Blocked",
        component="blocked",
        description=(
            "A blocker requires owner or external action before the pipeline can proceed."
        ),
        provisional_level="L0_CONCEPT",
        markers=(
            "blocked",
            "waiting for",
            "need approval",
            "owner action",
            "requires permission",
            "can't proceed",
            "cannot proceed",
            "pending",
        ),
        milestones=["blocker documented", "unlock packet produced"],
        gates=["blocker clearly named", "owner or external dependency identified"],
        owner_dependent=True,
        next_unlocks=["owner reviews blocker and approves next action"],
        claim_boundary=(
            "no progress claim while blocked; produce the unlock packet only"
        ),
        progress_artifacts=["blocker_report.md", "unlock_packet.md"],
    ),
    Lane(
        lane_id="vision",
        name="Vision",
        component="vision",
        description=(
            "A pure-vision ask: must be grounded into a concrete, buildable first slice."
        ),
        provisional_level="L0_CONCEPT",
        markers=(
            "push humanity forward",
            "change the world",
            "advance humanity",
            "save the world",
            "make everything better",
            "transform",
            "revolutionize",
            "vision for",
        ),
        milestones=["concrete first slice chosen", "routed to a build or research lane"],
        gates=["first slice is specific and buildable"],
        claim_boundary=(
            "no vision milestone claimed; only the first concrete slice counts as progress"
        ),
        progress_artifacts=["first_slice_spec.md"],
    ),
)

LANE_CATALOG: dict[str, Lane] = {lane.lane_id: lane for lane in _DEFAULT_LANES}

# Routing precedence: more specific lanes outrank generic ones.
# "blocked" and "vision" are checked first because their markers are highly specific.
# "build" is last since its markers are common substrings.
MATCH_PRIORITY = ("blocked", "vision", "research", "fix", "build")

# Vision markers that trigger the must_pick_concrete_slice path.
VISION_MARKERS = (
    "push humanity forward",
    "change the world",
    "advance humanity",
    "save the world",
    "push the world forward",
    "make the world better",
    "humanity forward",
)


def all_lanes() -> list[Lane]:
    """Return all lanes in the current catalog as a list."""
    return list(LANE_CATALOG.values())


def get_lane(lane_id: str) -> Lane | None:
    """Return the Lane for lane_id, or None if not found."""
    return LANE_CATALOG.get(lane_id)


def matched_lanes(text: str, catalog: dict[str, Lane] | None = None) -> list[str]:
    """Return lane IDs whose markers appear in text (already lowered), in MATCH_PRIORITY order."""
    cat = catalog if catalog is not None else LANE_CATALOG
    priority = list(cat.keys())  # fallback: catalog insertion order
    # Prefer MATCH_PRIORITY order when using the default catalog.
    if catalog is None:
        priority = [lid for lid in MATCH_PRIORITY if lid in cat]
    hits = [lid for lid in priority if any(m in text for m in cat[lid].markers)]
    return hits


def is_vision(text: str) -> bool:
    """True if text contains a vision-level marker."""
    return any(m in text for m in VISION_MARKERS)
