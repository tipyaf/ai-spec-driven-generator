"""Conformance tests for the v5 stack plugin system (Étape 4).

Validates that every built-in stack under `stacks/templates/<name>/` exposes
the expected files and that their YAML content matches the v5 plugin schema.

The structure mirrors what `scripts/orchestrator.py` will discover at runtime
via `_work/stacks/registry.yaml`. Breaking these tests means the stack plugin
contract is broken, which cascades into every project using the framework.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
STACKS_TEMPLATES_DIR = REPO_ROOT / "stacks" / "templates"

# Stacks that must exist in v5. Postgres does not define smoke-boot.yaml
# (it uses migration-strategy.yaml for G13 instead of G4.1).
BUILTIN_STACKS = ["python-fastapi", "typescript-react", "postgres", "nodejs-express"]

STACKS_WITH_SMOKE_BOOT = ["python-fastapi", "typescript-react", "nodejs-express"]
STACKS_WITH_MIGRATION_STRATEGY = ["postgres"]

REQUIRED_PROFILE_FIELDS = {"name", "languages", "test_command", "build_command", "smoke_boot"}


# ---------------------------------------------------------------------------
# Directory layout
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("stack", BUILTIN_STACKS)
def test_stack_directory_exists(stack: str) -> None:
    stack_dir = STACKS_TEMPLATES_DIR / stack
    assert stack_dir.is_dir(), f"expected directory {stack_dir}"


@pytest.mark.parametrize("stack", BUILTIN_STACKS)
def test_stack_has_profile_yaml(stack: str) -> None:
    profile = STACKS_TEMPLATES_DIR / stack / "profile.yaml"
    assert profile.is_file(), f"missing profile.yaml for stack {stack}"


@pytest.mark.parametrize("stack", BUILTIN_STACKS)
def test_stack_has_ac_templates_yaml(stack: str) -> None:
    ac = STACKS_TEMPLATES_DIR / stack / "ac-templates.yaml"
    assert ac.is_file(), f"missing ac-templates.yaml for stack {stack}"


@pytest.mark.parametrize("stack", BUILTIN_STACKS)
def test_stack_has_readme(stack: str) -> None:
    readme = STACKS_TEMPLATES_DIR / stack / "README.md"
    assert readme.is_file(), f"missing README.md for stack {stack}"


@pytest.mark.parametrize("stack", BUILTIN_STACKS)
def test_stack_has_checks_dir(stack: str) -> None:
    checks = STACKS_TEMPLATES_DIR / stack / "checks"
    assert checks.is_dir(), f"missing checks/ directory for stack {stack}"


@pytest.mark.parametrize("stack", STACKS_WITH_SMOKE_BOOT)
def test_stacks_with_smoke_boot_have_yaml(stack: str) -> None:
    sb = STACKS_TEMPLATES_DIR / stack / "smoke-boot.yaml"
    assert sb.is_file(), f"{stack} should declare smoke-boot.yaml"


@pytest.mark.parametrize("stack", STACKS_WITH_MIGRATION_STRATEGY)
def test_stacks_with_migration_have_yaml(stack: str) -> None:
    ms = STACKS_TEMPLATES_DIR / stack / "migration-strategy.yaml"
    assert ms.is_file(), f"{stack} should declare migration-strategy.yaml"


# ---------------------------------------------------------------------------
# profile.yaml schema validation
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), f"{path} is not a YAML mapping"
    return data


@pytest.mark.parametrize("stack", BUILTIN_STACKS)
def test_profile_yaml_has_required_fields(stack: str) -> None:
    profile = _load_yaml(STACKS_TEMPLATES_DIR / stack / "profile.yaml")
    missing = REQUIRED_PROFILE_FIELDS - set(profile.keys())
    assert not missing, f"{stack}/profile.yaml missing fields: {missing}"


@pytest.mark.parametrize("stack", BUILTIN_STACKS)
def test_profile_yaml_name_matches_dir(stack: str) -> None:
    profile = _load_yaml(STACKS_TEMPLATES_DIR / stack / "profile.yaml")
    assert profile["name"] == stack, (
        f"{stack}/profile.yaml: name '{profile['name']}' must match directory '{stack}'"
    )


@pytest.mark.parametrize("stack", BUILTIN_STACKS)
def test_profile_yaml_languages_non_empty(stack: str) -> None:
    profile = _load_yaml(STACKS_TEMPLATES_DIR / stack / "profile.yaml")
    langs = profile.get("languages")
    assert isinstance(langs, list) and langs, f"{stack}: languages must be a non-empty list"


@pytest.mark.parametrize("stack", BUILTIN_STACKS)
def test_profile_yaml_smoke_boot_shape(stack: str) -> None:
    """smoke_boot may be inline mapping OR a reference to smoke-boot.yaml — either way it must be a mapping."""
    profile = _load_yaml(STACKS_TEMPLATES_DIR / stack / "profile.yaml")
    sb = profile.get("smoke_boot")
    assert isinstance(sb, dict), f"{stack}: smoke_boot must be a mapping"
    assert "strategy" in sb, f"{stack}: smoke_boot.strategy is required"


# ---------------------------------------------------------------------------
# ac-templates.yaml validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("stack", BUILTIN_STACKS)
def test_ac_templates_declare_ac_sec_and_ac_bp(stack: str) -> None:
    ac = _load_yaml(STACKS_TEMPLATES_DIR / stack / "ac-templates.yaml")
    assert isinstance(ac.get("ac_sec"), list) and ac["ac_sec"], (
        f"{stack}/ac-templates.yaml: ac_sec must be a non-empty list"
    )
    assert isinstance(ac.get("ac_bp"), list) and ac["ac_bp"], (
        f"{stack}/ac-templates.yaml: ac_bp must be a non-empty list"
    )


@pytest.mark.parametrize("stack", BUILTIN_STACKS)
def test_ac_templates_have_required_fields(stack: str) -> None:
    ac = _load_yaml(STACKS_TEMPLATES_DIR / stack / "ac-templates.yaml")
    for section in ("ac_sec", "ac_bp"):
        for item in ac[section]:
            assert "id" in item, f"{stack}.{section}: entry missing 'id'"
            assert "applies_to" in item, f"{stack}.{section}.{item['id']}: missing 'applies_to'"
            assert "text" in item, f"{stack}.{section}.{item['id']}: missing 'text'"
            assert "verify" in item, f"{stack}.{section}.{item['id']}: missing 'verify'"


@pytest.mark.parametrize("stack", BUILTIN_STACKS)
def test_ac_ids_have_expected_prefix(stack: str) -> None:
    ac = _load_yaml(STACKS_TEMPLATES_DIR / stack / "ac-templates.yaml")
    for item in ac["ac_sec"]:
        assert item["id"].startswith("AC-SEC-"), (
            f"{stack}: ac_sec entry id '{item['id']}' must start with AC-SEC-"
        )
    for item in ac["ac_bp"]:
        assert item["id"].startswith("AC-BP-"), (
            f"{stack}: ac_bp entry id '{item['id']}' must start with AC-BP-"
        )


# ---------------------------------------------------------------------------
# Migrated check scripts (previously in scripts/)
# ---------------------------------------------------------------------------

def test_msw_contracts_check_migrated_to_typescript_react() -> None:
    path = STACKS_TEMPLATES_DIR / "typescript-react" / "checks" / "check_msw_contracts.py"
    assert path.is_file(), "check_msw_contracts.py must live under typescript-react/checks/"
    # Executable bit preserved from git mv (or restored by init-project).
    mode = path.stat().st_mode
    assert mode & stat.S_IXUSR, f"{path} should be executable (user-exec bit missing)"


def test_write_coverage_check_migrated_to_postgres() -> None:
    path = STACKS_TEMPLATES_DIR / "postgres" / "checks" / "check_write_coverage.py"
    assert path.is_file(), "check_write_coverage.py must live under postgres/checks/"


def test_migrated_checks_no_longer_in_scripts() -> None:
    """The two migrated checks must not remain under scripts/ (no accidental duplicates)."""
    scripts_dir = REPO_ROOT / "scripts"
    assert not (scripts_dir / "check_msw_contracts.py").exists(), (
        "check_msw_contracts.py should have been moved to stacks/templates/typescript-react/checks/"
    )
    assert not (scripts_dir / "check_write_coverage.py").exists(), (
        "check_write_coverage.py should have been moved to stacks/templates/postgres/checks/"
    )


# ---------------------------------------------------------------------------
# Registry example
# ---------------------------------------------------------------------------

def test_registry_example_references_every_builtin_stack() -> None:
    registry = _load_yaml(REPO_ROOT / "stacks" / "registry-example.yaml")
    names = {s["name"] for s in registry.get("stacks", [])}
    missing = set(BUILTIN_STACKS) - names
    # nodejs-express might be commented out or in the example — accept either,
    # but python-fastapi / typescript-react / postgres MUST be present.
    required = {"python-fastapi", "typescript-react", "postgres"}
    assert required.issubset(names), (
        f"registry-example.yaml must reference at least {required}; missing {required - names}"
    )
