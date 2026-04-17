"""Smoke test for the v5 orchestrator scaffold (Étape 1).

Covers:
  - ui_messages helpers produce output in both human and JSON modes.
  - Project-type YAMLs load and expose the expected gates.
  - The inheritance chain (web-ui extends web-api) merges gates correctly
    via the orchestrator's internal merger.

These tests do NOT spin up a real project — they exercise the scaffold
in isolation so that Étape 3 (real gate runners) can plug in safely.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
PROJECT_TYPES_DIR = REPO_ROOT / "stacks" / "project-types"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {name} from {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def ui_messages():
    return _load_module("ui_messages", SCRIPTS_DIR / "ui_messages.py")


@pytest.fixture(scope="module")
def orchestrator():
    return _load_module("orchestrator", SCRIPTS_DIR / "orchestrator.py")


# --- ui_messages --------------------------------------------------------

def test_ui_messages_human_mode_contains_expected_markers(capsys, ui_messages):
    ui_messages.success("G2", "coverage 87%")
    ui_messages.fail("G2.1", "mutation score 67%", fix="strengthen assertions")
    out = capsys.readouterr().out
    assert "PASS" in out
    assert "FAIL" in out
    assert "Fix" in out
    assert "G2.1" in out


def test_ui_messages_fail_requires_fix(ui_messages):
    with pytest.raises(ValueError, match="fix"):
        ui_messages.fail("G1", "something broke", fix="")


def test_ui_messages_json_mode(monkeypatch, capsys, ui_messages):
    monkeypatch.setenv("SDD_OUTPUT", "json")
    ui_messages.success("G3", "sonarqube clean", tool="sonarqube")
    line = capsys.readouterr().out.strip()
    payload = json.loads(line)
    assert payload["kind"] == "success"
    assert payload["gate"] == "G3"
    assert payload["details"]["tool"] == "sonarqube"


def test_escalation_requires_how_to_resume(ui_messages):
    with pytest.raises(ValueError, match="how_to_resume"):
        ui_messages.escalation(
            story_id="sc-0012",
            reason="3 cycles failed",
            how_to_resume="",
        )


# --- project-type YAMLs -------------------------------------------------

@pytest.mark.parametrize("name,expected_gate_count", [
    ("cli", 15),
    ("web-api", 17),
])
def test_standalone_project_types_have_expected_gates(name, expected_gate_count, orchestrator):
    cfg = orchestrator.load_project_type_config(name)
    gates = cfg["gates"]
    assert len(gates) == expected_gate_count, (
        f"{name}.yaml should declare {expected_gate_count} gates, got {len(gates)}"
    )
    # Every gate must have an id and a name (hard contract).
    for g in gates:
        assert "id" in g and "name" in g, f"gate without id/name in {name}: {g}"


def test_web_ui_inherits_web_api_and_adds_G9_block(orchestrator):
    """web-ui extends web-api: should have 17 (inherited) + 6 (G9.x added) = 23.
    The G4.1 gate is also overridden (different smoke-boot strategy)."""
    cfg = orchestrator.load_project_type_config("web-ui")
    gate_ids = [g["id"] for g in cfg["gates"]]

    # Inherited from web-api
    for inherited in ["G1", "G2", "G2.1", "G2.2", "G2.3", "G3", "G4", "G4.1",
                      "G5", "G6", "G7", "G8", "G10", "G11", "G12", "G13", "G14"]:
        assert inherited in gate_ids, f"{inherited} should be inherited from web-api"

    # Added UI block
    for added in ["G9.1", "G9.2", "G9.3", "G9.4", "G9.5", "G9.6"]:
        assert added in gate_ids, f"{added} should be added by web-ui"

    assert len(gate_ids) == 23, f"expected 23 total gates, got {len(gate_ids)}"


def test_web_ui_overrides_G4_1_smoke_boot_strategy(orchestrator):
    cfg = orchestrator.load_project_type_config("web-ui")
    g4_1 = next(g for g in cfg["gates"] if g["id"] == "G4.1")
    # web-api default is docker_compose_healthcheck; web-ui overrides to playwright_dev_server.
    assert g4_1["strategy"] == "playwright_dev_server", (
        "web-ui should override G4.1 smoke-boot strategy"
    )


def test_unknown_project_type_produces_clear_config_error(orchestrator, capsys):
    """Asking for an unknown spec.type should print a helpful fix message and
    raise SystemExit(EXIT_CONFIG_ERROR) — not a cryptic trace."""
    with pytest.raises(SystemExit) as excinfo:
        orchestrator.load_project_type_config("nonexistent-stack")
    assert excinfo.value.code == orchestrator.EXIT_CONFIG_ERROR
    out = capsys.readouterr().out
    assert "unknown spec.type" in out
    assert "nonexistent-stack" in out
    # Must suggest alternatives.
    assert "web-ui" in out or "web-api" in out or "cli" in out


# --- gate filtering -----------------------------------------------------

def test_filter_gates_excludes_ship_only_gates_in_build_mode(orchestrator):
    gates = [
        {"id": "G1", "name": "Security", "required": True},
        {"id": "G14", "name": "Release readiness", "required": False, "trigger": "invoked_by_ship"},
        {"id": "G2", "name": "Unit tests", "required": True},
    ]
    filtered = orchestrator.filter_applicable_gates(gates, mode="build")
    ids = [g["id"] for g in filtered]
    assert "G14" not in ids, "G14 should be excluded in build mode (ship-only trigger)"
    assert "G1" in ids
    assert "G2" in ids


def test_filter_gates_includes_ship_only_gates_in_ship_mode(orchestrator):
    gates = [
        {"id": "G14", "name": "Release readiness", "required": False, "trigger": "invoked_by_ship"},
    ]
    filtered = orchestrator.filter_applicable_gates(gates, mode="ship")
    assert [g["id"] for g in filtered] == ["G14"]


# --- CLI smoke ----------------------------------------------------------

def test_orchestrator_cli_requires_mode():
    """--mode is required; missing it should produce a non-zero exit and an
    argparse-style error (not a Python traceback)."""
    result = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "orchestrator.py")],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "--mode" in result.stderr
