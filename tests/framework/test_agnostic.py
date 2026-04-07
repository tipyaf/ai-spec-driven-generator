"""
Agnostic compliance tests — framework templates and rules must not hardcode
language-specific tooling outside of clearly marked examples.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import FRAMEWORK_ROOT, read_text

# Language-specific commands/tools that should not appear in agnostic contexts
LANGUAGE_SPECIFIC = [
    # JS/TS
    (r"\bnpm\s+(run|install|test)\b", "npm"),
    (r"\byarn\s+(run|add|test)\b", "yarn"),
    (r"\bpnpm\s+(run|add|test)\b", "pnpm"),
    (r"\bnpx\b", "npx"),
    (r"\btsc\b", "tsc"),
    (r"\bvitest\b", "vitest"),
    (r"\bjest\b", "jest"),
    (r"\bnode\s+ace\b", "node ace"),
    # Python
    (r"\bpip\s+install\b", "pip install"),
    (r"\bpoetry\s+(run|add|install)\b", "poetry"),
    (r"\buvicorn\b", "uvicorn"),
    # Go
    (r"\bgo\s+(test|build|run)\b", "go"),
    # Rust
    (r"\bcargo\s+(test|build|run)\b", "cargo"),
]

# Files that are expected to be agnostic (templates, core rules)
AGNOSTIC_FILES = [
    "specs/templates/story-template.yaml",
    "specs/templates/build-template.yaml",
    "rules/agent-conduct.md",
    # SKILL.md files for core skills
    "skills/build/SKILL.md",
    "skills/refine/SKILL.md",
    "skills/validate/SKILL.md",
    "skills/review/SKILL.md",
]

# Lines containing these markers are allowed to have language-specific content
EXAMPLE_MARKERS = [
    "example",
    "e.g.",
    "eg.",
    "such as",
    "for instance",
    "```",  # code blocks
    "# comment",
    "pytest",  # our own test framework uses pytest
    "coverage",
    "--cov",  # coverage is a generic concept
]


def _is_example_line(line: str) -> bool:
    """Check if a line is part of an example or code block."""
    line_lower = line.lower()
    return any(marker in line_lower for marker in EXAMPLE_MARKERS)


def _in_code_block(lines: list[str], line_idx: int) -> bool:
    """Check if a given line index is inside a markdown code block."""
    fence_count = 0
    for i in range(line_idx):
        if lines[i].strip().startswith("```"):
            fence_count += 1
    return fence_count % 2 == 1


class TestAgnosticTemplates:
    """Framework templates must not contain language-specific commands."""

    def test_story_template_agnostic(self):
        path = FRAMEWORK_ROOT / "specs" / "templates" / "story-template.yaml"
        content = read_text(path)
        violations: list[str] = []
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if _is_example_line(line) or _in_code_block(lines, i - 1):
                continue
            for pattern, name in LANGUAGE_SPECIFIC:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(f"  line {i}: `{name}` — {line.strip()}")
        assert not violations, (
            f"story-template.yaml contains language-specific references:\n"
            + "\n".join(violations)
        )

    def test_build_template_agnostic(self):
        path = FRAMEWORK_ROOT / "specs" / "templates" / "build-template.yaml"
        content = read_text(path)
        violations: list[str] = []
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if _is_example_line(line) or _in_code_block(lines, i - 1):
                continue
            for pattern, name in LANGUAGE_SPECIFIC:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(f"  line {i}: `{name}` — {line.strip()}")
        assert not violations, (
            f"build-template.yaml contains language-specific references:\n"
            + "\n".join(violations)
        )


class TestAgnosticBuildSkill:
    """Build SKILL.md should be agnostic except in clearly marked examples."""

    def test_build_skill_no_hardcoded_language(self):
        path = FRAMEWORK_ROOT / "skills" / "build" / "SKILL.md"
        content = read_text(path)
        violations: list[str] = []
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if _is_example_line(line) or _in_code_block(lines, i - 1):
                continue
            for pattern, name in LANGUAGE_SPECIFIC:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(f"  line {i}: `{name}` — {line.strip()}")
        assert not violations, (
            f"build/SKILL.md contains language-specific references outside examples:\n"
            + "\n".join(violations)
        )


class TestAgnosticStackProfileTemplate:
    """Stack profile template must document the interface, not hardcode tools."""

    def test_stack_template_exists(self):
        template = FRAMEWORK_ROOT / "stacks" / "stack-profile-template.md"
        assert template.exists(), "Missing stacks/stack-profile-template.md"

    def test_stack_template_has_required_sections(self):
        template = FRAMEWORK_ROOT / "stacks" / "stack-profile-template.md"
        content = read_text(template)
        # The template should define the interface stacks must implement
        required_concepts = ["forbidden", "anti-pattern", "test"]
        found = [c for c in required_concepts if c.lower() in content.lower()]
        assert len(found) >= 2, (
            f"Stack template should define forbidden patterns and test conventions. "
            f"Found: {found}"
        )


class TestAgnosticToolOptional:
    """Framework must never require specific external tools."""

    def test_sonarqube_never_required(self):
        """SonarQube must never be REQUIRED in core framework files."""
        agnostic_files = [
            "skills/build/SKILL.md",
            "skills/refine/SKILL.md",
            "rules/agent-conduct.md",
        ]
        for f in agnostic_files:
            content = read_text(FRAMEWORK_ROOT / f).lower()
            # Should not say "must use sonarqube" or "requires sonarqube"
            assert "must use sonarqube" not in content, (
                f"{f} must not require SonarQube"
            )
            assert "requires sonarqube" not in content, (
                f"{f} must not require SonarQube"
            )

    def test_code_quality_gate_has_fallback(self):
        """Gate 3 (Code Quality) must have a fallback when no tool is configured."""
        skill = read_text(FRAMEWORK_ROOT / "skills" / "build" / "SKILL.md")
        # Must mention reviewer as fallback
        assert "reviewer" in skill.lower(), (
            "Code quality gate must have reviewer fallback"
        )
        assert "never skip" in skill.lower() or "never skipped" in skill.lower(), (
            "Code quality gate must be documented as NEVER skipped"
        )

    def test_pm_tool_not_hardcoded(self):
        """PM tool must not be hardcoded to a single provider."""
        skill = read_text(FRAMEWORK_ROOT / "skills" / "refine" / "SKILL.md")
        # Must mention multiple PM tools or say "if configured"
        assert "if configured" in skill.lower() or "if pm tool configured" in skill.lower(), (
            "refine/SKILL.md must treat PM tool as optional"
        )

    def test_wcag_tool_not_hardcoded(self):
        """WCAG audit tool must not be hardcoded."""
        skill = read_text(FRAMEWORK_ROOT / "skills" / "refine" / "SKILL.md")
        # Must say "if configured" or "if tool configured"
        assert "if" in skill.lower() and "configured" in skill.lower(), (
            "WCAG audit tool must be treated as optional in refine/SKILL.md"
        )

    def test_agent_conduct_documents_tool_optionality(self):
        """agent-conduct.md must document that tools are optional."""
        content = read_text(FRAMEWORK_ROOT / "rules" / "agent-conduct.md")
        assert "optional" in content.lower(), (
            "agent-conduct.md must document that tools are optional"
        )
