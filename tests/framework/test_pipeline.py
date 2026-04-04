"""
Pipeline tests — validates the COMPLETE /build pipeline from prerequisites
through RED phase, GREEN phase, 7 quality gates, and verdict logic.

This is the most critical test file: it ensures the build orchestration
described in skills/build/SKILL.md is internally consistent and that all
handoffs between agents and scripts are correctly wired.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import FRAMEWORK_ROOT, parse_frontmatter, read_text


@pytest.fixture
def skill_content() -> str:
    return read_text(FRAMEWORK_ROOT / "skills" / "build" / "SKILL.md")


# ══════════════════════════════════════════════════════════════════════════
# Phase guard — prerequisites
# ══════════════════════════════════════════════════════════════════════════


class TestPrerequisites:
    """Build SKILL.md must enforce prerequisites before building."""

    def test_requires_feature_tracker(self, skill_content: str):
        assert "feature-tracker.yaml" in skill_content

    def test_requires_status_refined(self, skill_content: str):
        assert "refined" in skill_content

    def test_requires_story_file(self, skill_content: str):
        assert "specs/stories/" in skill_content

    def test_requires_verify_fields(self, skill_content: str):
        assert "verify:" in skill_content

    def test_suggests_refine_when_missing(self, skill_content: str):
        assert "/refine" in skill_content


# ══════════════════════════════════════════════════════════════════════════
# Setup — files to read before building
# ══════════════════════════════════════════════════════════════════════════


class TestSetupPhase:
    """Build SKILL.md setup must list all required reads."""

    REQUIRED_READS = [
        "agents/developer.md",
        "agents/validator.md",
        "LESSONS.md",
    ]

    def test_setup_lists_required_reads(self, skill_content: str):
        for read_file in self.REQUIRED_READS:
            assert read_file in skill_content, (
                f"Build SKILL.md setup must read {read_file}"
            )

    def test_setup_reads_story_file(self, skill_content: str):
        """Must read the story file as the build contract."""
        # Should mention reading the story file and it being the build contract
        assert "build contract" in skill_content.lower()

    def test_setup_reads_stack_profiles(self, skill_content: str):
        assert "stacks/" in skill_content


# ══════════════════════════════════════════════════════════════════════════
# Build file creation
# ══════════════════════════════════════════════════════════════════════════


class TestBuildFileCreation:
    """Build file must be created before implementation starts."""

    def test_skill_documents_build_file_creation(self, skill_content: str):
        assert "build-template.yaml" in skill_content

    def test_skill_specifies_build_file_location(self, skill_content: str):
        assert "_work/build/" in skill_content

    def test_build_template_exists(self):
        path = FRAMEWORK_ROOT / "specs" / "templates" / "build-template.yaml"
        assert path.exists()

    def test_build_template_has_required_top_level_fields(self):
        template = read_text(FRAMEWORK_ROOT / "specs" / "templates" / "build-template.yaml")
        required = ["story:", "cycle:", "agent:", "files:", "gates:", "dependency_map:"]
        for field in required:
            assert field in template, f"build-template.yaml missing: {field}"

    def test_build_template_has_agent_dispatchers(self):
        """Template must list valid agent values."""
        template = read_text(FRAMEWORK_ROOT / "specs" / "templates" / "build-template.yaml")
        expected_agents = [
            "developer",
            "builder-service",
            "builder-frontend",
            "builder-infra",
            "builder-migration",
        ]
        for agent in expected_agents:
            assert agent in template, (
                f"build-template.yaml should reference agent: {agent}"
            )


# ══════════════════════════════════════════════════════════════════════════
# Dependency map generation
# ══════════════════════════════════════════════════════════════════════════


class TestDependencyMapGeneration:
    """Dependency map generation procedure in SKILL.md."""

    def test_skill_documents_dependency_map_section(self, skill_content: str):
        assert "dependency map" in skill_content.lower()

    def test_skill_lists_dep_map_fields(self, skill_content: str):
        for field in ["touched_functions", "existing_tests", "connected_components"]:
            assert field in skill_content, (
                f"SKILL.md dependency map section must mention {field}"
            )

    def test_skill_specifies_grep_based_analysis(self, skill_content: str):
        assert "grep" in skill_content.lower(), (
            "Dependency map generation should be grep-based (lightweight)"
        )

    def test_skill_runs_before_test_engineer(self, skill_content: str):
        """Dependency map must be generated BEFORE dispatching test-engineer."""
        dep_map_pos = skill_content.lower().find("dependency map generation")
        red_phase_pos = skill_content.lower().find("red phase")
        if dep_map_pos >= 0 and red_phase_pos >= 0:
            assert dep_map_pos < red_phase_pos, (
                "Dependency map generation must come BEFORE RED phase in SKILL.md"
            )


# ══════════════════════════════════════════════════════════════════════════
# Specialized builder dispatch
# ══════════════════════════════════════════════════════════════════════════


class TestBuilderDispatch:
    """Builder dispatch table must be complete and match existing agents."""

    DISPATCH_TABLE = {
        "builder-service": ["Backend", "API", "service"],
        "builder-frontend": ["Frontend", "UI"],
        "builder-infra": ["Infrastructure", "DevOps"],
        "builder-migration": ["Database", "migration"],
        "builder-exchange": ["External", "exchange", "integration"],
        "developer": ["General", "unknown", "default"],
    }

    def test_dispatch_table_exists(self, skill_content: str):
        # Should have a markdown table with builder agents
        assert "builder-service" in skill_content
        assert "builder-frontend" in skill_content

    def test_all_dispatched_agents_exist(self):
        for agent_stem in self.DISPATCH_TABLE:
            path = FRAMEWORK_ROOT / "agents" / f"{agent_stem}.md"
            assert path.exists(), f"Dispatched agent missing: agents/{agent_stem}.md"

    def test_dispatched_agents_have_model_field(self):
        for agent_stem in self.DISPATCH_TABLE:
            path = FRAMEWORK_ROOT / "agents" / f"{agent_stem}.md"
            fm = parse_frontmatter(read_text(path))
            assert "model" in fm, f"{agent_stem}.md missing model: field in frontmatter"

    def test_skill_reads_story_type_for_dispatch(self, skill_content: str):
        """Must read the story's epic or type to determine which builder."""
        assert "epic" in skill_content.lower() or "type" in skill_content.lower()


