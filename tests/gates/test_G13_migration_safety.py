"""Gate G13 — Migration safety (seed + migrate up + verify + migrate down).

The script executes three user-supplied commands (`--up`, `--verify`,
`--down`) and hashes the seed directory before+after to check that an
up/down round-trip preserves state. We use the `--seed-dir` CLI override
so the test seed lives in tmp_path instead of the framework repo.

The script's `find_root()` walks from its own `__file__` — commands run
in that cwd — so we keep the shell commands absolute-path aware.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_migration_safety.py"


def _make_seed(tmp_path: Path, content: str = "initial\n") -> Path:
    seed = tmp_path / "seed"
    seed.mkdir()
    (seed / "canary.txt").write_text(content)
    return seed


def _run(seed: Path, up: str, verify: str, down: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT),
         "--story", "sc-0001",
         "--seed-dir", str(seed),
         "--up", up, "--verify", verify, "--down", down],
        capture_output=True, text=True, timeout=30,
    )


def test_reversible_migration_passes(tmp_path):
    seed = _make_seed(tmp_path)
    marker = seed / "__migrated"
    result = _run(
        seed,
        up=f"touch '{marker}'",
        verify=f"test -f '{marker}'",
        down=f"rm -f '{marker}'",
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"


def test_irreversible_migration_fails(tmp_path):
    """up mutates seed, down doesn't restore — post-hash differs."""
    seed = _make_seed(tmp_path, "before\n")
    canary = seed / "canary.txt"
    result = _run(
        seed,
        up=f"printf 'after\\n' > '{canary}'",
        verify=f"grep -q after '{canary}'",
        down="true",  # no-op rollback → hash mismatch
    )
    assert result.returncode == 1
    combined = (result.stdout + result.stderr).lower()
    assert "seed" in combined or "differs" in combined


def test_verify_step_failure_fails_gate(tmp_path):
    seed = _make_seed(tmp_path)
    result = _run(seed, up="true", verify="false", down="true")
    assert result.returncode == 1
    assert "verify" in (result.stdout + result.stderr).lower()


def test_up_step_failure_fails_gate(tmp_path):
    seed = _make_seed(tmp_path)
    result = _run(seed, up="exit 2", verify="true", down="true")
    assert result.returncode == 1
    assert "up" in (result.stdout + result.stderr).lower()


def test_no_seed_dir_is_skipped(tmp_path):
    """Missing seed directory → gate is a no-op (graceful)."""
    result = _run(tmp_path / "nonexistent", "true", "true", "true")
    assert result.returncode == 0


def test_roundtrip_preserves_nested_content(tmp_path):
    """Sanity: hashing covers nested files too."""
    seed = _make_seed(tmp_path)
    nested = seed / "sub"
    nested.mkdir()
    (nested / "row.sql").write_text("INSERT INTO t VALUES (1);")
    result = _run(seed, "true", "true", "true")
    assert result.returncode == 0
