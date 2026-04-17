"""Root conftest for SDD v5 tests.

Provides a factory fixture used by e2e and gate tests to materialize
minimal v5 projects in tmp_path (or point at the pre-built fixtures under
tests/e2e/fixtures/).
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

FRAMEWORK_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "e2e" / "fixtures"


@pytest.fixture
def framework_root() -> Path:
    """Absolute path to the SDD framework repo under test."""
    return FRAMEWORK_ROOT


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def copy_fixture(tmp_path: Path):
    """Return a callable that copies a named e2e fixture into tmp_path.

    Usage:
        project = copy_fixture("web-api")
    """
    def _copy(name: str) -> Path:
        src = FIXTURES_DIR / name
        if not src.exists():
            pytest.skip(f"fixture '{name}' not built")
        dst = tmp_path / name
        shutil.copytree(src, dst)
        # Initialise a throwaway git repo so scripts that shell out to git
        # (check_story_commits --scan-branch, etc.) behave deterministically.
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=dst, check=True)
        subprocess.run(["git", "config", "user.email", "sdd-test@example.org"], cwd=dst, check=True)
        subprocess.run(["git", "config", "user.name", "sdd-test"], cwd=dst, check=True)
        subprocess.run(["git", "add", "-A"], cwd=dst, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "fixture seed"], cwd=dst,
            check=True, env={**os.environ, "GIT_COMMITTER_DATE": "2024-01-01T00:00:00"},
        )
        return dst
    return _copy


@pytest.fixture
def orchestrator_env(framework_root):
    """Env vars that tell orchestrator scripts where the framework lives."""
    def _env(project_root: Path) -> dict:
        return {
            **os.environ,
            "SDD_PROJECT_ROOT": str(project_root),
            "SDD_FRAMEWORK_ROOT": str(framework_root),
        }
    return _env
