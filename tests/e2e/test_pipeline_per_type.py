"""End-to-end pipeline routing tests per spec.type.

Invokes the v5 orchestrator against minimal fixture projects (web-api,
web-ui, cli) and verifies that the correct set of gates is announced and
that the scaffold exits 0. The goal is to lock in the ROUTING contract
(which gates fire for which type, in which order) — NOT the internals of
each gate runner (those live in tests/gates/).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATOR = ROOT / "scripts" / "orchestrator.py"


def _run(project: Path, env: dict, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ORCHESTRATOR), *args],
        capture_output=True, text=True, cwd=project, env=env, timeout=60,
    )


def _announced_gates(stdout: str) -> list[str]:
    """Parse gate IDs from orchestrator header lines like `━━━ G2.3 — …`."""
    ids = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("━") or "—" not in line:
            continue
        # Strip leading unicode bars and whitespace.
        body = line.strip("━ ").split("—", 1)[0].strip()
        if body.startswith("G"):
            ids.append(body)
    return ids


# ---------- web-api ------------------------------------------------------

def test_web_api_pipeline_routes_expected_gates(copy_fixture, orchestrator_env):
    project = copy_fixture("web-api")
    env = orchestrator_env(project)
    result = _run(project, env, "--mode", "build", "--story", "sc-0001-minimal")
    assert result.returncode == 0, f"orch failed: {result.stdout}\n{result.stderr}"

    announced = _announced_gates(result.stdout)
    # Core web-api gates must be present.
    for required in ["G1", "G2", "G2.1", "G2.3", "G3", "G4", "G4.1", "G5", "G6", "G7"]:
        assert required in announced, f"{required} not announced for web-api: {announced}"


def test_web_api_has_no_ui_gates(copy_fixture, orchestrator_env):
    project = copy_fixture("web-api")
    env = orchestrator_env(project)
    result = _run(project, env, "--mode", "build", "--story", "sc-0001-minimal")
    announced = _announced_gates(result.stdout)
    # UI gates (G9.x) must NOT fire for a pure web-api project.
    ui = [g for g in announced if g.startswith("G9")]
    assert ui == [], f"web-api should have no G9.* gates, got: {ui}"


def test_web_api_announces_g11_observability(copy_fixture, orchestrator_env):
    """G11 is a web-api marker — proves we loaded web-api.yaml, not cli.yaml."""
    project = copy_fixture("web-api")
    env = orchestrator_env(project)
    result = _run(project, env, "--mode", "build", "--story", "sc-0001-minimal")
    assert "G11" in _announced_gates(result.stdout)


# ---------- cli ----------------------------------------------------------

def test_cli_pipeline_routes_expected_gates(copy_fixture, orchestrator_env):
    project = copy_fixture("cli")
    env = orchestrator_env(project)
    result = _run(project, env, "--mode", "build", "--story", "sc-0001-minimal")
    assert result.returncode == 0, f"orch failed: {result.stdout}\n{result.stderr}"

    announced = _announced_gates(result.stdout)
    for required in ["G1", "G2", "G2.1", "G2.3", "G3", "G4", "G4.1", "G5", "G6", "G7", "G10"]:
        assert required in announced, f"{required} missing for cli: {announced}"


def test_cli_excludes_web_only_gates(copy_fixture, orchestrator_env):
    """CLI must NOT get G11 (observability) or G12 (DAST) or any G9.*."""
    project = copy_fixture("cli")
    env = orchestrator_env(project)
    result = _run(project, env, "--mode", "build", "--story", "sc-0001-minimal")
    announced = _announced_gates(result.stdout)
    for forbidden in ["G11", "G12"]:
        assert forbidden not in announced, f"{forbidden} should not fire for cli"
    assert not [g for g in announced if g.startswith("G9")], \
        f"cli should have no G9.* gates: {announced}"


# ---------- web-ui -------------------------------------------------------

def test_web_ui_inherits_web_api_gates(copy_fixture, orchestrator_env):
    """web-ui `extends: web-api` — base gates must still be announced."""
    project = copy_fixture("web-ui")
    env = orchestrator_env(project)
    result = _run(project, env, "--mode", "build", "--story", "sc-0001-minimal")
    assert result.returncode == 0
    announced = _announced_gates(result.stdout)
    for required in ["G1", "G2", "G2.3", "G3", "G4", "G4.1", "G11"]:
        assert required in announced, f"inherited gate {required} missing: {announced}"


def test_web_ui_adds_all_g9_gates(copy_fixture, orchestrator_env):
    """Every G9.x gate must be announced for web-ui."""
    project = copy_fixture("web-ui")
    env = orchestrator_env(project)
    result = _run(project, env, "--mode", "build", "--story", "sc-0001-minimal")
    announced = _announced_gates(result.stdout)
    for g in ["G9.1", "G9.2", "G9.3", "G9.4", "G9.5", "G9.6"]:
        assert g in announced, f"{g} missing for web-ui: {announced}"


# ---------- mode selection ----------------------------------------------

@pytest.mark.parametrize("fixture_name", ["web-api", "cli", "web-ui"])
def test_all_fixtures_run_review_mode(copy_fixture, orchestrator_env, fixture_name):
    """Review mode must work on every fixture (read-only by contract)."""
    project = copy_fixture(fixture_name)
    env = orchestrator_env(project)
    result = _run(project, env, "--mode", "review")
    assert result.returncode == 0, f"{fixture_name} review failed: {result.stdout}\n{result.stderr}"


def test_build_requires_story(copy_fixture, orchestrator_env):
    project = copy_fixture("web-api")
    env = orchestrator_env(project)
    result = _run(project, env, "--mode", "build")
    # Config-error exit is 3.
    assert result.returncode == 3
    assert "requires --story" in (result.stdout + result.stderr)


def test_g14_release_readiness_only_on_ship(copy_fixture, orchestrator_env):
    """G14 carries trigger: invoked_by_ship — absent from /build."""
    project = copy_fixture("web-api")
    env = orchestrator_env(project)
    build = _run(project, env, "--mode", "build", "--story", "sc-0001-minimal")
    assert "G14" not in _announced_gates(build.stdout), \
        "G14 must not appear during /build"
    review = _run(project, env, "--mode", "review")
    # review is treated as 'review' — G14's trigger=invoked_by_ship -> absent.
    assert "G14" not in _announced_gates(review.stdout)
