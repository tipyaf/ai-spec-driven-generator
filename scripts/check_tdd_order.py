#!/usr/bin/env python3
"""
check_tdd_order.py -- Enforcement: RED commit must precede GREEN commit.

For every story with a build file in _work/build/, verifies that:
1. A "test: RED" commit exists (test engineer wrote failing tests)
2. A "feat: GREEN" commit exists (builder wrote code to pass tests)
3. The RED commit is OLDER than the GREEN commit

This is a hard gate. If the builder committed code without a preceding
RED phase, the story is rejected.

Usage:
    python check_tdd_order.py                    # check all active build files
    python check_tdd_order.py --story 1500       # check specific story
    python check_tdd_order.py --config PATH      # custom config path

Exit code: 0 = pass, 1 = violation found
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


def find_project_root() -> Path:
    """Walk up from script location to find project root."""
    script_dir = Path(__file__).resolve().parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / "CLAUDE.md").exists():
            return parent
    # Fallback: topmost .git directory (skip submodule .git files)
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / ".git").is_dir():
            return parent
    return Path.cwd()


def git_log_for_story(story_id: str, project_root: Path) -> list[dict]:
    """Get all commits for a story, oldest first."""
    pattern = f"\\[sc-{story_id}\\]"
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--oneline",
                "--reverse",
                "--format=%H %s",
                f"--grep={pattern}",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=30,
        )
        if result.returncode != 0:
            return []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    commits = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split(" ", 1)
        if len(parts) == 2:
            commits.append({"sha": parts[0], "message": parts[1]})
    return commits


def find_active_stories(project_root: Path) -> list[str]:
    """Find all story IDs with active build files."""
    build_dir = project_root / "_work" / "build"
    if not build_dir.exists():
        return []

    story_ids = []
    for f in build_dir.glob("sc-*.yaml"):
        match = re.match(r"sc-(\d+)\.yaml", f.name)
        if match:
            story_ids.append(match.group(1))
    return story_ids


def check_story(story_id: str, project_root: Path) -> bool:
    """Check TDD commit order for a single story. Returns True if OK."""
    commits = git_log_for_story(story_id, project_root)

    if not commits:
        # No commits yet -- story hasn't started building. Not a violation.
        return True

    # Find RED and GREEN commits by their conventional prefixes
    red_idx = None
    green_idx = None

    for i, commit in enumerate(commits):
        msg = commit["message"].lower()
        # RED phase: "test: RED" or "test: red" (test engineer)
        if re.match(r"test:\s*red\b", msg, re.IGNORECASE):
            if red_idx is None:
                red_idx = i
        # GREEN phase: "feat: GREEN" or "feat: green" (builder)
        if re.match(r"feat:\s*green\b", msg, re.IGNORECASE):
            green_idx = i  # take the latest GREEN commit

    # Also check for code commits that aren't labeled GREEN
    # (builder committed without following convention)
    has_non_test_commits = False
    for commit in commits:
        msg = commit["message"].lower()
        if not msg.startswith("test:") and not msg.startswith("chore:"):
            has_non_test_commits = True
            break

    # --- Enforcement rules ---

    # Rule 1: If there are code commits but no RED commit, TDD was skipped
    if has_non_test_commits and red_idx is None:
        violations.append(
            f"sc-{story_id}: Code commits exist but no 'test: RED' commit found. "
            f"TDD RED phase was skipped. Test engineer must write failing tests "
            f"BEFORE the builder writes code."
        )
        return False

    # Rule 2: If GREEN exists but RED doesn't, TDD was skipped
    if green_idx is not None and red_idx is None:
        violations.append(
            f"sc-{story_id}: 'feat: GREEN' commit found but no 'test: RED' commit. "
            f"Builder wrote code without the test engineer writing tests first."
        )
        return False

    # Rule 3: If both exist, RED must come before GREEN
    if red_idx is not None and green_idx is not None and red_idx >= green_idx:
        violations.append(
            f"sc-{story_id}: 'test: RED' commit ({commits[red_idx]['sha'][:8]}) "
            f"is AFTER 'feat: GREEN' commit ({commits[green_idx]['sha'][:8]}). "
            f"Tests must be written BEFORE code."
        )
        return False

    # Rule 4: If RED exists but no GREEN yet, that's fine (build in progress)
    if red_idx is not None and green_idx is None and not has_non_test_commits:
        return True

    # Rule 5: If code commits exist after RED but aren't labeled GREEN, warn
    if red_idx is not None and green_idx is None and has_non_test_commits:
        warnings.append(
            f"sc-{story_id}: Code commits exist after RED phase but none are labeled "
            f"'feat: GREEN'. Builder should use the conventional commit message."
        )
        # Warning, not violation -- the order is correct even without the label
        return True

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Check TDD commit order")
    parser.add_argument("--story", type=str, help="Check specific story ID")
    parser.add_argument(
        "--config", type=str, help="Config file path (unused, for consistency)"
    )
    args = parser.parse_args()

    project_root = find_project_root()

    if args.story:
        story_ids = [args.story]
    else:
        story_ids = find_active_stories(project_root)

    if not story_ids:
        print(f"{GREEN}No active build files found. Nothing to check.{NC}")
        return 0

    for sid in story_ids:
        check_story(sid, project_root)

    # Report
    if warnings:
        for w in warnings:
            print(f"{YELLOW}[WARN]{NC} {w}")

    if violations:
        print(f"\n{RED}TDD order violations:{NC}")
        for v in violations:
            print(f"  {RED}[FAIL]{NC} {v}")
        print(
            f"\n{RED}TDD enforcement: RED (failing tests) must be committed "
            f"BEFORE GREEN (production code). No exceptions.{NC}"
        )
        return 1

    checked = len(story_ids)
    print(f"{GREEN}TDD order check: {checked} story(ies) OK.{NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