# ══════════════════════════════════════════════════════════════════════════
# TDD RED phase (4 steps)
# ══════════════════════════════════════════════════════════════════════════


class TestRedPhase:
    """RED phase must dispatch test-engineer and run 3 enforcement scripts."""

    def test_red_phase_dispatches_test_engineer(self, skill_content: str):
        assert "test-engineer" in skill_content

    def test_test_engineer_exists(self):
        assert (FRAMEWORK_ROOT / "agents" / "test-engineer.md").exists()

    def test_test_engineer_is_opus(self):
        fm = parse_frontmatter(
            read_text(FRAMEWORK_ROOT / "agents" / "test-engineer.md")
        )
        assert fm.get("model") == "opus", (
            "test-engineer.md must default to Opus (deep reasoning required)"
        )

    RED_PHASE_SCRIPTS = [
        "check_red_phase.py",
        "check_test_intentions.py",
        "check_msw_contracts.py",
    ]

    def test_red_phase_runs_enforcement_scripts(self, skill_content: str):
        for script in self.RED_PHASE_SCRIPTS:
            assert script in skill_content, (
                f"RED phase must run {script}"
            )

    def test_red_phase_scripts_exist(self):
        for script in self.RED_PHASE_SCRIPTS:
            assert (FRAMEWORK_ROOT / "scripts" / script).exists(), (
                f"RED phase script missing: scripts/{script}"
            )

    def test_check_red_phase_runs_first(self, skill_content: str):
        """check_red_phase.py must run before check_test_intentions.py."""
        red_pos = skill_content.find("check_red_phase.py")
        intentions_pos = skill_content.find("check_test_intentions.py")
        assert red_pos < intentions_pos, (
            "check_red_phase.py must precede check_test_intentions.py in RED phase"
        )

    def test_check_test_intentions_documents_flags(self, skill_content: str):
        """SKILL.md must document --spec-path and --require-ui-intentions flags."""
        assert "--spec-path" in skill_content or "spec-path" in skill_content
        assert "--require-ui-intentions" in skill_content or "require-ui-intentions" in skill_content


# ══════════════════════════════════════════════════════════════════════════
# TDD GREEN phase (3 steps)
# ══════════════════════════════════════════════════════════════════════════


