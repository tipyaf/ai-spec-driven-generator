"""Consistency tests for v5 documentation (Étape 6).

Validates that the documentation references real artefacts on disk:

- Every command cited in README.md has a matching skill folder under `skills/`.
- Every filesystem path mentioned in README.md exists (best-effort).
- The gate IDs listed in README.md match the gate IDs declared in
  `stacks/project-types/*.yaml`.
- The 18 agents listed in README.md exist in `agents/`.
- `PIPELINE.md`, `GUIDE.md`, `CHEATSHEET.md` exist and contain their expected
  top-level sections.

These tests are the machine witness that the docs are not diverging from the
code base. If a test fails, either the doc is lying or the artefact was
renamed/moved.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"
PIPELINE = REPO_ROOT / "_docs" / "PIPELINE.md"
GUIDE = REPO_ROOT / "rules" / "GUIDE.md"
CHEATSHEET = REPO_ROOT / "rules" / "CHEATSHEET.md"
CLAUDE_TEMPLATE = REPO_ROOT / "rules" / "CLAUDE.md.template"

SKILLS_DIR = REPO_ROOT / "skills"
AGENTS_DIR = REPO_ROOT / "agents"
PROJECT_TYPES_DIR = REPO_ROOT / "stacks" / "project-types"

# Commands that exist as skills (excluding /help variants and flags).
EXPECTED_SKILLS = {
    "spec",
    "refine",
    "build",
    "validate",
    "review",
    "ship",
    "ux",
    "scan",
    "next",
    "status",
    "help",
    "resume",
    "migrate",
}

# The 18 agents (v5 consolidation). orchestrator.md is a stub pointing to the
# Python script — it is not counted in the 18.
EXPECTED_AGENTS = {
    "product-owner",
    "ux-ui",
    "architect",
    "refinement",
    "builder-service",
    "builder-frontend",
    "builder-infra",
    "builder-migration",
    "builder-exchange",
    "test-author",
    "code-reviewer",
    "validator",
    "security",
    "devops",
    "observability-engineer",
    "performance-engineer",
    "data-migration-engineer",
    "release-manager",
}
EXPECTED_AGENT_COUNT = 18


# ---------------------------------------------------------------------------
# Existence of the unified docs
# ---------------------------------------------------------------------------


def test_pipeline_md_exists():
    assert PIPELINE.is_file(), "Expected _docs/PIPELINE.md (unified v5 doc)"


def test_guide_md_exists():
    assert GUIDE.is_file(), "Expected rules/GUIDE.md (unified v5 rules)"


def test_cheatsheet_md_exists():
    assert CHEATSHEET.is_file(), "Expected rules/CHEATSHEET.md (1-page TL;DR)"


def test_claude_template_exists():
    assert CLAUDE_TEMPLATE.is_file(), "Expected rules/CLAUDE.md.template"


def test_claude_md_source_removed():
    """The divergent rules/CLAUDE.md source file must be gone in v5 — only
    the .template survives."""
    assert not (REPO_ROOT / "rules" / "CLAUDE.md").exists(), (
        "rules/CLAUDE.md should be removed in v5; only CLAUDE.md.template remains"
    )


def test_v4_docs_removed():
    """The 4 v4 docs have been merged into PIPELINE.md and must be gone."""
    for stale in ("agents.md", "process.md", "workflow.md", "skills.md"):
        assert not (REPO_ROOT / "_docs" / stale).exists(), (
            f"_docs/{stale} should have been merged into _docs/PIPELINE.md"
        )


def test_v4_rules_removed():
    for stale in ("coding-standards.md", "test-quality.md", "agent-conduct.md"):
        assert not (REPO_ROOT / "rules" / stale).exists(), (
            f"rules/{stale} should have been merged into rules/GUIDE.md"
        )


# ---------------------------------------------------------------------------
# Section presence inside the unified docs
# ---------------------------------------------------------------------------


PIPELINE_REQUIRED_SECTIONS = [
    "Overview",
    "Project types",
    "Gates G1–G14",
    "Agents (18)",
    "Enforcement scripts (20)",
    "Stack plugins",
    "Pre-PR assurance chain",
    "anti-regression",
    "Escalation",
    "Feature tracker state machine",
]

GUIDE_REQUIRED_SECTIONS = [
    "Principles",
    "Coding standards",
    "Test quality",
    "Agent conduct",
    "Commits",
    "Git flow",
    "Strict rules",
]

CHEATSHEET_REQUIRED_SECTIONS = [
    "Commands",
    "Top 10 rules",
    "Gates G1",
    "exit codes",
    "Feature tracker states",
]


@pytest.mark.parametrize("needle", PIPELINE_REQUIRED_SECTIONS)
def test_pipeline_has_section(needle):
    content = PIPELINE.read_text(encoding="utf-8").lower()
    assert needle.lower() in content, f"PIPELINE.md missing expected section: {needle!r}"


@pytest.mark.parametrize("needle", GUIDE_REQUIRED_SECTIONS)
def test_guide_has_section(needle):
    content = GUIDE.read_text(encoding="utf-8").lower()
    assert needle.lower() in content, f"GUIDE.md missing expected section: {needle!r}"


@pytest.mark.parametrize("needle", CHEATSHEET_REQUIRED_SECTIONS)
def test_cheatsheet_has_section(needle):
    content = CHEATSHEET.read_text(encoding="utf-8").lower()
    assert needle.lower() in content, f"CHEATSHEET.md missing expected section: {needle!r}"


# ---------------------------------------------------------------------------
# README ↔ skills / agents / gates consistency
# ---------------------------------------------------------------------------


def _commands_in(text: str) -> set[str]:
    """Extract /command tokens from a markdown document.

    Matches tokens at a line start or inside a fenced code block / backtick run
    where the slash is not preceded by a word char or another slash, and NOT
    followed by another `/` (which would indicate a path like `/path/to/x`).
    """
    return set(re.findall(r"(?<![\w/])/([a-z][a-z-]*)\b(?!/)", text))


def test_readme_commands_all_exist_as_skills():
    text = README.read_text(encoding="utf-8")
    cited = _commands_in(text)
    # Exclude /api/... style paths that re-use the leading slash — we filter
    # anything that isn't in our known command vocabulary or on-disk skill set.
    available = {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()}
    unknown = cited - available - {
        # Tokens that aren't commands but share the /name pattern (API paths,
        # code samples, etc.). Whitelist them explicitly.
        "api",
        "health",
        "candidates",
        "ship-service",
    }
    assert not unknown, (
        f"README cites commands that have no matching skill folder: {sorted(unknown)}"
    )


def test_all_expected_skills_exist_on_disk():
    available = {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()}
    missing = EXPECTED_SKILLS - available
    assert not missing, f"Skills missing on disk: {sorted(missing)}"


def test_readme_lists_the_18_agents():
    text = README.read_text(encoding="utf-8")
    missing = [a for a in EXPECTED_AGENTS if a not in text]
    assert not missing, f"README doesn't mention these v5 agents: {missing}"


def test_18_agents_exist_on_disk():
    present = {p.stem for p in AGENTS_DIR.glob("*.md")}
    missing = EXPECTED_AGENTS - present
    assert not missing, f"Agents missing in agents/ dir: {sorted(missing)}"


def test_removed_agents_are_gone():
    """developer, spec-generator, tester, test-engineer, reviewer,
    story-reviewer must not exist anymore (merged or removed)."""
    forbidden = {
        "developer",
        "spec-generator",
        "tester",
        "test-engineer",
        "reviewer",
        "story-reviewer",
    }
    present = {p.stem for p in AGENTS_DIR.glob("*.md")}
    lingering = forbidden & present
    assert not lingering, f"These v4 agents should have been removed: {sorted(lingering)}"


# ---------------------------------------------------------------------------
# Gate numbering in README matches the project-type YAMLs
# ---------------------------------------------------------------------------


def _gate_ids_in(text: str) -> set[str]:
    """Extract gate IDs of the form G1, G2.1, G9.4, G14 from markdown."""
    return set(re.findall(r"\bG(?:\d+(?:\.\d+)?)\b", text))


def _gate_ids_from_project_types() -> set[str]:
    ids: set[str] = set()
    for yaml_path in PROJECT_TYPES_DIR.glob("*.yaml"):
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        for block_name in ("gates", "gates_add"):
            for entry in data.get(block_name, []) or []:
                gate_id = entry.get("id")
                if gate_id:
                    ids.add(str(gate_id).lstrip("G"))
        # gates_override is a dict keyed by gate id
        for gate_id in (data.get("gates_override") or {}).keys():
            ids.add(str(gate_id).lstrip("G"))
    return {f"G{gid}" for gid in ids}


def test_readme_mentions_every_gate_from_project_types():
    declared = _gate_ids_from_project_types()
    text = README.read_text(encoding="utf-8")
    cited = _gate_ids_in(text)
    missing = declared - cited
    assert not missing, (
        f"README is missing gates that exist in stacks/project-types/*.yaml: "
        f"{sorted(missing)}"
    )


def test_pipeline_mentions_every_gate_from_project_types():
    declared = _gate_ids_from_project_types()
    text = PIPELINE.read_text(encoding="utf-8")
    cited = _gate_ids_in(text)
    missing = declared - cited
    assert not missing, (
        f"PIPELINE.md is missing gates declared in stacks/project-types/*.yaml: "
        f"{sorted(missing)}"
    )


# ---------------------------------------------------------------------------
# README file-path references exist
# ---------------------------------------------------------------------------


README_REFERENCED_PATHS = [
    "_docs/PIPELINE.md",
    "rules/GUIDE.md",
    "rules/CHEATSHEET.md",
    "stacks/CUSTOM_STACK_GUIDE.md",
    "_docs/sonarqube.md",
    "_docs/test-methodology.md",
    "_docs/token-costs.md",
    "_docs/INDEX.md",
    "scripts/orchestrator.py",
    "stacks/templates",
]


@pytest.mark.parametrize("path", README_REFERENCED_PATHS)
def test_readme_path_reference_exists(path):
    target = REPO_ROOT / path
    assert target.exists(), f"README references {path!r} but it doesn't exist"


# ---------------------------------------------------------------------------
# CLAUDE.md.template coherence with v5 numbers
# ---------------------------------------------------------------------------


def test_claude_template_references_v5_counts():
    text = CLAUDE_TEMPLATE.read_text(encoding="utf-8")
    assert "18 agents" in text, "CLAUDE.md.template should mention 18 agents"
    assert "20 " in text and "scripts" in text, "CLAUDE.md.template should mention 20 scripts"
    assert "G1" in text and "G14" in text, "CLAUDE.md.template should mention G1–G14"


def test_claude_template_mentions_next_and_ship():
    text = CLAUDE_TEMPLATE.read_text(encoding="utf-8")
    assert "/next" in text, "CLAUDE.md.template should highlight /next as morning command"
    assert "/ship" in text, "CLAUDE.md.template should describe /ship as the single exit"


def test_claude_template_links_to_unified_docs():
    text = CLAUDE_TEMPLATE.read_text(encoding="utf-8")
    assert "PIPELINE.md" in text
    assert "GUIDE.md" in text
    assert "CHEATSHEET.md" in text


def test_readme_highlights_ship_contract():
    text = README.read_text(encoding="utf-8")
    assert "sdd-validated-v5" in text, "README should mention the sdd-validated-v5 PR tag"
    assert "/ship" in text
