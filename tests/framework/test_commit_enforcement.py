"""
Commit enforcement tests — validates that the framework enforces atomic commits,
explicit git add, and the check_story_commits.py script.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from conftest import FRAMEWORK_ROOT, read_text


# ══════════════════════════════════════════════════════════════════════════
# agent-conduct.md commit rules
# ══════════════════════════════════════════════════════════════════════════


class TestAgentConductCommitRules:
    """agent-conduct.md must enforce commit rules."""

    @pytest.fixture
    def conduct_content(self) -> str:
        return read_text(FRAMEWORK_ROOT / "rules" / "agent-conduct.md")

    def test_git_add_dot_forbidden(self, conduct_content: str):
        """agent-conduct.md must forbid 'git add .' and 'git add -A'."""
        lower = conduct_content.lower()
        assert "git add ." in lower or "git add -a" in lower, (
            "agent-conduct.md must mention 'git add .' or 'git add -A' as forbidden"
        )

    def test_explicit_file_names_required(self, conduct_content: str):
        """agent-conduct.md must require explicit file names in git add."""
        lower = conduct_content.lower()
        assert "explicit" in lower or "name" in lower, (
            "agent-conduct.md must require explicit file names for git add"
        )

    def test_atomic_commit_after_validation(self, conduct_content: str):
        """agent-conduct.md must enforce atomic commit after build validation."""
        lower = conduct_content.lower()
        assert "atomic" in lower or "single" in lower, (
            "agent-conduct.md must document atomic commit requirement"
        )
        assert "validation" in lower or "all gates pass" in lower, (
            "agent-conduct.md must document that commit happens after validation"
        )

    def test_no_commit_during_build(self, conduct_content: str):
        """agent-conduct.md must state no commits during build phase."""
        lower = conduct_content.lower()
        assert "no commit" in lower or "no commits" in lower, (
            "agent-conduct.md must state no commits during build/refine phases"
        )


# ══════════════════════════════════════════════════════════════════════════
# Build SKILL.md commit section
# ══════════════════════════════════════════════════════════════════════════


class TestBuildSkillCommit:
    """Build SKILL.md must document atomic commit after all gates pass."""

    @pytest.fixture
    def skill_content(self) -> str:
        return read_text(FRAMEWORK_ROOT / "skills" / "build" / "SKILL.md")

    def test_commit_after_all_pass(self, skill_content: str):
        lower = skill_content.lower()
        assert "all gates pass" in lower or "all pass" in lower, (
            "Build SKILL.md must document commit after ALL gates pass"
        )

    def test_git_add_explicit_files(self, skill_content: str):
        """Build SKILL.md must show explicit git add with named files."""
        assert "git add specs/stories/" in skill_content, (
            "Build SKILL.md must show explicit git add for story file"
        )
        assert "git add specs/feature-tracker.yaml" in skill_content, (
            "Build SKILL.md must show explicit git add for feature tracker"
        )

    def test_never_git_add_dot(self, skill_content: str):
        """Build SKILL.md must forbid 'git add .' and 'git add -A'."""
        assert "never" in skill_content.lower() and (
            "git add ." in skill_content or "git add -A" in skill_content
        ), (
            "Build SKILL.md must explicitly forbid 'git add .' and 'git add -A'"
        )

    def test_pr_mr_creation(self, skill_content: str):
        """Build SKILL.md must document PR/MR creation."""
        lower = skill_content.lower()
        assert "pr" in lower or "mr" in lower, (
            "Build SKILL.md must document PR/MR creation after commit"
        )

    def test_pr_tool_detection(self, skill_content: str):
        """Build SKILL.md must document PR tool detection (gh/glab/az)."""
        assert "gh" in skill_content and "glab" in skill_content, (
            "Build SKILL.md must document gh and glab as PR/MR tools"
        )

    def test_pr_tool_memorization(self, skill_content: str):
        """Build SKILL.md must document PR tool memorization."""
        lower = skill_content.lower()
        assert "memorize" in lower or "memory" in lower, (
            "Build SKILL.md must document PR tool memorization"
        )


# ══════════════════════════════════════════════════════════════════════════
# check_story_commits.py script
# ══════════════════════════════════════════════════════════════════════════


class TestCheckStoryCommitsScript:
    """check_story_commits.py must exist and be correctly structured."""

    @pytest.fixture
    def script_content(self) -> str:
        return read_text(FRAMEWORK_ROOT / "scripts" / "check_story_commits.py")

    def test_script_exists(self):
        assert (FRAMEWORK_ROOT / "scripts" / "check_story_commits.py").exists()

    def test_script_parses(self, script_content: str):
        try:
            ast.parse(script_content, filename="check_story_commits.py")
        except SyntaxError as e:
            pytest.fail(f"check_story_commits.py has syntax error: {e}")

    def test_script_has_main(self, script_content: str):
        tree = ast.parse(script_content)
        func_names = [
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        ]
        assert "main" in func_names, "check_story_commits.py must have main()"

    def test_script_has_ifmain(self, script_content: str):
        assert "__name__" in script_content and "__main__" in script_content, (
            "check_story_commits.py must have if __name__ == '__main__' guard"
        )

    def test_script_checks_atomic_commit(self, script_content: str):
        """Script must check that production code + story + tracker are staged together."""
        lower = script_content.lower()
        assert "atomic" in lower or "story" in lower, (
            "check_story_commits.py must check atomic commit requirements"
        )

    def test_script_checks_verify_fields(self, script_content: str):
        """Script must validate that ACs have verify: fields."""
        assert "verify" in script_content.lower(), (
            "check_story_commits.py must validate verify: fields"
        )

    def test_script_checks_yaml_validity(self, script_content: str):
        """Script must validate story file YAML."""
        assert "yaml" in script_content.lower(), (
            "check_story_commits.py must validate YAML structure"
        )


# ══════════════════════════════════════════════════════════════════════════
# setup-hooks.sh includes check_story_commits.py
# ══════════════════════════════════════════════════════════════════════════


class TestSetupHooksIntegration:
    """setup-hooks.sh must include check_story_commits.py in pre-commit."""

    def test_setup_hooks_references_story_commits(self):
        content = read_text(FRAMEWORK_ROOT / "scripts" / "setup-hooks.sh")
        assert "check_story_commits" in content, (
            "setup-hooks.sh must reference check_story_commits.py in pre-commit hook"
        )

    def test_setup_hooks_runs_on_spec_files(self):
        content = read_text(FRAMEWORK_ROOT / "scripts" / "setup-hooks.sh")
        assert "specs/" in content, (
            "setup-hooks.sh must trigger story commit check when specs/ files are staged"
        )
