"""
Model consistency tests — every agent has a model field, CLAUDE.md lists all
agents, and model values are valid.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import FRAMEWORK_ROOT, all_agent_cores, parse_frontmatter, read_text

VALID_MODELS = {"opus", "sonnet"}

# Agents that are expected to have a model: field
# (all core agents should have one)
AGENTS_DIR = FRAMEWORK_ROOT / "agents"


class TestAgentFrontmatter:
    """Every core agent file must have valid YAML frontmatter with model field."""

    @pytest.fixture
    def agent_cores(self) -> list[Path]:
        return all_agent_cores(AGENTS_DIR)

    def test_every_agent_has_frontmatter(self, agent_cores: list[Path]):
        missing: list[str] = []
        for agent in agent_cores:
            content = read_text(agent)
            if not content.startswith("---"):
                missing.append(agent.name)
        assert not missing, f"Agents without frontmatter: {missing}"

    def test_every_agent_has_model_field(self, agent_cores: list[Path]):
        missing: list[str] = []
        for agent in agent_cores:
            fm = parse_frontmatter(read_text(agent))
            if "model" not in fm:
                missing.append(agent.name)
        assert not missing, f"Agents without model: field: {missing}"

    def test_all_model_values_are_valid(self, agent_cores: list[Path]):
        invalid: list[str] = []
        for agent in agent_cores:
            fm = parse_frontmatter(read_text(agent))
            model = fm.get("model", "")
            if model and model not in VALID_MODELS:
                invalid.append(f"{agent.name}: model={model}")
        assert not invalid, f"Invalid model values: {invalid}"

    def test_every_agent_has_name_field(self, agent_cores: list[Path]):
        missing: list[str] = []
        for agent in agent_cores:
            fm = parse_frontmatter(read_text(agent))
            if not fm.get("name"):
                missing.append(agent.name)
        assert not missing, f"Agents without name: field: {missing}"

    def test_every_agent_has_description_field(self, agent_cores: list[Path]):
        missing: list[str] = []
        for agent in agent_cores:
            fm = parse_frontmatter(read_text(agent))
            if not fm.get("description"):
                missing.append(agent.name)
        assert not missing, f"Agents without description: field: {missing}"


class TestClaudeMdModelTable:
    """CLAUDE.md model tier table must list all agents with correct models."""

    @pytest.fixture
    def claude_md(self) -> str:
        return read_text(FRAMEWORK_ROOT / "rules" / "CLAUDE.md")

    @pytest.fixture
    def model_table_section(self, claude_md: str) -> str:
        """Extract the model tier recommendations table."""
        # Find the section between "Model tier recommendations" and the next ##
        m = re.search(
            r"## Model tier recommendations.*?\n(.*?)(?=\n## |\Z)",
            claude_md,
            re.DOTALL,
        )
        assert m, "Model tier recommendations section not found in CLAUDE.md"
        return m.group(1)

    # Map from agent filename stem to expected display name in CLAUDE.md table
    AGENT_DISPLAY_NAMES = {
        "developer": "Developer",
        "tester": "Tester",
        "refinement": "Refinement",
        "reviewer": "Reviewer",
        "validator": "Validator",
        "security": "Security",
        "product-owner": "Product Owner",
        "architect": "Architect",
        "ux-ui": "UX/UI",
        "test-engineer": "Test Engineer",
        "devops": "DevOps",
        "orchestrator": "Orchestrator",
    }

    def test_all_key_agents_in_model_table(self, model_table_section: str):
        """Every key agent should appear in the model recommendations table."""
        missing: list[str] = []
        for stem, display in self.AGENT_DISPLAY_NAMES.items():
            if display not in model_table_section:
                missing.append(f"{stem} (expected: '{display}')")
        assert not missing, f"Agents missing from model table:\n" + "\n".join(missing)

    def test_model_table_matches_frontmatter(self):
        """Model recommendations in CLAUDE.md should match agent frontmatter defaults."""
        claude_md = read_text(FRAMEWORK_ROOT / "rules" / "CLAUDE.md")

        # Extract table rows: | Agent | Model | Rationale |
        rows = re.findall(r"\|\s*(\w[\w/ ]+?)\s*\|\s*(\w+)\s*\|", claude_md)
        table_models: dict[str, str] = {}
        for name, model in rows:
            model_lower = model.lower().strip()
            if model_lower in VALID_MODELS:
                table_models[name.strip()] = model_lower

        # Cross-check with frontmatter for agents we can map
        mismatches: list[str] = []
        for stem, display in self.AGENT_DISPLAY_NAMES.items():
            agent_file = AGENTS_DIR / f"{stem}.md"
            if not agent_file.exists():
                continue
            fm = parse_frontmatter(read_text(agent_file))
            fm_model = fm.get("model", "")
            if not fm_model:
                continue
            # Find the matching table entry
            table_model = table_models.get(display)
            if table_model and table_model != fm_model:
                mismatches.append(
                    f"{stem}: frontmatter={fm_model}, CLAUDE.md table={table_model}"
                )

        assert not mismatches, (
            f"Model mismatches between frontmatter and CLAUDE.md:\n"
            + "\n".join(mismatches)
        )


class TestAgentRefFiles:
    """Every core agent that mentions a .ref.md should have one."""

    def test_ref_files_exist_when_referenced(self):
        missing: list[str] = []
        for agent in all_agent_cores(AGENTS_DIR):
            content = read_text(agent)
            ref_name = agent.stem + ".ref.md"
            if ref_name in content:
                ref_path = AGENTS_DIR / ref_name
                if not ref_path.exists():
                    missing.append(f"{agent.name} references {ref_name} but it doesn't exist")
        assert not missing, "\n".join(missing)
