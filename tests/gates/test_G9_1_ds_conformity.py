"""Gate G9.1 — Design System conformity.

Scans staged .tsx/.jsx/.vue files for hex colors and px values that are
NOT declared in `specs/design-system.yaml`. The production script uses
`find_root()` based on its own `__file__`, so we import it as a module
and monkey-patch `find_root` + cwd for testing.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_ds_conformity.py"


@pytest.fixture
def ds_module():
    spec = importlib.util.spec_from_file_location("ds_conf", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _init_project(tmp_path: Path, ds_yaml: str) -> Path:
    project = tmp_path / "proj"
    project.mkdir()
    (project / "specs").mkdir()
    (project / "specs" / "design-system.yaml").write_text(ds_yaml)
    _git(project, "init", "-q", "-b", "main")
    _git(project, "config", "user.email", "t@t")
    _git(project, "config", "user.name", "t")
    (project / "README.md").write_text("# seed")
    _git(project, "add", "README.md")
    _git(project, "commit", "-q", "-m", "seed")
    return project


def _run(ds_module, project: Path, monkeypatch) -> int:
    monkeypatch.setattr(ds_module, "find_root", lambda: project)
    monkeypatch.setattr(sys, "argv", ["ds"])
    return ds_module.main()


DS_YAML = textwrap.dedent("""
    name: demo
    colors:
      primary: "#1e40af"
      surface: "#ffffff"
    spacing:
      md: 16
      lg: 24
""").strip() + "\n"


def test_hardcoded_hex_color_fails(tmp_path, ds_module, monkeypatch):
    project = _init_project(tmp_path, DS_YAML)
    (project / "src").mkdir()
    (project / "src" / "Bad.tsx").write_text('export const c = "#c0ffee";\n')
    _git(project, "add", "src/Bad.tsx")
    assert _run(ds_module, project, monkeypatch) == 1


def test_token_color_passes(tmp_path, ds_module, monkeypatch):
    project = _init_project(tmp_path, DS_YAML)
    (project / "src").mkdir()
    (project / "src" / "Good.tsx").write_text(
        'export const c = "#1e40af";\n'
        'export const bg = "#ffffff";\n'
    )
    _git(project, "add", "src/Good.tsx")
    assert _run(ds_module, project, monkeypatch) == 0


def test_hardcoded_px_outside_scale_fails(tmp_path, ds_module, monkeypatch):
    project = _init_project(tmp_path, DS_YAML)
    (project / "src").mkdir()
    (project / "src" / "Bad.tsx").write_text(
        "const s = { padding: '13px' };\n"
    )
    _git(project, "add", "src/Bad.tsx")
    assert _run(ds_module, project, monkeypatch) == 1


def test_px_within_scale_passes(tmp_path, ds_module, monkeypatch):
    project = _init_project(tmp_path, DS_YAML)
    (project / "src").mkdir()
    (project / "src" / "Good.tsx").write_text(
        "const s = { padding: '16px', margin: '24px' };\n"
    )
    _git(project, "add", "src/Good.tsx")
    assert _run(ds_module, project, monkeypatch) == 0


def test_no_ui_files_changed_passes(tmp_path, ds_module, monkeypatch):
    project = _init_project(tmp_path, DS_YAML)
    (project / "docs.md").write_text("some doc\n")
    _git(project, "add", "docs.md")
    assert _run(ds_module, project, monkeypatch) == 0
