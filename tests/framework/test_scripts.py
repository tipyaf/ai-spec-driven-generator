"""
Script validation tests — every enforcement script must parse, have a main(),
accept expected CLI args, and use consistent config keys.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from conftest import FRAMEWORK_ROOT, read_text

SCRIPTS_DIR = FRAMEWORK_ROOT / "scripts"

ALL_CHECK_SCRIPTS = [
    "check_red_phase.py",
    "check_test_intentions.py",
    "check_coverage_audit.py",
    "check_msw_contracts.py",
    "check_test_tampering.py",
    "check_tdd_order.py",
    "check_test_quality.py",
    "check_write_coverage.py",
    "check_oracle_assertions.py",
    "check_story_commits.py",
]


class TestScriptSyntax:
    """All enforcement scripts must be valid Python."""

    @pytest.mark.parametrize("script_name", ALL_CHECK_SCRIPTS)
    def test_script_parses(self, script_name: str):
        path = SCRIPTS_DIR / script_name
        assert path.exists(), f"Script {script_name} not found"
        source = read_text(path)
        try:
            ast.parse(source, filename=script_name)
        except SyntaxError as e:
            pytest.fail(f"{script_name} has syntax error: {e}")

    @pytest.mark.parametrize("script_name", ALL_CHECK_SCRIPTS)
    def test_script_has_main(self, script_name: str):
        """Every script must define a main() function."""
        path = SCRIPTS_DIR / script_name
        source = read_text(path)
        tree = ast.parse(source)
        func_names = [
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        ]
        assert "main" in func_names, f"{script_name} missing main() function"

    @pytest.mark.parametrize("script_name", ALL_CHECK_SCRIPTS)
    def test_script_has_ifmain(self, script_name: str):
        """Every script must have if __name__ == '__main__' guard."""
        source = read_text(SCRIPTS_DIR / script_name)
        assert '__name__' in source and '__main__' in source, (
            f"{script_name} missing if __name__ == '__main__' guard"
        )


class TestScriptCLIArgs:
    """Scripts that accept --story must use argparse consistently."""

    STORY_SCRIPTS = [
        "check_red_phase.py",
        "check_test_intentions.py",
        "check_test_tampering.py",
        "check_tdd_order.py",
        "check_msw_contracts.py",
    ]

    @pytest.mark.parametrize("script_name", STORY_SCRIPTS)
    def test_story_scripts_accept_story_arg(self, script_name: str):
        source = read_text(SCRIPTS_DIR / script_name)
        assert "--story" in source, f"{script_name} should accept --story argument"

    def test_check_test_intentions_accepts_spec_path(self):
        source = read_text(SCRIPTS_DIR / "check_test_intentions.py")
        assert "--spec-path" in source, (
            "check_test_intentions.py must accept --spec-path for direct story file override"
        )

    def test_check_test_intentions_accepts_require_ui_intentions(self):
        source = read_text(SCRIPTS_DIR / "check_test_intentions.py")
        assert "--require-ui-intentions" in source, (
            "check_test_intentions.py must accept --require-ui-intentions for Trigger C"
        )


class TestScriptConfigKeys:
    """Config keys used by scripts must be documented in the example config."""

    @pytest.fixture
    def example_config(self) -> dict:
        import json
        config_path = SCRIPTS_DIR / "test_enforcement.json.example"
        assert config_path.exists(), "test_enforcement.json.example not found"
        return json.loads(read_text(config_path))

    def test_example_config_is_valid_json(self):
        import json
        config_path = SCRIPTS_DIR / "test_enforcement.json.example"
        content = read_text(config_path)
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"test_enforcement.json.example is invalid JSON: {e}")

    def test_example_config_has_oracle_check_section(self, example_config: dict):
        """oracle_check section must be documented (used by check_oracle_assertions.py)."""
        assert "oracle_check" in example_config, (
            "test_enforcement.json.example missing oracle_check section"
        )

    def test_oracle_check_has_required_keys(self, example_config: dict):
        oracle = example_config.get("oracle_check", {})
        required = ["enabled", "write_path_keywords", "known_files_without_oracle"]
        missing = [k for k in required if k not in oracle]
        assert not missing, f"oracle_check missing keys: {missing}"


class TestNoDeadCode:
    """Scripts should not have functions that are defined but never called."""

    @pytest.mark.parametrize("script_name", ALL_CHECK_SCRIPTS)
    def test_no_obvious_dead_functions(self, script_name: str):
        """Check that defined functions are referenced somewhere in the script."""
        source = read_text(SCRIPTS_DIR / script_name)
        tree = ast.parse(source)

        # Collect all function definitions (skip main and helpers starting with _)
        func_defs: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name not in ("main",) and not node.name.startswith("_"):
                    func_defs.append(node.name)

        dead: list[str] = []
        for func_name in func_defs:
            # Count occurrences: should appear at least twice (def + call)
            count = len(re.findall(rf"\b{re.escape(func_name)}\b", source))
            if count < 2:
                dead.append(func_name)

        assert not dead, (
            f"{script_name} has functions defined but never called: {dead}"
        )
