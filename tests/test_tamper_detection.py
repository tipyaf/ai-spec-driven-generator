"""Orchestrator pre-flight tamper detection, integrated on a real git repo.

Simulates the three bypass patterns the SDD v5 orchestrator looks for:

1. TEST TAMPERING — RED commit writes a test with `assert X`; a later
   commit removes that assertion. `check_test_tampering.py --scan-branch`
   must flag it.
2. PROD CODE WITHOUT STORY — a commit touches production files but
   the subject line lacks `[sc-NNNN]`. `check_story_commits.py
   --scan-branch` must flag it.
3. TDD ORDER — a story has a `feat:` (GREEN) commit but no preceding
   `test:` (RED) commit. `check_tdd_order.py --scan-branch` must flag it.

Because the scripts' `find_root()` walks from `__file__` (scripts dir),
we import them as modules and monkey-patch the root resolver.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git(cwd: Path, *args: str, **kw) -> subprocess.CompletedProcess:
    env = {**os.environ,
           "GIT_COMMITTER_DATE": kw.pop("date", "2024-01-01T00:00:00"),
           "GIT_AUTHOR_DATE": kw.pop("adate", "2024-01-01T00:00:00")}
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True, env=env)


def _setup_repo(tmp_path: Path) -> Path:
    project = tmp_path / "repo"
    project.mkdir()
    _git(project, "init", "-q", "-b", "main")
    _git(project, "config", "user.email", "t@t")
    _git(project, "config", "user.name", "t")
    # CLAUDE.md so find_project_root lands on the tmp repo
    (project / "CLAUDE.md").write_text("# toy project\n")
    (project / "README.md").write_text("# seed\n")
    _git(project, "add", "CLAUDE.md", "README.md")
    _git(project, "commit", "-q", "-m", "chore: seed [sc-0000]")
    # Create a fake origin/main ref pointing at seed, so merge-base works.
    _git(project, "update-ref", "refs/remotes/origin/main", "HEAD")
    return project


# ---------- 1. TEST TAMPERING -----------------------------------------

def test_tampering_flags_removed_assertion(tmp_path, monkeypatch):
    project = _setup_repo(tmp_path)
    tests_dir = project / "tests"
    tests_dir.mkdir()
    test_file = tests_dir / "test_balance.py"

    # Commit 1 (RED): a real assertion.
    test_file.write_text(
        "def test_balance():\n    balance = 100\n    assert balance == 100\n"
    )
    _git(project, "add", "tests/test_balance.py")
    _git(project, "commit", "-q", "-m", "test: RED balance [sc-0001]")

    # Commit 2 (tampered): assertion WEAKENED — `assert True` instead.
    test_file.write_text(
        "def test_balance():\n    balance = 100\n    assert True  # weakened\n"
    )
    _git(project, "add", "tests/test_balance.py")
    _git(project, "commit", "-q", "-m", "feat: GREEN balance [sc-0001]")

    # Run tampering check scoped to this repo.
    tamper = _load("check_test_tampering")
    monkeypatch.setattr(tamper, "find_project_root", lambda: project)
    rc = tamper._scan_branch(project)
    assert rc == 1, "weakened assertion must be detected"


def test_tampering_passes_on_clean_history(tmp_path, monkeypatch):
    project = _setup_repo(tmp_path)
    tests_dir = project / "tests"
    tests_dir.mkdir()
    test_file = tests_dir / "test_x.py"

    test_file.write_text(
        "def test_x():\n    assert 2 + 2 == 4\n"
    )
    _git(project, "add", "tests/test_x.py")
    _git(project, "commit", "-q", "-m", "test: RED [sc-0002]")

    # Add MORE assertions — net-additive, no removal.
    test_file.write_text(
        "def test_x():\n    assert 2 + 2 == 4\n    assert 3 * 3 == 9\n"
    )
    _git(project, "add", "tests/test_x.py")
    _git(project, "commit", "-q", "-m", "test: strengthen [sc-0002]")

    tamper = _load("check_test_tampering")
    monkeypatch.setattr(tamper, "find_project_root", lambda: project)
    rc = tamper._scan_branch(project)
    assert rc == 0


# ---------- 2. PROD CODE WITHOUT STORY --------------------------------

def test_story_commits_flags_prod_without_tag(tmp_path, monkeypatch):
    project = _setup_repo(tmp_path)
    (project / "app").mkdir()
    (project / "app" / "main.py").write_text("x = 1\n")
    _git(project, "add", "app/main.py")
    _git(project, "commit", "-q", "-m", "chore: random commit")  # no [sc-*]

    story_commits = _load("check_story_commits")
    monkeypatch.setattr(story_commits, "find_root", lambda: project)
    rc = story_commits._scan_branch()
    assert rc == 1, "prod code without [sc-*] must be flagged"


def test_story_commits_passes_when_tag_present(tmp_path, monkeypatch):
    project = _setup_repo(tmp_path)
    (project / "app").mkdir()
    (project / "app" / "main.py").write_text("x = 1\n")
    _git(project, "add", "app/main.py")
    _git(project, "commit", "-q", "-m", "feat: add x [sc-0003]")

    story_commits = _load("check_story_commits")
    monkeypatch.setattr(story_commits, "find_root", lambda: project)
    rc = story_commits._scan_branch()
    assert rc == 0


# ---------- 3. TDD ORDER ----------------------------------------------

def _write_build_file(project: Path, story: str) -> None:
    """check_tdd_order scans stories that have a build file."""
    build = project / "_work" / "build"
    build.mkdir(parents=True, exist_ok=True)
    (build / f"{story}.yaml").write_text(
        f"id: {story}\nstatus: building\n"
    )


def test_tdd_order_flags_green_before_red(tmp_path, monkeypatch):
    project = _setup_repo(tmp_path)
    _write_build_file(project, "sc-1004")

    # GREEN first (wrong order).
    (project / "app").mkdir()
    (project / "app" / "a.py").write_text("x = 1\n")
    _git(project, "add", "app/a.py", "_work/build/sc-1004.yaml")
    _git(project, "commit", "-q", "-m", "feat: GREEN impl [sc-1004]",
         date="2024-01-02T00:00:00", adate="2024-01-02T00:00:00")

    # RED after (also wrong — test came after code).
    (project / "tests").mkdir()
    (project / "tests" / "test_a.py").write_text("def test_a():\n    assert 1 == 1\n")
    _git(project, "add", "tests/test_a.py")
    _git(project, "commit", "-q", "-m", "test: RED late [sc-1004]",
         date="2024-01-03T00:00:00", adate="2024-01-03T00:00:00")

    tdd = _load("check_tdd_order")
    monkeypatch.setattr(tdd, "find_project_root", lambda: project)
    # Reset the module-level violations list before invocation.
    tdd.violations.clear()
    rc = tdd._scan_branch(project)
    assert rc == 1, "GREEN-before-RED commit order must be flagged"


def test_tdd_order_passes_when_red_precedes_green(tmp_path, monkeypatch):
    project = _setup_repo(tmp_path)
    _write_build_file(project, "sc-1005")

    (project / "tests").mkdir()
    (project / "tests" / "test_b.py").write_text(
        "def test_b():\n    assert 1 == 1\n"
    )
    _git(project, "add", "tests/test_b.py")
    _git(project, "commit", "-q", "-m", "test: RED b [sc-1005]",
         date="2024-01-04T00:00:00", adate="2024-01-04T00:00:00")

    (project / "app").mkdir()
    (project / "app" / "b.py").write_text("y = 2\n")
    _git(project, "add", "app/b.py", "_work/build/sc-1005.yaml")
    _git(project, "commit", "-q", "-m", "feat: GREEN b [sc-1005]",
         date="2024-01-05T00:00:00", adate="2024-01-05T00:00:00")

    tdd = _load("check_tdd_order")
    monkeypatch.setattr(tdd, "find_project_root", lambda: project)
    tdd.violations.clear()
    rc = tdd._scan_branch(project)
    assert rc == 0
