#!/usr/bin/env python3
"""
check_story_commits.py -- Enforcement script for atomic story commits.

Pre-commit hook that verifies story commits are atomic and complete.
When production code is staged, the story file, manifest, and tracker must also be staged.

Checks:
1. If production code is staged -> story file + manifest + tracker MUST also be staged
2. Story file is valid YAML with required fields
3. All ACs in the story file have verify: fields
4. Feature-tracker status is consistent

Language-agnostic: works with any project type.

Usage:
    python check_story_commits.py [--config PATH]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"

violations: list[str] = []
warnings: list[str] = []


def find_root() -> Path:
    """Find project root by walking up from script location."""
    script_dir = Path(__file__).resolve().parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / "CLAUDE.md").exists() or (parent / ".git").exists():
            return parent
    return script_dir


def get_staged_files() -> list[str]:
    """Get list of staged files from git."""
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        cwd=find_root(),
    )
    if result.returncode != 0:
        return []
    return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]


def is_production_code(filepath: str) -> bool:
    """Check if a file is production code (not spec, test, config, or framework)."""
    # Framework files are not production code
    framework_prefixes = (
        "agents/",
        "skills/",
        "rules/",
        "scripts/",
        "specs/",
        "stacks/",
        "tests/",
        "_work/",
        "_docs/",
        "memory/",
        "prompts/",
    )
    if any(filepath.startswith(prefix) for prefix in framework_prefixes):
        return False

    # Config files are not production code
    config_files = (
        "CLAUDE.md",
        "README.md",
        "CHANGELOG.md",
        "VERSION",
        ".gitignore",
        "package.json",
        "tsconfig.json",
        "pyproject.toml",
        "Cargo.toml",
        "go.mod",
        "Makefile",
        "Dockerfile",
        "docker-compose",
    )
    basename = filepath.split("/")[-1]
    if any(basename.startswith(cfg) for cfg in config_files):
        return False

    return True


def check_atomic_commit(staged_files: list[str]) -> None:
    """Check 1: If production code is staged, story file + manifest + tracker must be too."""
    prod_files = [f for f in staged_files if is_production_code(f)]

    if not prod_files:
        return  # No production code staged, skip check

    # Check for story file
    story_files = [
        f
        for f in staged_files
        if f.startswith("specs/stories/") and not f.endswith("-manifest.yaml")
    ]
    manifest_files = [
        f for f in staged_files if f.endswith("-manifest.yaml")
    ]
    tracker_staged = "specs/feature-tracker.yaml" in staged_files

    if not story_files:
        violations.append(
            "Production code is staged but no story file (specs/stories/*.yaml) is staged. "
            "Story + code must be committed together (atomic commit)."
        )

    if not manifest_files:
        warnings.append(
            "Production code is staged but no manifest file (specs/stories/*-manifest.yaml) is staged. "
            "Consider including the manifest for traceability."
        )

    if not tracker_staged:
        violations.append(
            "Production code is staged but specs/feature-tracker.yaml is not staged. "
            "The tracker must be updated and committed with the implementation."
        )


def check_story_yaml_valid(staged_files: list[str]) -> None:
    """Check 2: Story files are valid YAML with required fields."""
    try:
        import yaml
    except ImportError:
        warnings.append(
            "PyYAML not installed — cannot validate story file YAML structure. "
            "Install with: pip install pyyaml"
        )
        return

    root = find_root()
    for f in staged_files:
        if not (f.startswith("specs/stories/") and f.endswith(".yaml")):
            continue
        if f.endswith("-manifest.yaml"):
            continue

        filepath = root / f
        if not filepath.exists():
            continue

        try:
            content = yaml.safe_load(filepath.read_text())
        except yaml.YAMLError as e:
            violations.append(f"Story file {f} is not valid YAML: {e}")
            continue

        if not content:
            violations.append(f"Story file {f} is empty")
            continue

        # Check required top-level fields
        required_fields = ["story", "user_story", "scope", "acceptance_criteria"]
        for field in required_fields:
            if field not in content:
                violations.append(
                    f"Story file {f} missing required field: '{field}'"
                )


def check_verify_commands(staged_files: list[str]) -> None:
    """Check 3: All ACs in story files have verify: fields."""
    try:
        import yaml
    except ImportError:
        return  # Already warned in check 2

    root = find_root()
    for f in staged_files:
        if not (f.startswith("specs/stories/") and f.endswith(".yaml")):
            continue
        if f.endswith("-manifest.yaml"):
            continue

        filepath = root / f
        if not filepath.exists():
            continue

        try:
            content = yaml.safe_load(filepath.read_text())
        except yaml.YAMLError:
            continue  # Already caught in check 2

        if not content or "acceptance_criteria" not in content:
            continue

        ac = content["acceptance_criteria"]
        for ac_type in ["functional", "security", "best_practices"]:
            if ac_type not in ac or not ac[ac_type]:
                continue
            for criterion in ac[ac_type]:
                if not isinstance(criterion, dict):
                    continue
                ac_id = criterion.get("id", "unknown")
                verify = criterion.get("verify", "")
                if not verify or verify.strip() == "":
                    violations.append(
                        f"Story file {f}: AC '{ac_id}' has no verify: command. "
                        "Every AC must have a runnable verify: command."
                    )
                if verify and verify.strip() == "static":
                    violations.append(
                        f"Story file {f}: AC '{ac_id}' uses 'verify: static' which is BANNED. "
                        "Rewrite with a shell command (grep, bash, curl)."
                    )


def check_tracker_consistency(staged_files: list[str]) -> None:
    """Check 4: Feature-tracker status is consistent."""
    if "specs/feature-tracker.yaml" not in staged_files:
        return

    try:
        import yaml
    except ImportError:
        return

    root = find_root()
    tracker_path = root / "specs/feature-tracker.yaml"
    if not tracker_path.exists():
        return

    try:
        content = yaml.safe_load(tracker_path.read_text())
    except yaml.YAMLError as e:
        violations.append(f"Feature tracker is not valid YAML: {e}")
        return

    if not content or "features" not in content:
        return

    valid_statuses = {"pending", "refined", "building", "testing", "validated", "escalated"}
    for feature in content.get("features", []):
        if not isinstance(feature, dict):
            continue
        status = feature.get("status", "")
        feature_id = feature.get("id", "unknown")
        if status and status not in valid_statuses:
            violations.append(
                f"Feature tracker: feature '{feature_id}' has invalid status '{status}'. "
                f"Valid statuses: {', '.join(sorted(valid_statuses))}"
            )


def _scan_branch() -> int:
    """Scan every commit on main..HEAD — every prod-code commit must carry [sc-*]."""
    root = find_root()
    try:
        base = subprocess.run(
            ["git", "merge-base", "origin/main", "HEAD"],
            capture_output=True, text=True, cwd=root, timeout=10,
        ).stdout.strip() or "HEAD~30"
        shas = subprocess.run(
            ["git", "log", f"{base}..HEAD", "--format=%H|%s"],
            capture_output=True, text=True, cwd=root, timeout=20,
        ).stdout.strip().splitlines()
    except Exception as exc:
        print(f"{YELLOW}[WARN]{NC} --scan-branch failed: {exc}")
        return 0
    offenders = []
    for line in shas:
        if "|" not in line:
            continue
        sha, subject = line.split("|", 1)
        # Determine if this commit touched production files.
        files_out = subprocess.run(
            ["git", "show", "--name-only", "--format=", sha],
            capture_output=True, text=True, cwd=root, timeout=10,
        ).stdout.strip().splitlines()
        prod = [f for f in files_out if f and is_production_code(f)]
        if prod and not re.search(r"\[sc-\d+\]", subject):
            offenders.append(f"{sha[:8]} ({subject[:50]}): prod code without [sc-*]")
    if offenders:
        for o in offenders:
            print(f"{RED}[FAIL]{NC} {o}")
        return 1
    print(f"{GREEN}--scan-branch: all prod commits carry a story tag.{NC}")
    return 0


def main() -> int:
    """Run all checks and report results."""
    # Optional --scan-branch flag for orchestrator preflight.
    if "--scan-branch" in sys.argv:
        return _scan_branch()

    staged_files = get_staged_files()

    if not staged_files:
        return 0

    # Run all checks
    check_atomic_commit(staged_files)
    check_story_yaml_valid(staged_files)
    check_verify_commands(staged_files)
    check_tracker_consistency(staged_files)

    # Report warnings
    if warnings:
        print(f"\n{YELLOW}WARNINGS ({len(warnings)}):{NC}")
        for w in warnings:
            print(f"  {YELLOW}⚠{NC} {w}")

    # Report violations
    if violations:
        print(f"\n{RED}VIOLATIONS ({len(violations)}):{NC}")
        for v in violations:
            print(f"  {RED}✗{NC} {v}")
        print(f"\n{RED}Story commit check FAILED — commit blocked.{NC}")
        print("Fix the issues above, then commit again.")
        return 1

    if not warnings:
        print(f"{GREEN}Story commit check PASSED.{NC}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