class TestGreenPhase:
    """GREEN phase must dispatch builder and run 2 enforcement scripts."""

    GREEN_PHASE_SCRIPTS = [
        "check_tdd_order.py",
        "check_test_tampering.py",
    ]

    def test_green_phase_dispatches_builder(self, skill_content: str):
        """GREEN phase must dispatch the appropriate builder agent."""
        assert "builder" in skill_content.lower()

    def test_green_phase_runs_enforcement_scripts(self, skill_content: str):
        for script in self.GREEN_PHASE_SCRIPTS:
            assert script in skill_content, f"GREEN phase must run {script}"

    def test_green_phase_scripts_exist(self):
        for script in self.GREEN_PHASE_SCRIPTS:
            assert (FRAMEWORK_ROOT / "scripts" / script).exists()

    def test_tdd_order_before_tampering(self, skill_content: str):
        """check_tdd_order.py must run before check_test_tampering.py."""
        order_pos = skill_content.find("check_tdd_order.py")
        tamper_pos = skill_content.find("check_test_tampering.py")
        assert order_pos < tamper_pos, (
            "check_tdd_order.py must precede check_test_tampering.py in GREEN phase"
        )

    def test_red_phase_before_green_phase(self, skill_content: str):
        """RED phase must come before GREEN phase."""
        red_pos = skill_content.lower().find("red phase")
        green_pos = skill_content.lower().find("green phase")
        assert red_pos < green_pos, "RED phase must precede GREEN phase"


# ══════════════════════════════════════════════════════════════════════════
# Post-build
# ══════════════════════════════════════════════════════════════════════════


class TestPostBuild:
    """Post-build must run coverage audit."""

    def test_post_build_runs_coverage_audit(self, skill_content: str):
        assert "check_coverage_audit.py" in skill_content

    def test_coverage_audit_script_exists(self):
        assert (FRAMEWORK_ROOT / "scripts" / "check_coverage_audit.py").exists()


# ══════════════════════════════════════════════════════════════════════════
# 7 Quality Gates (Phase 3.5: Validate)
# ══════════════════════════════════════════════════════════════════════════


class TestQualityGates:
    """SKILL.md must document 7 sequential validation gates correctly."""

    GATE_DESCRIPTIONS = {
        1: "Security",
        2: "Tests",
        3: "UI",
        4: "AC Validation",
        5: "Review",
        6: "SonarQube",
        7: "Story Review",
    }

    def test_seven_gates_documented(self, skill_content: str):
        for gate_num, gate_name in self.GATE_DESCRIPTIONS.items():
            pattern = rf"\*\*Gate\s+{gate_num}\b"
            assert re.search(pattern, skill_content), (
                f"SKILL.md must document Gate {gate_num} — {gate_name}"
            )

    def test_gate_1_is_security(self, skill_content: str):
        m = re.search(r"\*\*Gate 1\b.*", skill_content)
        assert m and "security" in m.group(0).lower()

    def test_gate_2_is_tests(self, skill_content: str):
        m = re.search(r"\*\*Gate 2\b.*", skill_content)
        assert m and "test" in m.group(0).lower()

    def test_gate_4_is_ac_validation(self, skill_content: str):
        m = re.search(r"\*\*Gate 4\b.*", skill_content)
        assert m and ("ac" in m.group(0).lower() or "validation" in m.group(0).lower())

    def test_gate_6_is_sonarqube_optional(self, skill_content: str):
        m = re.search(r"\*\*Gate 6\b.*", skill_content)
        assert m and "sonar" in m.group(0).lower()

    def test_gate_7_is_story_review_mandatory(self, skill_content: str):
        m = re.search(r"\*\*Gate 7\b.*", skill_content)
        assert m and "story" in m.group(0).lower()

    def test_gate_7_references_story_reviewer(self, skill_content: str):
        assert "story-reviewer" in skill_content

    def test_story_reviewer_agent_exists(self):
        assert (FRAMEWORK_ROOT / "agents" / "story-reviewer.md").exists()

    def test_gates_are_sequential(self, skill_content: str):
        """Gates must appear in order 1-7 in SKILL.md."""
        positions = []
        for i in range(1, 8):
            m = re.search(rf"\*\*Gate\s+{i}\b", skill_content)
            assert m, f"Gate {i} not found"
            positions.append(m.start())
        assert positions == sorted(positions), "Gates must appear in sequential order 1-7"


# ══════════════════════════════════════════════════════════════════════════
# Verdict logic
# ══════════════════════════════════════════════════════════════════════════


class TestVerdictLogic:
    """Verdict section must handle pass, fail, and escalation."""

    def test_verdict_section_exists(self, skill_content: str):
        assert "verdict" in skill_content.lower()

    def test_all_pass_sets_validated(self, skill_content: str):
        assert "validated" in skill_content

    def test_fail_increments_cycles(self, skill_content: str):
        assert "cycles" in skill_content.lower()

    def test_escalation_at_three_cycles(self, skill_content: str):
        assert "3" in skill_content and "escalat" in skill_content.lower()

    def test_no_fourth_cycle(self, skill_content: str):
        """Must explicitly say NOT to attempt a 4th cycle."""
        assert "4th" in skill_content.lower() or "do not" in skill_content.lower()


