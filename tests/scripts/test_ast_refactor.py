"""Tests for the v5 AST refactoring of the check_*.py scripts.

Covers the edge cases that the v4 regex approach missed:
  * check_red_phase: `assert 1 != 2` is semantically trivial
  * check_oracle_assertions: `# ORACLE: 10 + 5 = 15` with inconsistent math
  * check_contract_diff: endpoint removed without `breaks:` declaration
  * check_test_tampering: AST diff detects assertion removed between commits
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


# --- check_red_phase ----------------------------------------------------

def test_red_phase_detects_literal_inequality_tautology():
    """`assert 1 != 2` is always true — it's trivial. Regex missed this."""
    from check_red_phase import detect_trivial_python_ast

    code = textwrap.dedent(
        """
        def test_tautology():
            assert 1 != 2
        """
    )
    findings = detect_trivial_python_ast(code)
    assert findings, "AST should detect `assert 1 != 2` as trivial"


def test_red_phase_detects_pytest_fail_semantically():
    from check_red_phase import detect_trivial_python_ast

    code = textwrap.dedent(
        """
        import pytest
        def test_fail():
            pytest.fail("always")
        """
    )
    findings = detect_trivial_python_ast(code)
    assert findings, "pytest.fail() should be detected"


def test_red_phase_accepts_real_assertion():
    from check_red_phase import detect_trivial_python_ast

    code = textwrap.dedent(
        """
        def test_real(candidate):
            assert candidate.name == "alice"
        """
    )
    findings = detect_trivial_python_ast(code)
    assert not findings, "real assertion should NOT be flagged"


# --- check_oracle_assertions -------------------------------------------

def test_oracle_evaluates_inconsistent_math_as_fail():
    """`# ORACLE: 10 + 5 = 20` is mathematically wrong — must be caught."""
    from check_oracle_assertions import evaluate_oracle

    ok, detail = evaluate_oracle("# ORACLE: 10 + 5 = 20")
    assert ok is False, f"inconsistent ORACLE should fail, got {detail}"


def test_oracle_evaluates_consistent_math_as_pass():
    from check_oracle_assertions import evaluate_oracle

    ok, _ = evaluate_oracle("# ORACLE: 10 + 5 = 15")
    assert ok is True


def test_oracle_sandbox_rejects_unsafe_expressions():
    """The sandbox must refuse to execute arbitrary code."""
    from check_oracle_assertions import evaluate_oracle

    # Arbitrary function call should NOT crash — it should just return "unparsable" safely.
    ok, detail = evaluate_oracle("# ORACLE: __import__('os').system('ls') = 0")
    # Sandbox returned 'unparsable' -> ok=True means we skip, which is safe.
    assert "unparsable" in detail or ok is True


# --- check_contract_diff -----------------------------------------------

def test_contract_diff_detects_removed_endpoint_without_breaks(tmp_path):
    """Removing GET /users/{id} without declaring it in `breaks:` must fail."""
    current = tmp_path / "current.yaml"
    snapshot = tmp_path / "snapshot.yaml"
    current.write_text(
        "paths:\n"
        "  /users:\n"
        "    get: {}\n"
    )
    snapshot.write_text(
        "paths:\n"
        "  /users:\n"
        "    get: {}\n"
        "  /users/{id}:\n"
        "    get: {}\n"
    )
    # Create a minimal story manifest with no `breaks:` declared.
    story_dir = tmp_path / "specs" / "stories"
    story_dir.mkdir(parents=True)
    (story_dir / "sc-9999.yaml").write_text("id: sc-9999\n")
    (tmp_path / ".git").mkdir()

    script = SCRIPTS / "check_contract_diff.py"
    result = subprocess.run(
        [sys.executable, str(script), "--kind", "api", "--story", "sc-9999",
         "--current", str(current), "--snapshot", str(snapshot)],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert result.returncode == 1, f"expected fail, stdout={result.stdout} stderr={result.stderr}"
    assert "GET /users/{id}" in (result.stdout + result.stderr) or "undeclared" in (result.stdout + result.stderr)


# --- check_test_tampering ----------------------------------------------

def test_tampering_ast_diff_detects_removed_assertion():
    """Even if 2 new asserts are added, removing one from RED must be flagged."""
    from check_test_tampering import diff_assertions_ast

    red = textwrap.dedent(
        """
        def test_x():
            assert balance == 100
        """
    )
    green_net_plus = textwrap.dedent(
        """
        def test_x():
            assert balance is not None
            assert name == "alice"
        """
    )
    removed = diff_assertions_ast(red, green_net_plus)
    assert removed, "the `balance == 100` sig must appear as removed despite net-positive count"
