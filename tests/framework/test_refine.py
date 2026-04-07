"""
Refine tests — validates the /refine pipeline including wireframe gate,
WCAG validation, PM integration, and auto-generated validation ACs.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import FRAMEWORK_ROOT, read_text


@pytest.fixture
def skill_content() -> str:
    return read_text(FRAMEWORK_ROOT / "skills" / "refine" / "SKILL.md")


@pytest.fixture
def refinement_content() -> str:
    return read_text(FRAMEWORK_ROOT / "agents" / "refinement.md")


@pytest.fixture
def ux_ui_content() -> str:
    return read_text(FRAMEWORK_ROOT / "agents" / "ux-ui.md")


# ══════════════════════════════════════════════════════════════════════════
# Wireframe gate
# ══════════════════════════════════════════════════════════════════════════


class TestWireframeGate:
    """Refine SKILL.md must document the wireframe gate for UI projects."""

    def test_wireframe_gate_in_skill(self, skill_content: str):
        assert "wireframe gate" in skill_content.lower(), (
            "refine/SKILL.md must document the wireframe gate"
        )

    def test_wireframe_gate_is_ui_only(self, skill_content: str):
        assert "ui project" in skill_content.lower() or "ui only" in skill_content.lower(), (
            "Wireframe gate must be documented as UI-only"
        )

    def test_wireframe_html_output(self, skill_content: str):
        assert "html" in skill_content.lower(), (
            "Wireframes must be produced as HTML"
        )

    def test_wireframe_self_contained(self, skill_content: str):
        assert "self-contained" in skill_content.lower(), (
            "HTML wireframes must be self-contained"
        )

    def test_wireframe_data_testid(self, skill_content: str):
        assert "data-testid" in skill_content, (
            "Wireframes must include data-testid attributes"
        )

    def test_wireframe_storage_path(self, skill_content: str):
        assert "_work/ux/wireframes/" in skill_content, (
            "Wireframes must be stored in _work/ux/wireframes/"
        )

    def test_wireframe_user_validation(self, skill_content: str):
        """Wireframes must require explicit user validation."""
        assert "wait" in skill_content.lower() and "user" in skill_content.lower(), (
            "Wireframe gate must WAIT for user approval"
        )

    def test_wireframe_triggers(self, skill_content: str):
        """Wireframe gate must list trigger conditions."""
        lower = skill_content.lower()
        assert "new page" in lower or "new screen" in lower, (
            "Wireframe gate must trigger for new pages/screens"
        )

    def test_wireframe_dispatches_ux_agent(self, skill_content: str):
        """Wireframe gate must dispatch UX/UI agent."""
        assert "ux-ui" in skill_content.lower() or "ux/ui" in skill_content.lower(), (
            "Wireframe gate must dispatch UX/UI agent"
        )


# ══════════════════════════════════════════════════════════════════════════
# WCAG validation
# ══════════════════════════════════════════════════════════════════════════


class TestWCAGValidation:
    """WCAG validation must be documented with loop-until-pass."""

    def test_wcag_in_skill(self, skill_content: str):
        assert "wcag" in skill_content.lower(), (
            "refine/SKILL.md must document WCAG validation"
        )

    def test_wcag_loop_until_pass(self, skill_content: str):
        lower = skill_content.lower()
        assert "loop" in lower and "pass" in lower, (
            "WCAG validation must loop until PASS"
        )

    def test_wcag_tool_optional(self, skill_content: str):
        """WCAG tool must be optional (if configured)."""
        lower = skill_content.lower()
        assert "if" in lower and "configured" in lower, (
            "WCAG audit tool must be treated as optional"
        )

    def test_wcag_manual_fallback(self, skill_content: str):
        """Must have manual checklist fallback when no tool configured."""
        lower = skill_content.lower()
        assert "checklist" in lower or "manual" in lower, (
            "WCAG validation must have manual checklist fallback"
        )


# ══════════════════════════════════════════════════════════════════════════
# PM integration
# ══════════════════════════════════════════════════════════════════════════


class TestPMIntegration:
    """PM integration must be generic (not hardcoded to Shortcut)."""

    def test_pm_integration_in_skill(self, skill_content: str):
        lower = skill_content.lower()
        assert "pm" in lower or "project management" in lower, (
            "refine/SKILL.md must document PM integration"
        )

    def test_multiple_pm_tools_supported(self, skill_content: str):
        """Must support at least Shortcut, Jira, GitLab."""
        lower = skill_content.lower()
        assert "shortcut" in lower, "Must mention Shortcut"
        assert "jira" in lower, "Must mention Jira"
        assert "gitlab" in lower, "Must mention GitLab"

    def test_pm_tool_optional(self, skill_content: str):
        """PM tool must be optional."""
        lower = skill_content.lower()
        assert "if configured" in lower or "if pm tool configured" in lower, (
            "PM tool must be optional"
        )

    def test_specs_source_of_truth(self, skill_content: str):
        """Specs must be the source of truth, not the PM tool."""
        lower = skill_content.lower()
        assert "source of truth" in lower, (
            "refine/SKILL.md must state specs are the source of truth"
        )

    def test_refinement_agent_pm_integration(self, refinement_content: str):
        """Refinement agent must have PM integration section."""
        lower = refinement_content.lower()
        assert "project management" in lower or "pm tool" in lower, (
            "refinement.md must document PM integration"
        )


# ══════════════════════════════════════════════════════════════════════════
# Validation ACs (auto-generated)
# ══════════════════════════════════════════════════════════════════════════


class TestValidationACs:
    """Auto-generated validation ACs must be documented."""

    def test_validation_acs_in_skill(self, skill_content: str):
        assert "validation ac" in skill_content.lower() or "validation_acs" in skill_content.lower(), (
            "refine/SKILL.md must document auto-generated validation ACs"
        )

    def test_compile_ac_documented(self, skill_content: str):
        assert "COMPILE" in skill_content, (
            "refine/SKILL.md must document AC-BP-[FEATURE]-COMPILE"
        )

    def test_tu_ac_documented(self, skill_content: str):
        assert "-TU" in skill_content, (
            "refine/SKILL.md must document AC-BP-[FEATURE]-TU"
        )

    def test_console_ac_documented(self, skill_content: str):
        assert "CONSOLE" in skill_content, (
            "refine/SKILL.md must document AC-BP-[FEATURE]-CONSOLE"
        )

    def test_wcag_ac_for_ui_projects(self, skill_content: str):
        assert "WCAG" in skill_content, (
            "refine/SKILL.md must document AC-BP-[FEATURE]-WCAG for UI projects"
        )

    def test_wireframe_ac_for_ui_projects(self, skill_content: str):
        assert "WIREFRAME" in skill_content, (
            "refine/SKILL.md must document AC-BP-[FEATURE]-WIREFRAME for UI projects"
        )


# ══════════════════════════════════════════════════════════════════════════
# UX/UI agent triggered from /refine
# ══════════════════════════════════════════════════════════════════════════


class TestUXAgentFromRefine:
    """UX/UI agent must be triggerable from /refine."""

    def test_ux_agent_has_refine_trigger(self, ux_ui_content: str):
        assert "/refine" in ux_ui_content, (
            "ux-ui.md must list /refine as a trigger"
        )

    def test_ux_agent_produces_html(self, ux_ui_content: str):
        assert "html" in ux_ui_content.lower(), (
            "ux-ui.md must document HTML wireframe output"
        )

    def test_ux_agent_has_data_testid(self, ux_ui_content: str):
        assert "data-testid" in ux_ui_content, (
            "ux-ui.md must document data-testid requirement"
        )

    def test_ux_agent_outputs_to_work(self, ux_ui_content: str):
        assert "_work/ux/wireframes/" in ux_ui_content, (
            "ux-ui.md must output wireframes to _work/ux/wireframes/"
        )


# ══════════════════════════════════════════════════════════════════════════
# No commit during refine
# ══════════════════════════════════════════════════════════════════════════


class TestNoCommitDuringRefine:
    """Refine phase must NOT commit files."""

    def test_no_commit_in_skill(self, skill_content: str):
        lower = skill_content.lower()
        assert "no commit" in lower or "not commit" in lower or "commit happens after" in lower, (
            "refine/SKILL.md must state that no commit happens during refine"
        )
