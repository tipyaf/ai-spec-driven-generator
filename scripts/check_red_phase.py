#!/usr/bin/env python3
"""
check_red_phase.py -- Enforcement: tests MUST fail in RED phase.

Called by the orchestrator AFTER the test engineer commits (Step 6b).
Runs the test suite and verifies:
1. At least one test file was committed for this story
2. Tests actually FAIL (exit code != 0)
3. At least N test functions exist (not empty test files)

If tests PASS in RED phase, the tests are wrong -- they validate
existing behavior instead of defining correct behavior. This blocks
the pipeline until the test engineer fixes them.

Also updates the build file with RED phase results.

Usage:
    python check_red_phase.py --story 1500 --test-cmd "pytest path/ -x"
    python check_red_phase.py --story 1500 --backend    # auto-detect test path
    python check_red_phase.py --story 1500 --frontend   # auto-detect test path

Exit code: 0 = tests correctly fail (RED phase valid), 1 = tests pass (RED phase invalid)
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


def find_project_root() -> Path:
    """Walk up from script location to find project root."""
    script_dir = Path(__file__).resolve().parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / "CLAUDE.md").exists():
            return parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / ".git").is_dir():
            return parent
    return Path.cwd()


def get_story_test_files(story_id: str, project_root: Path) -> list[str]:
    """Find test files committed for this story."""
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--name-only",
                "--format=",
                f"--grep=\\[sc-{story_id}\\]",
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

    test_files = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # Python test files
        if re.match(r".*test_.*\.py$", line) or re.match(r".*_test\.py$", line):
            test_files.append(line)
        # TypeScript/JS test files
        if re.match(r".*\.test\.(ts|tsx|js|jsx)$", line) or re.match(
            r".*\.spec\.(ts|tsx|js|jsx)$", line
        ):
            test_files.append(line)

    return list(set(test_files))


def count_test_functions(test_files: list[str], project_root: Path) -> int:
    """Count test functions/methods across test files."""
    count = 0
    for tf in test_files:
        fpath = project_root / tf
        if not fpath.exists():
            continue
        content = fpath.read_text(errors="replace")
        # Python: def test_xxx or async def test_xxx
        count += len(re.findall(r"(?:async\s+)?def\s+test_\w+", content))
        # TypeScript: it("xxx" or test("xxx"
        count += len(re.findall(r"\b(?:it|test)\s*\(", content))
    return count


# --- Trivial-fail detection patterns ---
# These patterns indicate tests that fail for trivial reasons (assert False, raise)
# rather than testing actual production behavior.
TRIVIAL_FAIL_PATTERNS_PY = [
    r"^\s*assert\s+False\b",
    r"^\s*assert\s+0\b",
    r"^\s*assert\s+1\s*==\s*2\b",
    r"^\s*assert\s+not\s+True\b",
    r"^\s*raise\s+AssertionError\b",
    r"^\s*pytest\.fail\s*\(",
]

TRIVIAL_FAIL_PATTERNS_TS = [
    r"^\s*expect\s*\(\s*true\s*\)\s*\.toBe\s*\(\s*false\s*\)",
    r"^\s*expect\s*\(\s*false\s*\)\s*\.toBeTruthy\s*\(",
    r"^\s*throw\s+new\s+Error\s*\(",
]

# Production code import patterns -- at least one test file must import from production code
PRODUCTION_IMPORT_PATTERNS_PY = [
    r"from\s+app\.",  # FastAPI app imports
    r"from\s+services\.",  # service imports
    r"from\s+shared\.",  # shared lib imports
    r"import\s+app\.",  # direct imports
    r"from\s+engine\.",  # engine imports
    r"AsyncClient",  # httpx test client (integration tests)
    r"TestClient",  # starlette test client
    r"ASGITransport",  # httpx ASGI transport
]

PRODUCTION_IMPORT_PATTERNS_TS = [
    r"from\s+['\"]@/",  # aliased imports from src
    r"from\s+['\"]\.\.?/",  # relative imports from components/hooks
    r"import\s+.*from\s+['\"]@/",
    r"render\s*\(",  # React testing library render
    r"screen\.",  # React testing library screen queries
    r"setupServer",  # MSW server setup
]


def check_trivial_failures(test_files: list[str], project_root: Path) -> list[str]:
    """Detect tests that fail trivially (assert False, raise) instead of testing real code."""
    issues = []
    for tf in test_files:
        fpath = project_root / tf
        if not fpath.exists():
            continue
        content = fpath.read_text(errors="replace")
        is_python = tf.endswith(".py")
        patterns = TRIVIAL_FAIL_PATTERNS_PY if is_python else TRIVIAL_FAIL_PATTERNS_TS

        trivial_count = 0
        for pattern in patterns:
            trivial_count += len(re.findall(pattern, content, re.MULTILINE))

        # Count real assertions
        if is_python:
            real_asserts = len(
                re.findall(
                    r"^\s*assert\s+(?!False|0|not\s+True|1\s*==\s*2)",
                    content,
                    re.MULTILINE,
                )
            )
        else:
            real_asserts = len(re.findall(r"expect\s*\(", content))

        if trivial_count > 0 and real_asserts == 0:
            issues.append(
                f"{tf}: ALL {trivial_count} assertion(s) are trivial failures "
                f"(assert False, raise, pytest.fail). Tests must assert on "
                f"real production code behavior, not just fail unconditionally."
            )
    return issues


def check_production_imports(test_files: list[str], project_root: Path) -> list[str]:
    """Verify that test files import and call production code."""
    issues = []
    for tf in test_files:
        fpath = project_root / tf
        if not fpath.exists():
            continue
        content = fpath.read_text(errors="replace")
        is_python = tf.endswith(".py")
        patterns = (
            PRODUCTION_IMPORT_PATTERNS_PY
            if is_python
            else PRODUCTION_IMPORT_PATTERNS_TS
        )

        has_production_import = any(re.search(pattern, content) for pattern in patterns)

        if not has_production_import:
            issues.append(
                f"{tf}: No production code imports found. Tests must import from "
                f"app/, services/, shared/, or use AsyncClient/TestClient. "
                f"A test that doesn't touch production code catches nothing."
            )
    return issues


def run_tests(test_cmd: str, project_root: Path, timeout: int = 120) -> tuple[int, str]:
    """Run the test command. Returns (exit_code, output)."""
    try:
        result = subprocess.run(
            test_cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=timeout,
        )
        output = result.stdout + "\n" + result.stderr
        return result.returncode, output
    except subprocess.TimeoutExpired:
        return -1, "Test execution timed out"
    except Exception as e:
        return -1, f"Failed to run tests: {e}"


def update_build_file(
    story_id: str,
    project_root: Path,
    *,
    status: str,
    test_count: int,
    failing: int,
    error: str = "",
) -> None:
    """Update the build file with RED phase results."""
    build_file = project_root / "_work" / "build" / f"sc-{story_id}.yaml"
    if not build_file.exists():
        return

    content = build_file.read_text()

    # Simple YAML update -- find or create the tdd_red gate section
    tdd_red_block = (
        f"  tdd_red:\n"
        f"    status: {status}\n"
        f"    test_count: {test_count}\n"
        f"    failing: {failing}\n"
    )
    if error:
        tdd_red_block += f'    error: "{error}"\n'

    if "tdd_red:" in content:
        # Replace existing block
        content = re.sub(
            r"  tdd_red:\n(?:    .*\n)*",
            tdd_red_block,
            content,
        )
    elif "gates:" in content:
        # Insert after gates:
        content = content.replace("gates:\n", f"gates:\n{tdd_red_block}")

    build_file.write_text(content)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check RED phase: tests must fail")
    parser.add_argument("--story", required=True, type=str, help="Story ID")
    parser.add_argument("--test-cmd", type=str, help="Explicit test command to run")
    parser.add_argument(
        "--backend", action="store_true", help="Auto-detect backend test path"
    )
    parser.add_argument(
        "--frontend", action="store_true", help="Auto-detect frontend test path"
    )
    parser.add_argument(
        "--timeout", type=int, default=120, help="Test timeout in seconds"
    )
    args = parser.parse_args()

    project_root = find_project_root()
    story_id = args.story

    # --- Step 1: Find test files for this story ---
    test_files = get_story_test_files(story_id, project_root)
    if not test_files:
        print(f"{RED}[FAIL]{NC} sc-{story_id}: No test files found in story commits.")
        print(
            f"  The test engineer must commit test files with [sc-{story_id}] in the message."
        )
        update_build_file(
            story_id,
            project_root,
            status="fail",
            test_count=0,
            failing=0,
            error="No test files found in story commits",
        )
        return 1

    # --- Step 2: Count test functions ---
    test_count = count_test_functions(test_files, project_root)
    if test_count == 0:
        print(
            f"{RED}[FAIL]{NC} sc-{story_id}: Test files exist but contain 0 test functions."
        )
        print(f"  Files: {', '.join(test_files)}")
        update_build_file(
            story_id,
            project_root,
            status="fail",
            test_count=0,
            failing=0,
            error="Test files contain no test functions",
        )
        return 1

    print(f"Found {test_count} test function(s) in {len(test_files)} file(s):")
    for tf in test_files:
        print(f"  {tf}")

    # --- Step 2b: Check for trivially failing tests ---
    trivial_issues = check_trivial_failures(test_files, project_root)
    if trivial_issues:
        print(f"\n{RED}[FAIL]{NC} Trivially failing tests detected:")
        for issue in trivial_issues:
            print(f"  {issue}")
        print()
        print("Tests must fail because they assert on REAL production behavior")
        print("that doesn't exist yet -- not because they contain 'assert False'.")
        update_build_file(
            story_id,
            project_root,
            status="fail",
            test_count=test_count,
            failing=0,
            error="Trivially failing tests (assert False / raise / pytest.fail)",
        )
        return 1

    # --- Step 2c: Check for production code imports ---
    import_issues = check_production_imports(test_files, project_root)
    if import_issues:
        print(f"\n{RED}[FAIL]{NC} Tests don't import production code:")
        for issue in import_issues:
            print(f"  {issue}")
        print()
        print("Every test file must import from app/, services/, shared/,")
        print("or use AsyncClient/TestClient to hit real endpoints.")
        update_build_file(
            story_id,
            project_root,
            status="fail",
            test_count=test_count,
            failing=0,
            error="Tests do not import production code",
        )
        return 1

    # --- Step 3: Determine test command ---
    test_cmd = args.test_cmd
    if not test_cmd:
        if args.frontend:
            test_cmd = "npx vitest run --reporter=verbose"
        else:
            # Default: run pytest on the test files
            # Join test file paths for pytest
            file_args = " ".join(f'"{tf}"' for tf in test_files)
            test_cmd = f"python -m pytest {file_args} -x -q --tb=short"

    print(f"\nRunning tests: {test_cmd}")

    # --- Step 4: Run tests and check they FAIL ---
    exit_code, output = run_tests(test_cmd, project_root, args.timeout)

    # Count failures from output
    failing_count = 0
    # pytest: "X failed"
    m = re.search(r"(\d+) failed", output)
    if m:
        failing_count = int(m.group(1))
    # pytest: "X error"
    m = re.search(r"(\d+) error", output)
    if m:
        failing_count += int(m.group(1))
    # vitest: "X Tests Failed"
    m = re.search(r"(\d+)\s+Tests?\s+Failed", output, re.IGNORECASE)
    if m:
        failing_count = int(m.group(1))

    if exit_code == 0:
        # Tests PASSED -- this is WRONG for RED phase
        print(f"\n{RED}{'=' * 60}")
        print("RED PHASE VIOLATION: All tests PASS -- but they should FAIL!")
        print(f"{'=' * 60}{NC}")
        print()
        print("If all tests pass before the builder writes code, the tests are")
        print("validating existing (possibly broken) behavior, not defining")
        print("correct behavior.")
        print()
        print("The test engineer must fix the tests so they FAIL, then re-commit.")
        print()
        print(f"Test output:\n{output[-2000:]}")  # Last 2000 chars

        update_build_file(
            story_id,
            project_root,
            status="fail",
            test_count=test_count,
            failing=0,
            error="All tests pass in RED phase -- tests are wrong",
        )
        return 1

    # Tests FAILED -- this is CORRECT for RED phase
    print(
        f"\n{GREEN}RED phase valid:{NC} {failing_count} test(s) failing out of {test_count}."
    )

    update_build_file(
        story_id,
        project_root,
        status="done",
        test_count=test_count,
        failing=failing_count,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
