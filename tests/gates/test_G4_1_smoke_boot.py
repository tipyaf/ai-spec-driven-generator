"""Gate G4.1 — Smoke boot strategy selector.

Each stack template ships a `smoke-boot.yaml` with a `strategy:` key. The
orchestrator picks the strategy from the ACTIVE stack profile declared in
`_work/stacks/registry.yaml`. This test validates the contract for the two
built-in strategies (uvicorn and vite_preview) and the CLI subprocess
strategy from `stacks/project-types/cli.yaml`.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
STACKS = ROOT / "stacks" / "templates"
PROJECT_TYPES = ROOT / "stacks" / "project-types"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def test_python_fastapi_uses_uvicorn_strategy():
    sb = _load(STACKS / "python-fastapi" / "smoke-boot.yaml")
    assert sb["strategy"] == "uvicorn_healthcheck"
    assert "uvicorn" in sb["start_command"]
    assert sb["healthcheck"]["url"].endswith("/health")
    assert sb["healthcheck"]["expect_status"] == 200


def test_typescript_react_uses_vite_preview_strategy():
    sb = _load(STACKS / "typescript-react" / "smoke-boot.yaml")
    assert sb["strategy"] == "vite_preview_healthcheck"
    assert "preview" in sb["start_command"]
    # SPA smoke check = the root shell ships.
    assert "root" in sb["healthcheck"]["expect_body_contains"]


def test_cli_strategy_is_subprocess():
    """CLI project-type declares strategy: subprocess at gate level."""
    cfg = _load(PROJECT_TYPES / "cli.yaml")
    g41 = next(g for g in cfg["gates"] if g["id"] == "G4.1")
    assert g41["strategy"] == "subprocess"
    # Subprocess strategy must invoke --help, --version, and a canonical command.
    steps_text = yaml.safe_dump(g41["steps"])
    assert "--help" in steps_text
    assert "--version" in steps_text
    assert "canonical_command" in steps_text


def test_web_api_default_strategy_is_docker_compose():
    cfg = _load(PROJECT_TYPES / "web-api.yaml")
    g41 = next(g for g in cfg["gates"] if g["id"] == "G4.1")
    assert g41["strategy"] == "docker_compose_healthcheck"


def test_web_ui_overrides_to_playwright_strategy():
    """web-ui inherits web-api but gates_override swaps G4.1 to playwright."""
    cfg = _load(PROJECT_TYPES / "web-ui.yaml")
    assert cfg["extends"] == "web-api"
    override = cfg["gates_override"]["G4.1"]
    assert override["strategy"] == "playwright_dev_server"


@pytest.mark.parametrize("stack", ["python-fastapi", "typescript-react"])
def test_teardown_block_present(stack):
    """All smoke-boot strategies MUST declare a teardown block (no orphan procs)."""
    sb = _load(STACKS / stack / "smoke-boot.yaml")
    td = sb.get("teardown") or {}
    assert td.get("signal")
    assert td.get("grace_period_s")


def test_healthcheck_has_timeout():
    sb = _load(STACKS / "python-fastapi" / "smoke-boot.yaml")
    assert sb["healthcheck"]["timeout_s"] >= 10