# ══════════════════════════════════════════════════════════════════════════
# Artefact checklist
# ══════════════════════════════════════════════════════════════════════════


class TestArtefactChecklist:
    """Build SKILL.md must list all expected artefacts."""

    EXPECTED_ARTEFACTS = [
        "implementation code",
        "tests",
        "_work/build/",
        "feature-tracker.yaml",
    ]

    def test_artefact_section_exists(self, skill_content: str):
        assert "artefact" in skill_content.lower() or "artifact" in skill_content.lower()

    def test_artefacts_listed(self, skill_content: str):
        content_lower = skill_content.lower()
        for artefact in self.EXPECTED_ARTEFACTS:
            assert artefact.lower() in content_lower, (
                f"Artefact checklist must mention: {artefact}"
            )


# ══════════════════════════════════════════════════════════════════════════
# Stale story detection
# ══════════════════════════════════════════════════════════════════════════


class TestStaleStoryDetection:
    """Build SKILL.md must document stale story detection."""

    def test_stale_detection_documented(self, skill_content: str):
        assert "stale" in skill_content.lower()

    def test_stale_mentions_48_hours(self, skill_content: str):
        assert "48" in skill_content


# ══════════════════════════════════════════════════════════════════════════
# Pipeline ordering (end-to-end)
# ══════════════════════════════════════════════════════════════════════════


class TestPipelineOrdering:
    """The overall pipeline phases must appear in the correct order in SKILL.md."""

    def test_main_phase_order(self, skill_content: str):
        """Core workflow phases must appear in order: Prerequisites → Setup → Implement → Validate → Verdict"""
        markers = [
            ("prerequisites", skill_content.lower().find("prerequisit")),
            ("setup", skill_content.lower().find("setup")),
            ("implement", skill_content.lower().find("phase 3: implement")),
            ("validate", skill_content.lower().find("phase 3.5: validate")),
            ("verdict", skill_content.lower().find("verdict")),
        ]
        found = [(name, pos) for name, pos in markers if pos >= 0]
        positions = [pos for _, pos in found]
        assert positions == sorted(positions), (
            f"Pipeline phases out of order. Found: {[n for n, _ in found]}"
        )

    def test_red_before_green_in_tdd_section(self, skill_content: str):
        """In the TDD pipeline section, RED must come before GREEN."""
        tdd_section = ""
        in_tdd = False
        for line in skill_content.splitlines():
            if "tdd pipeline" in line.lower():
                in_tdd = True
            if in_tdd:
                tdd_section += line + "\n"
            if in_tdd and line.startswith("## ") and "tdd" not in line.lower():
                break

        red_pos = tdd_section.lower().find("red phase")
        green_pos = tdd_section.lower().find("green phase")
        assert red_pos >= 0 and green_pos >= 0, "TDD section must have RED and GREEN phases"
        assert red_pos < green_pos, "RED phase must come before GREEN phase in TDD section"


# ══════════════════════════════════════════════════════════════════════════
# CLAUDE.md ↔ SKILL.md consistency
# ══════════════════════════════════════════════════════════════════════════


class TestClaudeMdSkillMdConsistency:
    """CLAUDE.md and build/SKILL.md must agree on key pipeline aspects."""

    @pytest.fixture
    def claude_md(self) -> str:
        return read_text(FRAMEWORK_ROOT / "rules" / "CLAUDE.md")

    def test_both_mention_seven_gates(self, skill_content: str, claude_md: str):
        skill_gates = len(re.findall(r"\*\*Gate\s+\d+", skill_content))
        claude_gates = claude_md.lower().count("gate")
        assert skill_gates >= 7, f"SKILL.md should have 7+ gate references, found {skill_gates}"
        assert claude_gates >= 7, f"CLAUDE.md should mention gates multiple times"

    def test_both_mention_escalation(self, skill_content: str, claude_md: str):
        assert "escalat" in skill_content.lower()
        assert "escalat" in claude_md.lower()

    def test_both_mention_tdd(self, skill_content: str, claude_md: str):
        assert "tdd" in skill_content.lower()

    def test_both_mention_story_reviewer(self, skill_content: str, claude_md: str):
        assert "story-reviewer" in skill_content or "story reviewer" in skill_content.lower()
        assert "story review" in claude_md.lower()

    def test_build_skill_listed_in_claudemd(self, claude_md: str):
        """CLAUDE.md skills table must list /build."""
        assert "/build" in claude_md
