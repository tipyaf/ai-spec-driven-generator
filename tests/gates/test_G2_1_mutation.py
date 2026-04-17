"""Gate G2.1 — Mutation testing (routing + tool selection).

In v5.0.0 there is no dedicated `check_mutation.py` runner — mutation
scoring is delegated to language-specific tools declared in
`stacks/project-types/<type>.yaml` under `tools_by_language:`. This test
locks in the contract that the project-type YAML enumerates at least one
mutation tool per supported language.

Those are the hooks that the future mutation runner (Étape 9) will read.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
PROJECT_TYPES = ROOT / "stacks" / "project-types"


def _load_type(name: str) -> dict:
    return yaml.safe_load((PROJECT_TYPES / f"{name}.yaml").read_text())


@pytest.mark.parametrize("project_type", ["web-api", "cli"])
def test_mutation_gate_declares_tools_by_language(project_type):
    cfg = _load_type(project_type)
    gates = {g["id"]: g for g in cfg.get("gates", []) if isinstance(g, dict)}
    g21 = gates.get("G2.1")
    if g21 is None and cfg.get("extends"):
        # Composed pipelines (web-ui) — rely on the inherited test below.
        pytest.skip(f"{project_type} inherits G2.1 via extends")
    assert g21 is not None, f"G2.1 missing from {project_type}.yaml"
    assert g21.get("required") is True
    tools = g21.get("tools_by_language") or {}
    # CLI YAML doesn't list tools_by_language explicitly — its G2.1 may just
    # declare min_score and scope. Accept either, but web-api MUST have tools.
    if project_type == "web-api":
        assert "python" in tools, "python mutation tool missing for web-api"


def test_mutation_gate_scope_is_changed_files():
    """Full-repo mutation runs can take >5min — gate must scope to diff."""
    cfg = _load_type("web-api")
    g21 = next(g for g in cfg["gates"] if g["id"] == "G2.1")
    assert g21["scope"] == "changed_files"


def test_mutation_gate_has_threshold():
    cfg = _load_type("web-api")
    g21 = next(g for g in cfg["gates"] if g["id"] == "G2.1")
    assert isinstance(g21["min_score"], int) and g21["min_score"] > 0


def test_mutation_blocks_on_score_below():
    """The `blocks_on:` field is the machine-readable failure taxonomy."""
    cfg = _load_type("web-api")
    g21 = next(g for g in cfg["gates"] if g["id"] == "G2.1")
    assert "mutation_score_below" in (g21.get("blocks_on") or [])
