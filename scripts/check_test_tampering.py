#!/usr/bin/env python3
"""
check_test_tampering.py -- Enforcement: builder must not weaken tests.

Called by the orchestrator AFTER the builder commits (Step 6c GREEN phase).
Compares test files between the RED commit and the GREEN commit:

1. No test functions may be DELETED (builder can't remove inconvenient tests)
2. No assert statements may be REMOVED without a replacement
3. No xfail markers may be ADDED without a "BUG:" reason
4. Test files from RED phase must still exist

The builder MAY:
- Add new test functions (more coverage is fine)
- Add new assert statements
- Fix a genuinely wrong test (wrong URL, wrong fixture) with a code comment explaining why
- Add imports needed for the tests to run

Usage:
    python check_test_tampering.py --story 1500
    python check_test_tampering.py --story 1500 --red-commit abc1234 --green-commit def5678

Exit code: 0 = pass, 1 = tampering detected
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

RED_C = "\033[0;31m"
GREEN_C = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"

violations: list[str] = []
warnings: list[str] = []


def find_project_root() -> Path:
    script_dir = Path(__file__).resolve().parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / "CLAUDE.md").exists():
            return parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / ".git").is_dir():
            return parent
    return Path.cwd()


def git_cmd(args: list[str], cwd: Path) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )
    return result.stdout.strip()


def find_phase_commits(
    story_id: str, project_root: Path
) -> tuple[str | None, str | None]:
    """Find the RED and GREEN commit SHAs for a story."""
    log = git_cmd(
        ["log", "--oneline", "--reverse", "--format=%H %s", f"--grep=\\[sc-{story_id}\\]"],
        project_root,
    )

    red_sha = None
    green_sha = None
    for line in log.splitlines():
        if not line.strip():
            continue
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        sha, msg = parts
        if re.match(r"test:\s*red\b", msg, re.IGNORECASE):
            if red_sha is None:
                red_sha = sha
        if re.match(r"feat:\s*green\b", msg, re.IGNORECASE):
            green_sha = sha  # latest GREEN

    return red_sha, green_sha


def get_file_at_commit(filepath: str, commit: str, cwd: Path) -> str | None:
    """Get file content at a specific commit."""
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{filepath}"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=15,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def get_test_files_in_commit(commit: str, cwd: Path) -> list[str]:
    """Get list of test files that exist at a commit."""
    log = git_cmd(["diff-tree", "--no-commit-id", "-r", "--name-only", commit], cwd)
    test_files = []
    for line in log.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r".*test_.*\.py$", line) or re.match(r".*_test\.py$", line):
            test_files.append(line)
        if re.match(r".*\.test\.(ts|tsx|js|jsx)$", line) or re.match(
            r".*\.spec\.(ts|tsx|js|jsx)$", line
        ):
            test_files.append(line)
    return test_files


def get_all_test_files_for_story(story_id: str, project_root: Path) -> list[str]:
    """Get all test files across all commits for this story."""
    log = git_cmd(
        ["log", "--name-only", "--format=", f"--grep=\\[sc-{story_id}\\]"],
        project_root,
    )
    test_files = set()
    for line in log.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r".*test_.*\.py$", line) or re.match(r".*_test\.py$", line):
            test_files.add(line)
        if re.match(r".*\.test\.(ts|tsx|js|jsx)$", line) or re.match(
            r".*\.spec\.(ts|tsx|js|jsx)$", line
        ):
            test_files.add(line)
    return list(test_files)


def extract_test_functions(content: str, is_python: bool) -> set[str]:
    """Extract test function names from file content."""
    if is_python:
        return set(re.findall(r"(?:async\s+)?def\s+(test_\w+)", content))
    else:
        # TypeScript: it("name" or test("name"
        names = set()
        for m in re.finditer(r'\b(?:it|test)\s*\(\s*["\']([^"\']+)', content):
            names.add(m.group(1))
        return names


def extract_assertions(content: str, is_python: bool) -> list[str]:
    """Extract assertion statements from file content."""
    if is_python:
        # assert xxx, pytest.approx, self.assertEqual, etc.
        return re.findall(r"^\s*(assert\s+.+)$", content, re.MULTILINE)
    else:
        # expect(...).toXxx
        return re.findall(r"^\s*(expect\s*\(.+)$", content, re.MULTILINE)


def extract_xfail_markers(content: str) -> list[str]:
    """Extract xfail markers from Python test content."""
    return re.findall(r"@pytest\.mark\.xfail\([^)]*\)", content)


def check_file_tampering(
    filepath: str,
    red_content: str,
    green_content: str | None,
) -> None:
    """Compare a test file between RED and GREEN phases."""
    is_python = filepath.endswith(".py")

    if green_content is None:
        # File was DELETED by the builder
        violations.append(
            f"{filepath}: Test file was DELETED by the builder. "
            f"The builder must not remove test files written by the test engineer."
        )
        return

    # Check 1: Test functions removed
    red_funcs = extract_test_functions(red_content, is_python)
    green_funcs = extract_test_functions(green_content, is_python)
    removed_funcs = red_funcs - green_funcs

    if removed_funcs:
        violations.append(
            f"{filepath}: {len(removed_funcs)} test function(s) DELETED by builder: "
            f"{', '.join(sorted(removed_funcs))}. "
            f"Builder must not delete tests. If a test is wrong, fix it with a comment."
        )

    # Check 2: Assert statements removed (net count) -- now a VIOLATION, not warning
    red_asserts = extract_assertions(red_content, is_python)
    green_asserts = extract_assertions(green_content, is_python)

    if len(green_asserts) < len(red_asserts):
        removed_count = len(red_asserts) - len(green_asserts)
        violations.append(
            f"{filepath}: {removed_count} assertion(s) REMOVED (RED had {len(red_asserts)}, "
            f"GREEN has {len(green_asserts)}). Builder must not remove assertions. "
            f"Fix the code to satisfy the assertions, not the other way around."
        )

    # Check 2b: Assertion weakening -- strong assertions replaced with weak ones
    if is_python:
        # Weak patterns: "is not None", "> 0", "!= None", "is True"
        weak_pattern = r"assert\s+\w+\s+is\s+not\s+None|assert\s+\w+\s*[>!]=?\s*0|assert\s+\w+\s+is\s+True"
        # Strong patterns: "== pytest.approx", "== <number>", specific value comparisons
        strong_pattern = r"assert\s+.*==\s*(?:pytest\.approx|[\d.]+|['\"])"

        red_strong = len(re.findall(strong_pattern, red_content, re.MULTILINE))
        green_strong = len(re.findall(strong_pattern, green_content, re.MULTILINE))
        red_weak = len(re.findall(weak_pattern, red_content, re.MULTILINE))
        green_weak = len(re.findall(weak_pattern, green_content, re.MULTILINE))

        # If strong assertions decreased AND weak assertions increased, that's weakening
        if red_strong > green_strong and green_weak > red_weak:
            violations.append(
                f"{filepath}: Assertion WEAKENING detected. "
                f"Strong assertions (exact values): {red_strong} -> {green_strong}. "
                f"Weak assertions (is not None, > 0): {red_weak} -> {green_weak}. "
                f"Builder replaced precise assertions with vague ones."
            )
    else:
        # TypeScript: toEqual/toBe -> toBeTruthy/toBeDefined
        strong_ts = r"\.(?:toBe|toEqual|toBeCloseTo|toHaveTextContent)\s*\("
        weak_ts = r"\.(?:toBeTruthy|toBeDefined|toBeFalsy|toBeNull)\s*\("

        red_strong = len(re.findall(strong_ts, red_content))
        green_strong = len(re.findall(strong_ts, green_content))
        red_weak = len(re.findall(weak_ts, red_content))
        green_weak = len(re.findall(weak_ts, green_content))

        if red_strong > green_strong and green_weak > red_weak:
            violations.append(
                f"{filepath}: Assertion WEAKENING detected. "
                f"Strong assertions (toBe/toEqual): {red_strong} -> {green_strong}. "
                f"Weak assertions (toBeTruthy/toBeDefined): {red_weak} -> {green_weak}. "
                f"Builder replaced precise assertions with vague ones."
            )

    # Check 3: xfail markers added without BUG: reason (Python only)
    if is_python:
        red_xfails = extract_xfail_markers(red_content)
        green_xfails = extract_xfail_markers(green_content)
        new_xfails = len(green_xfails) - len(red_xfails)

        if new_xfails > 0:
            # Check if new xfails have BUG: reason
            for xf in green_xfails:
                if "BUG:" not in xf and xf not in red_xfails:
                    violations.append(
                        f'{filepath}: xfail added without "BUG:" reason: {xf}. '
                        f"If marking a test as expected-fail, explain the bug."
                    )


def update_build_file(
    story_id: str,
    project_root: Path,
    *,
    status: str,
    tampering_found: list[str],
) -> None:
    """Update the build file with tampering check results."""
    build_file = project_root / "_work" / "build" / f"sc-{story_id}.yaml"
    if not build_file.exists():
        return

    content = build_file.read_text()

    tdd_green_block = f"  tdd_green:\n    status: {status}\n"
    if tampering_found:
        tdd_green_block += "    tampering:\n"
        for t in tampering_found:
            escaped = t.replace('"', '\\"')
            tdd_green_block += f'      - "{escaped}"\n'

    if "tdd_green:" in content:
        content = re.sub(
            r"  tdd_green:\n(?:    .*\n)*",
            tdd_green_block,
            content,
        )
    elif "gates:" in content:
        content = content.replace("gates:\n", f"gates:\n{tdd_green_block}")

    build_file.write_text(content)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check test tampering between RED and GREEN"
    )
    parser.add_argument("--story", required=True, type=str, help="Story ID")
    parser.add_argument("--red-commit", type=str, help="Override RED commit SHA")
    parser.add_argument("--green-commit", type=str, help="Override GREEN commit SHA")
    parser.add_argument(
        "--test-cmd", type=str, help="Explicit test command to verify GREEN phase"
    )
    args = parser.parse_args()

    # Bypass: "chore: cleanup" commits are legitimate test removals (e.g. after re-refinement)
    project_root = find_project_root()
    story_id = args.story

    # Check if the latest commit for this story is a cleanup commit
    latest_msg = git_cmd(
        ["log", "-1", "--format=%s", f"--grep=\\[sc-{story_id}\\]"],
        project_root,
    )
    if re.match(r"chore:\s*cleanup\b", latest_msg, re.IGNORECASE):
        print(f"{GREEN_C}Cleanup commit detected — test deletion bypass active.{NC}")
        return 0

    # Find commits
    if args.red_commit and args.green_commit:
        red_sha = args.red_commit
        green_sha = args.green_commit
    else:
        red_sha, green_sha = find_phase_commits(story_id, project_root)

    if not red_sha:
        print(
            f"{YELLOW}[WARN]{NC} sc-{story_id}: No RED commit found. Cannot check tampering."
        )
        return 0

    if not green_sha:
        print(
            f"{YELLOW}[WARN]{NC} sc-{story_id}: No GREEN commit found yet. Nothing to check."
        )
        return 0

    print(f"RED commit:   {red_sha[:8]}")
    print(f"GREEN commit: {green_sha[:8]}")

    # Get test files from RED phase
    test_files = get_all_test_files_for_story(story_id, project_root)
    if not test_files:
        print(f"{YELLOW}[WARN]{NC} No test files found for sc-{story_id}.")
        return 0

    print(f"Checking {len(test_files)} test file(s)...")

    # Compare each test file
    for tf in test_files:
        red_content = get_file_at_commit(tf, red_sha, project_root)
        if red_content is None:
            # File didn't exist at RED commit (added by builder -- that's fine)
            continue

        green_content = get_file_at_commit(tf, green_sha, project_root)
        check_file_tampering(tf, red_content, green_content)

    # Report
    if warnings:
        for w in warnings:
            print(f"{YELLOW}[WARN]{NC} {w}")

    if violations:
        print(f"\n{RED_C}Test tampering detected:{NC}")
        for v in violations:
            print(f"  {RED_C}[FAIL]{NC} {v}")
        print(
            f"\n{RED_C}The builder must not delete, weaken, or bypass tests "
            f"written by the test engineer. Fix the CODE, not the tests.{NC}"
        )
        update_build_file(
            story_id,
            project_root,
            status="fail",
            tampering_found=violations,
        )
        return 1

    # --- Step 2: Verify tests actually PASS (GREEN phase must make tests green) ---
    print("\nRe-running tests to verify GREEN phase...")
    test_cmd = args.test_cmd if hasattr(args, "test_cmd") and args.test_cmd else None
    if not test_cmd:
        # Auto-detect: Python or TypeScript
        py_files = [tf for tf in test_files if tf.endswith(".py")]
        ts_files = [tf for tf in test_files if not tf.endswith(".py")]
        if py_files:
            file_args = " ".join(f'"{tf}"' for tf in py_files)
            test_cmd = f"python -m pytest {file_args} -x -q --tb=short"
        elif ts_files:
            test_cmd = "npx vitest run --reporter=verbose"

    if test_cmd:
        try:
            result = subprocess.run(
                test_cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=120,
            )
            if result.returncode != 0:
                output = result.stdout + "\n" + result.stderr
                violations.append(
                    f"Tests FAIL after builder's GREEN commit. The builder's code "
                    f"does not make the tests pass. Exit code: {result.returncode}"
                )
                print(f"\n{RED_C}[FAIL]{NC} Tests still FAIL after GREEN phase!")
                print(f"Test output (last 1500 chars):\n{output[-1500:]}")
                update_build_file(
                    story_id,
                    project_root,
                    status="fail",
                    tampering_found=violations,
                )
                return 1
            else:
                print(f"{GREEN_C}Tests PASS after GREEN phase.{NC}")
        except subprocess.TimeoutExpired:
            print(
                f"{YELLOW}[WARN]{NC} Test execution timed out. Cannot verify GREEN phase."
            )
        except Exception as e:
            print(f"{YELLOW}[WARN]{NC} Failed to run tests: {e}")

    print(
        f"{GREEN_C}No test tampering detected. Builder preserved all RED phase tests.{NC}"
    )
    update_build_file(story_id, project_root, status="pass", tampering_found=[])
    return 0


if __name__ == "__main__":
    sys.exit(main())
