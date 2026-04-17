"""Integration tests for v5 skill wrappers.

Verifies that:
  - Every SKILL.md has the mandatory v5 structure (frontmatter + sections).
  - Pipeline skills (/build, /validate, /review, /ship) reference the
    orchestrator with the correct --mode.
  - /help can list every command.
  - /resume refuses without a non-empty reason.
  - /scan absorbs the old /scan-full and /sonar.
  - Obsolete skill directories are gone.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# v5 skills that must exist
EXPECTED_SKILLS = {
    "build",
    "validate",
    "review",
    "ship",
    "refine",
    "spec",
    "ux",
    "scan",
    "next",
    "status",
    "help",
    "resume",
    "migrate",
}

# Obsolete v4 skills that must NOT exist
OBSOLETE_SKILLS = {"scan-full", "sonar"}

# Skills that wrap the orchestrator and their expected --mode
ORCHESTRATOR_MODES = {
    "build": "build",
    "validate": "validate",
    "review": "review",
    "ship": "ship",
}

# Mandatory section headings in SKILL.md body
REQUIRED_SECTIONS = [
    "## Usage",
    "## What it does",
    "## How it works",
]


def _read_skill(name: str) -> str:
    path = SKILLS_DIR / name / "SKILL.md"
    assert path.exists(), f"skills/{name}/SKILL.md is missing"
    return path.read_text(encoding="utf-8")


def _frontmatter(body: str) -> dict[str, str]:
    """Extract the --- YAML frontmatter as a flat string map."""
    m = re.match(r"^---\n(.*?)\n---", body, re.DOTALL)
    assert m, "missing YAML frontmatter"
    result: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            result[k.strip()] = v.strip()
    return result


# --- Structural checks ---------------------------------------------------

@pytest.mark.parametrize("name", sorted(EXPECTED_SKILLS))
def test_skill_exists_with_required_structure(name: str):
    body = _read_skill(name)

    fm = _frontmatter(body)
    assert fm.get("name") == name, f"frontmatter 'name' must equal {name!r}"
    assert fm.get("description"), "frontmatter 'description' must be non-empty"

    for section in REQUIRED_SECTIONS:
        assert section in body, f"missing section {section!r} in skills/{name}/SKILL.md"


@pytest.mark.parametrize("name", sorted(OBSOLETE_SKILLS))
def test_obsolete_skills_removed(name: str):
    path = SKILLS_DIR / name
    assert not path.exists(), f"obsolete skill {name} should be removed (merged into /scan)"


# --- Orchestrator wiring -------------------------------------------------

@pytest.mark.parametrize("name,mode", sorted(ORCHESTRATOR_MODES.items()))
def test_pipeline_skill_references_orchestrator(name: str, mode: str):
    body = _read_skill(name)
    # Must mention scripts/orchestrator.py
    assert "scripts/orchestrator.py" in body, (
        f"skills/{name}/SKILL.md must invoke scripts/orchestrator.py"
    )
    # Must mention the correct --mode <mode>
    pattern = re.compile(rf"--mode\s+{re.escape(mode)}\b")
    assert pattern.search(body), (
        f"skills/{name}/SKILL.md must invoke orchestrator with --mode {mode}"
    )


# --- /help lists every command -------------------------------------------

def test_help_references_all_commands():
    body = _read_skill("help")
    # /help's own doc doesn't need to enumerate every command by hand,
    # but it must describe the discovery mechanism (walk skills/*/SKILL.md)
    # and must handle at least the pipeline + operations + meta categories.
    for hint in ["skills/*/SKILL.md", "description"]:
        assert hint in body, f"/help should mention {hint!r}"

    # Sanity: every expected skill has a description that /help would pick up.
    for name in EXPECTED_SKILLS:
        fm = _frontmatter(_read_skill(name))
        assert fm.get("description"), f"{name} needs a description for /help to list it"


def test_help_mentions_typo_suggestion():
    body = _read_skill("help")
    # The spec requires "did you mean X" on typos.
    assert re.search(r"did you mean", body, re.IGNORECASE), (
        "/help must mention the 'did you mean' typo-suggestion mechanic"
    )


# --- /resume requires a non-empty reason ---------------------------------

def test_resume_requires_reason():
    body = _read_skill("resume")
    # Signature must show reason in quotes
    assert re.search(r"/resume\s+<story-id>\s+\"<reason>\"", body), (
        "/resume usage must show the reason as a quoted mandatory argument"
    )
    # Must describe the refusal path
    assert "requires a reason" in body or "resume requires a reason" in body, (
        "/resume must describe the refusal when reason is missing"
    )
    # Arguments table marks reason as required
    assert re.search(r"\|\s*`?reason`?\s*\|\s*Yes\s*\|", body), (
        "/resume arguments table must mark reason as Required=Yes"
    )


# --- /scan absorbs scan-full and sonar -----------------------------------

def test_scan_documents_merged_flags():
    body = _read_skill("scan")
    assert "--full" in body, "/scan must document --full"
    assert "--report" in body, "/scan must document --report"
    # Migration note present
    assert "/scan-full" in body and "/sonar" in body, (
        "/scan must explain the migration from /scan-full and /sonar"
    )


# --- /ship contract ------------------------------------------------------

def test_ship_contract_and_tag():
    body = _read_skill("ship")
    assert "sdd-validated-v5" in body, (
        "/ship must mention the sdd-validated-v5 tag it applies to PRs"
    )
    assert "PR CREATED" in body, (
        "/ship must describe the 'PR CREATED' success message"
    )
    assert "release-manager" in body, (
        "/ship must dispatch release-manager for the push/PR step"
    )


# --- /next + /status ------------------------------------------------------

def test_next_has_five_sections():
    body = _read_skill("next")
    for section in [
        "BLOCKING",
        "IN PROGRESS",
        "READY",
        "PENDING SHIP",
        "SUGGESTIONS",
    ]:
        assert section in body, f"/next must document the {section!r} section"
    assert "next_report.py" in body, "/next must invoke scripts/next_report.py"


def test_status_embeds_next():
    body = _read_skill("status")
    assert "next_report.py" in body, (
        "/status must embed next_report.py output in Recommended actions"
    )
    assert "--scope" in body, "/status must show how it narrows next_report via --scope"


# --- /refine and /ux contracts ------------------------------------------

def test_refine_uses_new_agents_and_templates():
    body = _read_skill("refine")
    assert "refinement.md" in body, (
        "/refine must load agents/refinement.md (v5 agent)"
    )
    assert "ac-templates.yaml" in body, (
        "/refine must read stack ac-templates.yaml to inject AC-SEC/AC-BP"
    )


def test_ux_requires_four_data_attributes():
    body = _read_skill("ux")
    for attr in ["data-testid", "data-action", "data-state", "data-role"]:
        assert attr in body, f"/ux must require the {attr} attribute on interactive elements"


# --- /spec auto-detection ------------------------------------------------

def test_spec_mentions_autodetection_sources():
    body = _read_skill("spec")
    for f in ["package.json", "pyproject.toml", "Cargo.toml", "go.mod", "Gemfile"]:
        assert f in body, f"/spec must mention {f} as an auto-detection source"
