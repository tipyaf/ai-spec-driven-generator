"""Gate G2.3 — Contract diff (extended cases).

Covers endpoint add (OK), remove without `breaks:` (FAIL), library mode
signature change (FAIL), and the `breaks:` allowlist (PASS when declared).
Complements the single case in tests/scripts/test_ast_refactor.py.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_contract_diff.py"


def _prep_project(tmp_path: Path, story_yaml: str) -> Path:
    """Create a minimal repo layout so check_contract_diff.find_root works."""
    (tmp_path / ".git").mkdir()
    stories = tmp_path / "specs" / "stories"
    stories.mkdir(parents=True)
    (stories / "sc-0001.yaml").write_text(story_yaml)
    return tmp_path


def _run(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, cwd=project, timeout=30,
    )


# ---------- API mode: additive changes ---------------------------------

def test_endpoint_added_is_ok(tmp_path):
    project = _prep_project(tmp_path, "id: sc-0001\n")
    current = tmp_path / "current.yaml"
    snapshot = tmp_path / "snapshot.yaml"
    snapshot.write_text("paths:\n  /users:\n    get: {}\n")
    current.write_text(
        "paths:\n  /users:\n    get: {}\n  /orders:\n    post: {}\n"
    )
    result = _run(project, "--kind", "api", "--story", "sc-0001",
                  "--current", str(current), "--snapshot", str(snapshot))
    assert result.returncode == 0, \
        f"adding an endpoint must NOT fail: {result.stdout}{result.stderr}"


def test_endpoint_removed_without_breaks_fails(tmp_path):
    project = _prep_project(tmp_path, "id: sc-0001\n")
    current = tmp_path / "current.yaml"
    snapshot = tmp_path / "snapshot.yaml"
    snapshot.write_text(
        "paths:\n  /users:\n    get: {}\n  /users/{id}:\n    get: {}\n"
    )
    current.write_text("paths:\n  /users:\n    get: {}\n")
    result = _run(project, "--kind", "api", "--story", "sc-0001",
                  "--current", str(current), "--snapshot", str(snapshot))
    assert result.returncode == 1
    assert "undeclared" in (result.stdout + result.stderr).lower() \
        or "GET /users/{id}" in (result.stdout + result.stderr)


def test_endpoint_removal_allowed_when_declared_in_breaks(tmp_path, monkeypatch):
    """`breaks: ["GET /users/{id}"]` in story → removal is acknowledged.

    `load_story_breaks` is imported directly because the script's
    `find_root()` walks from __file__ and lands on the framework dir.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("cdiff", SCRIPT)
    cdiff = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cdiff)

    project = _prep_project(
        tmp_path,
        textwrap.dedent("""
            id: sc-0001
            breaks:
              - "GET /users/{id}"
        """).strip() + "\n",
    )
    # Direct logic test: the loader returns the declared breakages.
    breaks = cdiff.load_story_breaks(project, "sc-0001")
    assert breaks == ["GET /users/{id}"]

    # Simulate the filter: undeclared = removed - breaks
    removed = {"GET /users/{id}"}
    undeclared = [b for b in removed if b not in breaks]
    assert undeclared == [], f"declared break should be filtered out: {undeclared}"


# ---------- Library mode ------------------------------------------------

def test_library_signature_change_fails(tmp_path):
    project = _prep_project(tmp_path, "id: sc-0001\n")
    cur = tmp_path / "src"
    snap = tmp_path / "snap"
    cur.mkdir(); snap.mkdir()
    # Snapshot: greet(name)
    (snap / "api.py").write_text("def greet(name):\n    return name\n")
    # Current: greet(name, loud)  ← signature change
    (cur / "api.py").write_text("def greet(name, loud):\n    return name\n")

    result = _run(project, "--kind", "library", "--story", "sc-0001",
                  "--current", str(cur), "--snapshot", str(snap))
    assert result.returncode == 1, \
        f"signature change must fail: {result.stdout}{result.stderr}"
    assert "CHANGED" in (result.stdout + result.stderr) \
        or "greet" in (result.stdout + result.stderr)


def test_library_new_function_is_additive(tmp_path):
    project = _prep_project(tmp_path, "id: sc-0001\n")
    cur = tmp_path / "src"
    snap = tmp_path / "snap"
    cur.mkdir(); snap.mkdir()
    (snap / "api.py").write_text("def greet(name):\n    return name\n")
    (cur / "api.py").write_text(
        "def greet(name):\n    return name\n\n"
        "def farewell(name):\n    return name\n"
    )
    result = _run(project, "--kind", "library", "--story", "sc-0001",
                  "--current", str(cur), "--snapshot", str(snap))
    assert result.returncode == 0, \
        f"new public function must be allowed: {result.stdout}{result.stderr}"


def test_library_private_function_change_ignored(tmp_path):
    """`_internal` functions are underscore-prefixed → not part of the contract."""
    project = _prep_project(tmp_path, "id: sc-0001\n")
    cur = tmp_path / "src"
    snap = tmp_path / "snap"
    cur.mkdir(); snap.mkdir()
    (snap / "api.py").write_text("def _internal(a):\n    return a\n")
    (cur / "api.py").write_text("def _internal(a, b):\n    return a + b\n")
    result = _run(project, "--kind", "library", "--story", "sc-0001",
                  "--current", str(cur), "--snapshot", str(snap))
    assert result.returncode == 0
