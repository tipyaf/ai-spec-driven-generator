"""Integration tests for scripts/next_report.py — the /next skill backend.

Covers the 5 categories produced by /next:
  • BLOCKING (escalated / tampered)
  • IN PROGRESS (building / testing)
  • READY (refined)
  • PENDING SHIP (validated)
  • SUGGESTIONS (LESSONS unread, perf deltas)

Also covers --json output shape and --scope filtering.
"""

from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "next_report.py"
VENV_PYTHON = REPO_ROOT / ".venv-sdd-dev" / "bin" / "python3"


# ---------------------------------------------------------------------------
# Fixture: a minimal project that mixes every story state.
# ---------------------------------------------------------------------------

@pytest.fixture
def mixed_project(tmp_path: Path) -> Path:
    """Build a project fixture with one story per relevant status."""
    (tmp_path / "specs").mkdir()
    (tmp_path / "_work" / "build").mkdir(parents=True)
    (tmp_path / "memory").mkdir()

    (tmp_path / "specs" / "feature-tracker.yaml").write_text(textwrap.dedent("""\
        features:
          - id: sc-0001
            name: escalated story
            status: escalated
          - id: sc-0002
            name: tampered story
            status: tampered
          - id: sc-0003
            name: in-progress story
            status: building
          - id: sc-0004
            name: ready story
            status: refined
          - id: sc-0005
            name: shippable story
            status: validated
    """))
    # LESSONS.md non-empty → triggers a suggestion.
    (tmp_path / "memory" / "LESSONS.md").write_text("# Lessons\n- stub entry\n")
    return tmp_path


# ---------------------------------------------------------------------------
# CLI invocation helpers.
# ---------------------------------------------------------------------------

def _run(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(VENV_PYTHON), str(SCRIPT), *args],
        cwd=project_root,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# JSON mode: structural contract.
# ---------------------------------------------------------------------------

def test_json_output_contains_all_five_sections(mixed_project: Path):
    result = _run(mixed_project, "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    for key in ("blocking", "in_progress", "ready", "pending_ship", "suggestions"):
        assert key in payload, f"missing key {key} in /next --json output"


def test_escalated_story_appears_in_blocking(mixed_project: Path):
    payload = json.loads(_run(mixed_project, "--json").stdout)
    ids = [item["id"] for item in payload["blocking"]]
    assert "sc-0001" in ids
    assert "sc-0002" in ids  # tampered also blocks


def test_blocking_item_suggests_resume_command(mixed_project: Path):
    payload = json.loads(_run(mixed_project, "--json").stdout)
    for item in payload["blocking"]:
        assert item["cmd"].startswith("/resume "), (
            f"blocking item {item} must suggest /resume"
        )


def test_refined_story_is_ready(mixed_project: Path):
    payload = json.loads(_run(mixed_project, "--json").stdout)
    ready_ids = [item["id"] for item in payload["ready"]]
    assert "sc-0004" in ready_ids
    ready_cmd = next(i for i in payload["ready"] if i["id"] == "sc-0004")["cmd"]
    assert ready_cmd == "/build sc-0004"


def test_validated_story_is_pending_ship(mixed_project: Path):
    payload = json.loads(_run(mixed_project, "--json").stdout)
    ship_ids = [item["id"] for item in payload["pending_ship"]]
    assert "sc-0005" in ship_ids
    ship_cmd = next(i for i in payload["pending_ship"] if i["id"] == "sc-0005")["cmd"]
    assert ship_cmd == "/ship sc-0005"


def test_building_story_is_in_progress(mixed_project: Path):
    payload = json.loads(_run(mixed_project, "--json").stdout)
    ip_ids = [item["id"] for item in payload["in_progress"]]
    assert "sc-0003" in ip_ids


def test_lessons_file_triggers_suggestion(mixed_project: Path):
    payload = json.loads(_run(mixed_project, "--json").stdout)
    suggestions_text = " ".join(item.get("text", "") for item in payload["suggestions"])
    assert "LESSONS" in suggestions_text


# ---------------------------------------------------------------------------
# --scope filter.
# ---------------------------------------------------------------------------

def test_scope_blocked_filters_out_other_sections_in_json(mixed_project: Path):
    payload = json.loads(_run(mixed_project, "--json", "--scope", "blocked").stdout)
    # In JSON mode, --scope filters which sections are populated.
    assert payload["blocking"], "blocking must be populated with --scope blocked"
    # Other sections should be empty.
    for key in ("in_progress", "ready", "pending_ship", "suggestions"):
        assert payload[key] == [], (
            f"--scope blocked should empty {key}, got {payload[key]}"
        )


def test_scope_ready_filters_to_only_ready(mixed_project: Path):
    payload = json.loads(_run(mixed_project, "--json", "--scope", "ready").stdout)
    assert payload["ready"], "ready must be populated with --scope ready"
    for key in ("blocking", "in_progress", "pending_ship", "suggestions"):
        assert payload[key] == [], f"--scope ready should empty {key}"


# ---------------------------------------------------------------------------
# --strict exit code.
# ---------------------------------------------------------------------------

def test_strict_exits_non_zero_when_blockers_present(mixed_project: Path):
    result = _run(mixed_project, "--json", "--strict")
    assert result.returncode == 1, (
        "--strict must exit 1 when BLOCKING section is non-empty"
    )


def test_non_strict_exits_zero_even_with_blockers(mixed_project: Path):
    result = _run(mixed_project, "--json")
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# Human mode: smoke test (no crash, sections labelled).
# ---------------------------------------------------------------------------

def test_human_mode_renders_all_section_labels(mixed_project: Path):
    out = _run(mixed_project).stdout
    for label in ("BLOCKING", "IN PROGRESS", "READY", "PENDING SHIP", "SUGGESTIONS"):
        assert label in out, f"human output missing section {label}"


# ---------------------------------------------------------------------------
# Empty-project sanity.
# ---------------------------------------------------------------------------

def test_empty_project_has_no_blockers(tmp_path: Path):
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "feature-tracker.yaml").write_text("features: []\n")
    payload = json.loads(_run(tmp_path, "--json").stdout)
    assert payload["blocking"] == []
    assert payload["in_progress"] == []
    assert payload["ready"] == []
    assert payload["pending_ship"] == []
