"""Security and privacy tests.

All tests are deterministic filesystem or text checks. No LLM, no network.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

# Root of the public repo under test.
REPO_ROOT = Path(__file__).resolve().parents[1]

# Privacy pattern: GENERIC structural identifiers that must NOT appear in any
# published file. We screen for email addresses and absolute user-home paths
# only. We deliberately do NOT hardcode personal names or private project names
# here, because publishing such a denylist would itself leak the very tokens it
# is meant to keep out. A maintainer who wants a stricter local check can add
# private tokens to a gitignored tests/privacy_denylist.local.txt (one per line).
_PRIVACY_PATTERN = re.compile(
    r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    r"|/home/[A-Za-z0-9._-]+/"
    r"|/Users/[A-Za-z0-9._-]+/)",
    re.IGNORECASE,
)


def _extra_denylist_tokens() -> list[str]:
    """Load optional private tokens from a gitignored local denylist.

    Returns an empty list when the file is absent (the public default), so the
    published repository never has to name the tokens it screens for.
    """
    deny = Path(__file__).with_name("privacy_denylist.local.txt")
    if not deny.exists():
        return []
    return [
        line.strip()
        for line in deny.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

# Secret pattern.
_SECRET_PATTERN = re.compile(
    # sk- requires the real key shape (sk- plus a long key body); the bare prefix
    # also matches ordinary English ("task-success", "ask-", "risk-", "disk-").
    r"(api_key|password|bearer|basic_auth|-----BEGIN|ghp_|\bsk-[A-Za-z0-9_-]{16,}|AKIA)",
    re.IGNORECASE,
)

# Network call pattern (subprocess/socket in package source).
_NETWORK_PATTERN = re.compile(
    r"(subprocess\.|os\.system|socket\.|urllib\.request|http\.client)",
)

# Superiority claim pattern.
_SUPERIORITY_PATTERN = re.compile(
    r"(beats /compact|empirically superior|improves reasoning|guarantees progress"
    r"|proves better next actions|outperforms|proven to improve)",
    re.IGNORECASE,
)

# File extensions to check for privacy/secret patterns.
_CHECKED_EXTENSIONS = {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".txt", ".rst"}

# Directories to exclude from privacy checks.
# Note: tests/ and .github/workflows/ are excluded because they contain
# the privacy-pattern strings as data (test assertions, CI grep commands).
_EXCLUDED_DIRS = {
    ".git", "__pycache__", ".venv", "dist", "build", ".mypy_cache", ".pytest_cache",
    ".ruff_cache",
    "tests",  # test files contain pattern strings as string literals.
    # Gitignored local scratch: pipeline run artifacts and packaging caches that
    # are never published. They legitimately contain the scanned-for strings as
    # tool output, so they must not be scanned on a developer's working tree
    # (a clean CI checkout has none of these, which is why CI stayed green).
    ".runs", "journey_map_thinking.egg-info",
}

# Files excluded from the privacy check (contain patterns as shell or regex data).
_EXCLUDED_FILES = {
    "ci.yml", "ci_example.yml",  # CI grep commands include the pattern string.
}


def _all_checked_files(root: Path) -> list[Path]:
    files = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in _CHECKED_EXTENSIONS:
            if not any(ex in p.parts for ex in _EXCLUDED_DIRS):
                if p.name not in _EXCLUDED_FILES:
                    files.append(p)
    return files


def _all_package_py_files(root: Path) -> list[Path]:
    pkg = root / "journey_map"
    return [p for p in pkg.rglob("*.py") if "__pycache__" not in p.parts]


class TestPrivacy:
    def test_no_private_references(self) -> None:
        deny = [t.lower() for t in _extra_denylist_tokens()]
        matches = []
        for path in _all_checked_files(REPO_ROOT):
            text = path.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(text.splitlines(), start=1):
                low = line.lower()
                if _PRIVACY_PATTERN.search(line) or any(tok in low for tok in deny):
                    matches.append(f"{path.relative_to(REPO_ROOT)}:{i}: {line.strip()!r}")
        assert matches == [], (
            f"Privacy violation: {len(matches)} match(es) found:\n"
            + "\n".join(matches[:20])
        )

    def test_no_local_home_paths(self) -> None:
        home_pattern = re.compile(r"(/home/|/Users/)", re.IGNORECASE)
        matches = []
        for path in _all_checked_files(REPO_ROOT):
            text = path.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(text.splitlines(), start=1):
                if home_pattern.search(line):
                    matches.append(f"{path.relative_to(REPO_ROOT)}:{i}: {line.strip()!r}")
        assert matches == [], (
            "Home path found in published files:\n" + "\n".join(matches[:10])
        )


class TestSecurity:
    def test_no_secret_patterns(self) -> None:
        matches = []
        for path in _all_checked_files(REPO_ROOT):
            if "test_security" in path.name:
                continue  # Skip self-referential test file.
            text = path.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(text.splitlines(), start=1):
                if _SECRET_PATTERN.search(line):
                    matches.append(f"{path.relative_to(REPO_ROOT)}:{i}: {line.strip()!r}")
        assert matches == [], (
            "Secret pattern found:\n" + "\n".join(matches[:10])
        )

    def test_no_network_calls_in_package(self) -> None:
        matches = []
        for path in _all_package_py_files(REPO_ROOT):
            text = path.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(text.splitlines(), start=1):
                if _NETWORK_PATTERN.search(line):
                    matches.append(f"{path.relative_to(REPO_ROOT)}:{i}: {line.strip()!r}")
        assert matches == [], (
            "Network/subprocess call found in package source:\n"
            + "\n".join(matches[:10])
        )


class TestHonesty:
    def test_no_superiority_claims(self) -> None:
        matches = []
        for path in _all_checked_files(REPO_ROOT):
            if path.suffix not in (".md", ".rst"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(text.splitlines(), start=1):
                if _SUPERIORITY_PATTERN.search(line):
                    matches.append(f"{path.relative_to(REPO_ROOT)}:{i}: {line.strip()!r}")
        assert matches == [], (
            "Superiority claim found in docs:\n" + "\n".join(matches[:10])
        )

    def test_research_result_mentions_null(self) -> None:
        result_path = REPO_ROOT / "docs" / "research_result.md"
        assert result_path.exists(), "docs/research_result.md must exist"
        text = result_path.read_text(encoding="utf-8")
        assert "96" in text, "research_result.md must mention 96 trials"
        assert "0.000" in text or "delta" in text.lower(), (
            "research_result.md must mention the null result delta"
        )

    def test_research_result_no_superiority(self) -> None:
        result_path = REPO_ROOT / "docs" / "research_result.md"
        if result_path.exists():
            text = result_path.read_text(encoding="utf-8")
            assert not _SUPERIORITY_PATTERN.search(text), (
                "Superiority claim found in research_result.md"
            )


class TestExamplesUseFakeData:
    def test_examples_no_private_references(self) -> None:
        examples_dir = REPO_ROOT / "examples"
        if not examples_dir.exists():
            pytest.skip("examples/ directory does not exist")
        matches = []
        for path in examples_dir.rglob("*"):
            if path.is_file() and path.suffix in _CHECKED_EXTENSIONS:
                if path.name in _EXCLUDED_FILES:
                    continue  # CI example files contain the pattern as grep data.
                text = path.read_text(encoding="utf-8", errors="replace")
                for i, line in enumerate(text.splitlines(), start=1):
                    if _PRIVACY_PATTERN.search(line):
                        matches.append(f"{path.relative_to(REPO_ROOT)}:{i}: {line.strip()!r}")
        assert matches == [], (
            "Private reference in examples:\n" + "\n".join(matches[:10])
        )


class TestNoFakeProgressGate:
    def test_progress_no_evidence_exits_nonzero(self, tmp_path: Path) -> None:
        import json

        lane_data = {
            "primary_lane": "build",
            "secondary_lanes": [],
            "selected_milestone": "scaffold",
            "target_gate": "artifact exists",
            "progress_type": "BUILD_ARTIFACT",
            "why_this_lane": "test",
            "what_not_to_repeat": [],
            "artifact_that_proves_progress": "artifact.py",
            "honest_scope": "PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE",
        }
        lane_file = tmp_path / "lane.json"
        lane_file.write_text(json.dumps(lane_data), encoding="utf-8")
        out_file = tmp_path / "progress.json"

        result = subprocess.run(
            [sys.executable, "-m", "journey_map.cli", "progress",
             "--lane", str(lane_file), "--output", str(out_file)],
            capture_output=True,
        )
        assert result.returncode != 0, (
            "jm progress with no evidence must exit non-zero (got 0)"
        )
        assert result.returncode == 1, (
            f"Expected exit code 1, got {result.returncode}"
        )
