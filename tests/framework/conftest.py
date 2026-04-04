"""
Shared fixtures for framework self-tests.

These tests validate the SSD framework itself (agents, skills, scripts, rules,
templates, data flow contracts). They do NOT test consuming projects.

Usage:
    pytest tests/framework/ -v
    pytest tests/framework/ -k pipeline
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def root() -> Path:
    """Framework root directory."""
    return FRAMEWORK_ROOT


@pytest.fixture
def agents_dir(root: Path) -> Path:
    return root / "agents"


@pytest.fixture
def scripts_dir(root: Path) -> Path:
    return root / "scripts"


@pytest.fixture
def skills_dir(root: Path) -> Path:
    return root / "skills"


@pytest.fixture
def rules_dir(root: Path) -> Path:
    return root / "rules"


@pytest.fixture
def templates_dir(root: Path) -> Path:
    return root / "specs" / "templates"


# ── Helpers ──────────────────────────────────────────────────────────────


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def all_agent_cores(agents_dir: Path) -> list[Path]:
    """Return all core agent files (not .ref.md)."""
    return sorted(p for p in agents_dir.glob("*.md") if not p.name.endswith(".ref.md"))


def parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML frontmatter fields as raw strings."""
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith("#"):
            key, _, val = line.partition(":")
            # Strip inline comments
            val = re.sub(r"\s*#.*$", "", val).strip()
            fields[key.strip()] = val
    return fields


def extract_file_refs(text: str) -> list[str]:
    """Extract file paths referenced in markdown (backticks).

    Only returns references that look like actual filesystem paths:
    - Must contain a `/` (directory separator) to distinguish from code refs
      like `console.log` or `gates.code_review`
    - OR start with a known framework root directory
    """
    refs: list[str] = []
    KNOWN_ROOTS = (
        "agents/", "scripts/", "skills/", "rules/", "specs/",
        "stacks/", "memory/", "prompts/", "_work/", "_docs/",
    )
    for m in re.finditer(r"`([a-zA-Z_./\-\[\]{}]+\.\w+)`", text):
        candidate = m.group(1)
        # Must look like a path (has /) or start with a known root
        if "/" in candidate or any(candidate.startswith(r) for r in KNOWN_ROOTS):
            refs.append(candidate)
    # Directory references like `agents/` or `stacks/`
    for m in re.finditer(r"`([a-zA-Z_./\-]+/)`", text):
        candidate = m.group(1)
        if "/" in candidate:
            refs.append(candidate)
    return refs
