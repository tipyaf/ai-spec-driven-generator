"""End-to-end tests for migrate-v4-to-v5.sh.

Each test spins up a minimal v4 project fixture in a pytest tmp_path, invokes
the migration script (with --yes so it never prompts), and asserts on the
resulting filesystem state.

Run with:
    .venv-sdd-dev/bin/pytest tests/test_migration_v4_to_v5.py -v
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATE_SH = REPO_ROOT / "scripts" / "migrate-v4-to-v5.sh"


# ── Fixture: minimal v4 project ────────────────────────────────────────────

def _make_v4_project(root: Path) -> None:
    """Create a minimal v4.x-looking SDD project inside root."""
    (root / "specs" / "stories").mkdir(parents=True)
    (root / "_work" / "build").mkdir(parents=True)
    (root / "_work" / "spec").mkdir(parents=True)
    (root / "_work" / "ux" / "wireframes").mkdir(parents=True)
    (root / "_work" / "stacks").mkdir(parents=True)
    (root / "memory").mkdir(parents=True)
    (root / ".claude").mkdir(parents=True)

    # CLAUDE.md referencing v4
    (root / "CLAUDE.md").write_text(
        "# Project\n"
        "\nUsing SDD v4.1.1 framework with 11 gates (G1-G11).\n"
        "Agents: tester, reviewer, developer, orchestrator.\n",
        encoding="utf-8",
    )

    # feature-tracker.yaml
    (root / "specs" / "feature-tracker.yaml").write_text(
        "version: 1\n"
        "stories:\n"
        "  - id: sc-0001\n"
        "    title: Login flow\n"
        "    status: blocked\n"
        "  - id: sc-0002\n"
        "    title: Orphan story\n"
        "    status: validated\n",
        encoding="utf-8",
    )

    # A story file with some v4-era content
    (root / "specs" / "stories" / "sc-0001.yaml").write_text(
        "id: sc-0001\n"
        "type: web-ui\n"
        "title: Login flow\n"
        "owner: tester\n",
        encoding="utf-8",
    )

    # _work build file
    (root / "_work" / "build" / "sc-0001.yaml").write_text(
        "id: sc-0001\n"
        "gates:\n"
        "  G1: pass\n"
        "  G11: pass\n",
        encoding="utf-8",
    )

    # memory
    (root / "memory" / "LESSONS.md").write_text("# Lessons learned\n", encoding="utf-8")

    # settings.json
    (root / ".claude" / "settings.json").write_text(
        json.dumps({
            "hooks": {"PreToolUse": [{"_comment": "user-defined", "matcher": "X", "hooks": []}]},
            "custom": {"user-value": True},
        }, indent=2),
        encoding="utf-8",
    )

    # Initialize git so the script sees a clean repo
    env = os.environ.copy()
    env.setdefault("GIT_AUTHOR_NAME", "test")
    env.setdefault("GIT_AUTHOR_EMAIL", "test@example.com")
    env.setdefault("GIT_COMMITTER_NAME", "test")
    env.setdefault("GIT_COMMITTER_EMAIL", "test@example.com")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True, env=env)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=env)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "v4 baseline"],
        cwd=root, check=True, env=env,
    )


@pytest.fixture
def v4_project(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    root.mkdir()
    _make_v4_project(root)
    return root


def _run_migration(project: Path, *extra: str) -> subprocess.CompletedProcess:
    cmd = [
        "bash", str(MIGRATE_SH),
        "--project-path", str(project),
        "--yes",
        *extra,
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


# ── Tests ──────────────────────────────────────────────────────────────────


def test_migrate_script_exists_and_executable():
    assert MIGRATE_SH.exists()
    assert os.access(MIGRATE_SH, os.X_OK)


def test_dry_run_makes_no_changes(v4_project: Path):
    before = _snapshot(v4_project)
    result = _run_migration(v4_project, "--dry-run")
    assert result.returncode == 0, result.stderr
    after = _snapshot(v4_project)
    # Dry run must NOT create the backup dir or new _work/ dirs.
    assert not (v4_project / "_backup_v4").exists()
    assert before == after


def test_full_migration_creates_backup(v4_project: Path):
    result = _run_migration(v4_project)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"

    backup = v4_project / "_backup_v4"
    assert backup.exists(), "backup directory missing"
    assert (backup / "CLAUDE.md").exists()
    assert (backup / "specs").is_dir()
    assert (backup / "memory").is_dir()


def test_full_migration_updates_claude_md(v4_project: Path):
    result = _run_migration(v4_project)
    assert result.returncode == 0

    claude = (v4_project / "CLAUDE.md").read_text()
    # v5-indicative markers
    assert "v5" in claude.lower() or "14 gates" in claude or "G1-G14" in claude
    # old marker should be replaced
    assert "G1-G11" not in claude


def test_full_migration_merges_settings_json(v4_project: Path):
    # Provide a fake template next to where the script expects it.
    # The repo's own stacks/hooks/settings-hooks-example.json is used by default.
    result = _run_migration(v4_project)
    assert result.returncode == 0
    settings = json.loads((v4_project / ".claude" / "settings.json").read_text())
    assert "hooks" in settings
    # Custom user keys preserved
    assert settings.get("custom", {}).get("user-value") is True


def test_full_migration_creates_new_work_dirs(v4_project: Path):
    result = _run_migration(v4_project)
    assert result.returncode == 0
    for sub in ("visual-baseline", "perf-baseline", "contracts", "data-fixtures"):
        d = v4_project / "_work" / sub
        assert d.is_dir(), f"{d} missing"


def test_full_migration_creates_stacks_registry(v4_project: Path):
    result = _run_migration(v4_project)
    assert result.returncode == 0
    reg = v4_project / "_work" / "stacks" / "registry.yaml"
    assert reg.exists()
    txt = reg.read_text()
    assert "python-fastapi" in txt
    assert "typescript-react" in txt


def test_full_migration_writes_report(v4_project: Path):
    result = _run_migration(v4_project)
    assert result.returncode == 0
    report = v4_project / "_backup_v4" / "MIGRATION_REPORT.md"
    assert report.exists()
    body = report.read_text()
    assert "v4" in body and "v5" in body
    assert "Post-migration checklist" in body


def test_feature_tracker_upgrade_marks_blocked_as_escalated(v4_project: Path):
    result = _run_migration(v4_project)
    assert result.returncode == 0
    content = (v4_project / "specs" / "feature-tracker.yaml").read_text()
    # sc-0001 was "blocked" -> "escalated"
    assert "escalated" in content
    # sc-0002 was "validated" but no build file — should carry a migration note
    assert "MIGRATION" in content or "no build file" in content


def test_agent_rename_on_story_files(v4_project: Path):
    result = _run_migration(v4_project)
    assert result.returncode == 0
    story = (v4_project / "specs" / "stories" / "sc-0001.yaml").read_text()
    assert "tester" not in story
    assert "test-author" in story


def test_rollback_restores_state(v4_project: Path):
    before = _snapshot(v4_project)
    r1 = _run_migration(v4_project)
    assert r1.returncode == 0
    # sanity: state changed
    assert _snapshot(v4_project) != before

    r2 = _run_migration(v4_project, "--rollback")
    assert r2.returncode == 0, r2.stderr
    after = _snapshot(v4_project)

    # Critical files restored byte-for-byte
    for rel in ("CLAUDE.md", "specs/feature-tracker.yaml", "specs/stories/sc-0001.yaml"):
        assert after[rel] == before[rel], f"{rel} not restored"


def test_claude_md_does_not_double_prefix_code_reviewer(v4_project: Path):
    """v5.0.2 regression: `reviewer` → `code-reviewer` produced
    `code-code-reviewer` because the regex ran twice over the already-renamed
    token. The negative lookbehind in v5.0.3+ must prevent this."""
    r = _run_migration(v4_project)
    assert r.returncode == 0, r.stderr
    claude = (v4_project / "CLAUDE.md").read_text(encoding="utf-8")
    assert "code-code-reviewer" not in claude, (
        "Double-prefix bug: the replacement was applied more than once"
    )
    assert "code-reviewer" in claude


def test_stack_registry_detects_project_stack(v4_project: Path, tmp_path: Path):
    """registry.yaml must not enable every stack unconditionally.
    Here the v4 fixture has NO package.json nor pyproject.toml, so every
    built-in stack should be `enabled: false` — letting the dev opt in
    rather than carrying dead config."""
    r = _run_migration(v4_project)
    assert r.returncode == 0, r.stderr
    registry = (v4_project / "_work" / "stacks" / "registry.yaml").read_text()
    # Every stack on the fixture should be disabled (no project deps to detect).
    for stack in ("python-fastapi", "typescript-react", "postgres", "nodejs-express"):
        # Accept either: absent, or `enabled: false` within the block.
        assert stack in registry
    # Parse structurally.
    import yaml
    data = yaml.safe_load(registry)
    for stack, cfg in data.get("stacks", {}).items():
        assert cfg["enabled"] is False, (
            f"{stack} should be disabled on a fixture without any detectable deps, got enabled"
        )


def test_stack_registry_enables_detected_stack(tmp_path: Path):
    """If the project has a React package.json, typescript-react must be
    auto-enabled without manual intervention."""
    root = tmp_path / "reacty"
    _make_v4_project(root)
    # Add a React-ish package.json at the root.
    (root / "package.json").write_text(json.dumps({
        "name": "reacty",
        "dependencies": {"react": "^18.0.0", "next": "^14.0.0"},
    }), encoding="utf-8")
    r = _run_migration(root, "--force")
    assert r.returncode == 0, r.stderr
    import yaml
    data = yaml.safe_load((root / "_work" / "stacks" / "registry.yaml").read_text())
    assert data["stacks"]["typescript-react"]["enabled"] is True


def test_spec_type_write_targets_root_spec_not_story(v4_project: Path):
    """v5.0.2 regression: cmd_spec_type --write picked the first sc-*.yaml
    it found and prepended `type:` to a per-story overlay. v5.0.3 must
    write ONLY into a root project spec (or leave things alone)."""
    # Seed a ROOT-looking spec the script can target.
    (v4_project / "specs" / "myproj.yaml").write_text(
        "project:\n  name: myproj\n",
        encoding="utf-8",
    )
    # Seed a story overlay that must NOT be touched.
    (v4_project / "_work" / "spec" / "sc-0042.yaml").write_text(
        "# Story overlay — sc-0042\n"
        "# No spec delta.\n",
        encoding="utf-8",
    )
    r = _run_migration(v4_project, "--force")
    assert r.returncode == 0, r.stderr
    overlay = (v4_project / "_work" / "spec" / "sc-0042.yaml").read_text()
    assert not overlay.startswith("type:"), (
        "Story overlay must not be rewritten with type:, it's not a root spec"
    )
    assert "# Story overlay — sc-0042" in overlay


def test_idempotent_second_run_is_noop_for_core_files(v4_project: Path):
    r1 = _run_migration(v4_project)
    assert r1.returncode == 0
    claude_after_first = (v4_project / "CLAUDE.md").read_text()

    r2 = _run_migration(v4_project, "--force")
    assert r2.returncode == 0
    claude_after_second = (v4_project / "CLAUDE.md").read_text()
    # Second run should not duplicate the v5 note.
    assert claude_after_first.count("v5 migration note") == claude_after_second.count("v5 migration note")


# ── Helpers ────────────────────────────────────────────────────────────────


def _snapshot(root: Path) -> dict[str, str]:
    """Map of relpath -> content for non-binary files in project."""
    out: dict[str, str] = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if ".git" in p.parts:
            continue
        rel = str(p.relative_to(root))
        try:
            out[rel] = p.read_text(encoding="utf-8")
        except Exception:
            out[rel] = "<binary>"
    return out
