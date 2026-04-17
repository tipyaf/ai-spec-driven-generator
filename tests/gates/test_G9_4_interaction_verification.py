"""Gate G9.4 — Interaction verification.

Drives `generate-interaction-tests.py` against a story declaring
`interactions:` and verifies the emitted Playwright `.spec.ts` contains
the expected locators, events, and assertions. We never launch Playwright
— we verify the CODE GENERATION contract.

Because the script uses `find_root()` based on its own `__file__` location,
we import the module directly and monkey-patch `find_root` to point at
the fixture directory.
"""
from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate-interaction-tests.py"


@pytest.fixture
def gen_module(monkeypatch):
    """Load generate-interaction-tests.py as a module."""
    # Hyphenated filename → load via spec.
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("gen_interactions", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _setup(tmp_path: Path, story_yaml: str, name: str = "sc-1234") -> Path:
    project = tmp_path / "proj"
    project.mkdir()
    (project / ".git").mkdir()
    stories = project / "specs" / "stories"
    stories.mkdir(parents=True)
    (stories / f"{name}.yaml").write_text(story_yaml)
    return project


def _run(gen_module, project: Path, story: str, monkeypatch) -> int:
    monkeypatch.setattr(gen_module, "find_root", lambda: project)
    monkeypatch.setattr(sys, "argv", ["gen", "--story", story])
    return gen_module.main()


STORY = textwrap.dedent("""
    id: sc-1234
    title: Counter interactions
    interactions:
      - action: increment
        trigger: "click data-action=increment"
        expected:
          - dom: "data-testid=counter is visible"
          - url: "unchanged"
          - api: "none"
      - action: reset
        trigger: "click data-action=reset"
        expected:
          - dom: "data-testid=counter is visible"
""").strip() + "\n"


def test_generates_spec_file(gen_module, tmp_path, monkeypatch):
    project = _setup(tmp_path, STORY)
    rc = _run(gen_module, project, "sc-1234", monkeypatch)
    assert rc == 0
    out = project / "_work" / "generated" / "interactions" / "sc-1234.spec.ts"
    assert out.exists(), "spec.ts should have been emitted"


def test_emits_one_test_per_interaction(gen_module, tmp_path, monkeypatch):
    project = _setup(tmp_path, STORY)
    _run(gen_module, project, "sc-1234", monkeypatch)
    content = (project / "_work" / "generated" / "interactions" / "sc-1234.spec.ts").read_text()
    assert content.count("test('") == 2
    assert "test('increment'" in content
    assert "test('reset'" in content


def test_imports_playwright_test_and_expect(gen_module, tmp_path, monkeypatch):
    project = _setup(tmp_path, STORY)
    _run(gen_module, project, "sc-1234", monkeypatch)
    content = (project / "_work" / "generated" / "interactions" / "sc-1234.spec.ts").read_text()
    assert "from '@playwright/test'" in content
    assert "test, expect" in content


def test_click_selector_uses_attribute_syntax(gen_module, tmp_path, monkeypatch):
    project = _setup(tmp_path, STORY)
    _run(gen_module, project, "sc-1234", monkeypatch)
    content = (project / "_work" / "generated" / "interactions" / "sc-1234.spec.ts").read_text()
    assert '[data-action="increment"]' in content
    assert ".click()" in content


def test_dom_visibility_assertion_emitted(gen_module, tmp_path, monkeypatch):
    project = _setup(tmp_path, STORY)
    _run(gen_module, project, "sc-1234", monkeypatch)
    content = (project / "_work" / "generated" / "interactions" / "sc-1234.spec.ts").read_text()
    assert '[data-testid="counter"]' in content
    assert "toBeVisible" in content


def test_console_error_assertion_emitted(gen_module, tmp_path, monkeypatch):
    project = _setup(tmp_path, STORY)
    _run(gen_module, project, "sc-1234", monkeypatch)
    content = (project / "_work" / "generated" / "interactions" / "sc-1234.spec.ts").read_text()
    assert "expect(errors).toEqual([])" in content
    assert "pageerror" in content


def test_no_interactions_warns_but_passes(gen_module, tmp_path, monkeypatch):
    story = "id: sc-5555\ntitle: no interactions\n"
    project = _setup(tmp_path, story, name="sc-5555")
    rc = _run(gen_module, project, "sc-5555", monkeypatch)
    assert rc == 0


def test_missing_story_returns_config_error(gen_module, tmp_path, monkeypatch):
    project = _setup(tmp_path, STORY)
    rc = _run(gen_module, project, "does-not-exist", monkeypatch)
    assert rc == 2
