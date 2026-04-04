"""
Cross-reference tests — every file path mentioned in agents, skills, and rules
must resolve to an actual file or directory in the framework.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import FRAMEWORK_ROOT, all_agent_cores, extract_file_refs, read_text

# ── Patterns to skip (placeholders, not real paths) ─────────────────────

SKIP_PATTERNS = {
    "[feature-id]",
    "[feature]",
    "[project-name]",
    "[project]",
    "[name]",
    "sc-[ID]",
    "[ID]",
    "[PR_NUMBER]",
    "sc-0000",
    "localhost",
    "http",
    "test@test.com",
    "path/to/",
    "{story_id}",
    "{feature",
}

# Files/dirs that are created per-project, not in the framework
PROJECT_ONLY = {
    "memory/LESSONS.md",
    "memory/",
    "specs/feature-tracker.yaml",
    "specs/constitution.md",
    "specs/stories/",
    "_work/",
    "test_enforcement.json",
    "stacks/hooks/code_review.py",
    "stacks/hooks/",
    "CLAUDE.md",  # project-level CLAUDE.md (rules/CLAUDE.md exists)
    ".env",
    "conftest.py",
    ".worktrees/",
    ".claude/",
    ".claude/skills/",
    "prompts/phases/",
}

# Paths used as examples in .ref.md files or documentation (not real framework files)
EXAMPLE_PATHS = {
    "src/components/ui/",
    "stacks/python-fastapi.md",
    "stacks/typescript-react.md",
    "framework/",
    "framework/specs/templates/story-template.yaml",
    "ai-framework/scripts/",
    "_docs/spec/",
    "_docs/spec/backend.md",
}

# Bare filenames (without directory) that appear in tables/prose, not as real paths
BARE_FILENAMES = {
    "code_review.py",
    "initial.yaml",
}


def _should_skip(ref: str) -> bool:
    """Check if a reference should be skipped (placeholder, project-only, example, or bare name)."""
    # Template placeholders
    for skip in SKIP_PATTERNS:
        if skip in ref:
            return True
    if re.search(r"\[.*\]", ref):
        return True
    # Project-only paths
    for proj in PROJECT_ONLY:
        if ref == proj or ref.startswith(proj):
            return True
    # Example paths from .ref.md or documentation
    if ref in EXAMPLE_PATHS:
        return True
    # Bare filenames without directory prefix (appear in tables)
    if ref in BARE_FILENAMES:
        return True
    # .ref.md suffix alone (generic reference to "read .ref.md files")
    if ref == ".ref.md":
        return True
    return False


def _resolve_ref(ref: str, root: Path) -> bool:
    """Check if a file reference resolves to an actual path."""
    # Direct path
    if (root / ref).exists():
        return True
    # Some refs use patterns like agents/*.md
    if "*" in ref:
        return bool(list(root.glob(ref)))
    return False


# ── Tests ────────────────────────────────────────────────────────────────


class TestAgentFileRefs:
    """Every file path in agent .md files must resolve."""

    @pytest.fixture
    def agent_files(self) -> list[Path]:
        agents = FRAMEWORK_ROOT / "agents"
        return sorted(agents.glob("*.md"))

    def test_agents_directory_not_empty(self, agent_files: list[Path]):
        assert len(agent_files) > 0, "No agent files found"

    def test_agent_refs_resolve(self, agent_files: list[Path]):
        broken: list[str] = []
        for agent_file in agent_files:
            content = read_text(agent_file)
            refs = extract_file_refs(content)
            for ref in refs:
                if _should_skip(ref):
                    continue
                if not _resolve_ref(ref, FRAMEWORK_ROOT):
                    broken.append(f"{agent_file.name}: `{ref}`")
        assert not broken, f"Broken file references:\n" + "\n".join(broken)


class TestSkillFileRefs:
    """Every file path in SKILL.md files must resolve."""

    @pytest.fixture
    def skill_files(self) -> list[Path]:
        skills = FRAMEWORK_ROOT / "skills"
        return sorted(skills.glob("*/SKILL.md"))

    def test_skills_directory_not_empty(self, skill_files: list[Path]):
        assert len(skill_files) > 0, "No skill files found"

    def test_skill_refs_resolve(self, skill_files: list[Path]):
        broken: list[str] = []
        for skill_file in skill_files:
            content = read_text(skill_file)
            refs = extract_file_refs(content)
            for ref in refs:
                if _should_skip(ref):
                    continue
                if not _resolve_ref(ref, FRAMEWORK_ROOT):
                    broken.append(f"{skill_file.parent.name}/SKILL.md: `{ref}`")
        assert not broken, f"Broken file references:\n" + "\n".join(broken)


class TestRulesFileRefs:
    """Every file path in rules/*.md must resolve."""

    @pytest.fixture
    def rule_files(self) -> list[Path]:
        rules = FRAMEWORK_ROOT / "rules"
        return sorted(rules.glob("*.md"))

    def test_rules_refs_resolve(self, rule_files: list[Path]):
        broken: list[str] = []
        for rule_file in rule_files:
            content = read_text(rule_file)
            refs = extract_file_refs(content)
            for ref in refs:
                if _should_skip(ref):
                    continue
                if not _resolve_ref(ref, FRAMEWORK_ROOT):
                    broken.append(f"{rule_file.name}: `{ref}`")
        assert not broken, f"Broken file references:\n" + "\n".join(broken)


class TestBuildSkillAgentRefs:
    """Build SKILL.md references agents that exist."""

    EXPECTED_BUILDER_AGENTS = [
        "agents/builder-service.md",
        "agents/builder-frontend.md",
        "agents/builder-infra.md",
        "agents/builder-migration.md",
        "agents/builder-exchange.md",
        "agents/developer.md",
    ]

    EXPECTED_PIPELINE_AGENTS = [
        "agents/test-engineer.md",
        "agents/story-reviewer.md",
        "agents/developer.md",
        "agents/validator.md",
    ]

    def test_all_builder_agents_exist(self):
        for agent_path in self.EXPECTED_BUILDER_AGENTS:
            assert (FRAMEWORK_ROOT / agent_path).exists(), f"Missing builder agent: {agent_path}"

    def test_all_pipeline_agents_exist(self):
        for agent_path in self.EXPECTED_PIPELINE_AGENTS:
            assert (FRAMEWORK_ROOT / agent_path).exists(), f"Missing pipeline agent: {agent_path}"

    def test_builder_dispatch_table_matches_agents(self):
        """The dispatch table in SKILL.md must reference agents that exist."""
        skill = read_text(FRAMEWORK_ROOT / "skills" / "build" / "SKILL.md")
        for agent_path in self.EXPECTED_BUILDER_AGENTS:
            agent_name = agent_path.replace("agents/", "").replace(".md", "")
            assert agent_name in skill, (
                f"Builder agent `{agent_name}` not referenced in build SKILL.md dispatch table"
            )


class TestEnforcementScriptRefs:
    """All enforcement scripts referenced in CLAUDE.md and SKILL.md exist."""

    EXPECTED_SCRIPTS = [
        "scripts/check_red_phase.py",
        "scripts/check_test_intentions.py",
        "scripts/check_coverage_audit.py",
        "scripts/check_msw_contracts.py",
        "scripts/check_test_tampering.py",
        "scripts/check_tdd_order.py",
        "scripts/check_test_quality.py",
        "scripts/check_write_coverage.py",
        "scripts/check_oracle_assertions.py",
    ]

    def test_all_enforcement_scripts_exist(self):
        for script_path in self.EXPECTED_SCRIPTS:
            assert (FRAMEWORK_ROOT / script_path).exists(), f"Missing script: {script_path}"

    def test_claudemd_lists_all_orchestrator_scripts(self):
        """CLAUDE.md enforcement table must list all orchestrator-gate scripts."""
        claude_md = read_text(FRAMEWORK_ROOT / "rules" / "CLAUDE.md")
        orchestrator_scripts = [
            "check_red_phase.py",
            "check_test_intentions.py",
            "check_coverage_audit.py",
            "check_msw_contracts.py",
            "check_test_tampering.py",
            "check_tdd_order.py",
        ]
        for script in orchestrator_scripts:
            assert script in claude_md, (
                f"Orchestrator script `{script}` missing from rules/CLAUDE.md enforcement table"
            )

    def test_claudemd_lists_all_precommit_scripts(self):
        """CLAUDE.md enforcement table must list all pre-commit scripts."""
        claude_md = read_text(FRAMEWORK_ROOT / "rules" / "CLAUDE.md")
        precommit_scripts = [
            "check_test_quality.py",
            "check_write_coverage.py",
            "check_oracle_assertions.py",
        ]
        for script in precommit_scripts:
            assert script in claude_md, (
                f"Pre-commit script `{script}` missing from rules/CLAUDE.md enforcement table"
            )
