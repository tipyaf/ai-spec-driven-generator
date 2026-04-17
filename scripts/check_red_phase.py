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
import ast
import re
import subprocess
import sys
from pathlib import Path

# Unified UI helpers (v5). Import best-effort; fall back to plain print.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from ui_messages import fail as ui_fail, success as ui_success, info as ui_info, warn as ui_warn  # noqa: E402
except Exception:  # pragma: no cover
    def ui_fail(gate, reason, fix="", **_):
        print(f"[FAIL {gate}] {reason} :: fix: {fix}")
    def ui_success(gate, reason, **_):
        print(f"[PASS {gate}] {reason}")
    def ui_info(text, **_):
        print(text)
    def ui_warn(text, **_):
        print(f"[WARN] {text}")

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"


# --- AST-based trivial-fail detection (v5 refactor) ----------------------
# Refactor notes:
#   The legacy regex approach missed several semantically equivalent trivial
#   assertions. The AST walker catches them structurally. Examples:
#     assert 1 != 2               -> trivial (tautology, always true in negation)
#     assert not (2 == 2)         -> trivial
#     assert 0                    -> trivial
#     pytest.fail("...")          -> trivial
#     if True: raise AssertionError -> trivial
#   vs the regex, which only matched the specific text "assert False".


def _is_trivial_assert_node(node: ast.AST) -> bool:
    """Decide whether a single AST node represents a trivial/tautological assert.

    Catches cases the regex missed: `assert 1 != 2`, `assert not True`,
    `assert 0`, `assert x == x` literals, `pytest.fail(...)`, etc.
    """
    if isinstance(node, ast.Assert):
        test = node.test
        # assert False / assert 0 / assert "" ...
        if isinstance(test, ast.Constant):
            return not bool(test.value)
        # assert not True  -> UnaryOp(Not, Constant(True))
        if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            operand = test.operand
            if isinstance(operand, ast.Constant) and bool(operand.value):
                return True
            # assert not (a == a)
            if isinstance(operand, ast.Compare) and _is_literal_tautology(operand):
                return True
        # assert 1 == 2, assert 1 != 1, etc. — numeric literal comparison
        if isinstance(test, ast.Compare):
            return _is_literal_contradiction_or_tautology(test)
    # pytest.fail(...) / raise AssertionError
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        call = node.value
        # pytest.fail(...)
        if isinstance(call.func, ast.Attribute) and call.func.attr == "fail":
            if isinstance(call.func.value, ast.Name) and call.func.value.id == "pytest":
                return True
    if isinstance(node, ast.Raise):
        exc = node.exc
        if isinstance(exc, ast.Name) and exc.id == "AssertionError":
            return True
        if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
            if exc.func.id == "AssertionError":
                return True
    return False


def _is_literal_contradiction_or_tautology(cmp: ast.Compare) -> bool:
    """Return True when every operand is a literal constant (always known)."""
    if not isinstance(cmp.left, ast.Constant):
        return False
    for comparator in cmp.comparators:
        if not isinstance(comparator, ast.Constant):
            return False
    # We found a comparison involving only literals — the result is a
    # compile-time constant, which is the textbook definition of a trivial
    # assert (never dependent on the production code under test).
    return True


def _is_literal_tautology(cmp: ast.Compare) -> bool:
    return _is_literal_contradiction_or_tautology(cmp)


def detect_trivial_python_ast(content: str) -> list[tuple[int, str]]:
    """AST-based scan. Returns list of (lineno, snippet)."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    trivial: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if _is_trivial_assert_node(node):
            snippet = ast.unparse(node) if hasattr(ast, "unparse") else "<assert>"
            trivial.append((getattr(node, "lineno", 0), snippet[:80]))
    return trivial


def detect_trivial_js_tree_sitter(content: str) -> list[tuple[int, str]]:
    """Tree-sitter based JS/TS scan.

    tree-sitter is optional. When it's not installed we fall back to the
    original regex patterns (kept for compatibility). This means the tool
    works out of the box on fresh environments.
    """
    try:
        import tree_sitter  # type: ignore  # noqa: F401
    except Exception:
        # Fall back to regex when tree-sitter is unavailable.
        findings: list[tuple[int, str]] = []
        for i, line in enumerate(content.splitlines(), start=1):
            for pattern in TRIVIAL_FAIL_PATTERNS_TS:
                if re.search(pattern, line):
                    findings.append((i, line.strip()[:80]))
                    break
        return findings

    # If tree-sitter is available, we still only do a regex pass for now
    # (grammar loading is project-specific). The regex list is a superset
    # of the v4 list so this is strictly better than the old behaviour.
    findings = []
    for i, line in enumerate(content.splitlines(), start=1):
        for pattern in TRIVIAL_FAIL_PATTERNS_TS:
            if re.search(pattern, line):
                findings.append((i, line.strip()[:80]))
                break
    return findings


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
    """Detect tests that fail trivially (assert False, raise) instead of testing real code.

    v5 refactor: uses AST walk for Python (catches `assert 1 != 2`,
    `pytest.fail()`, `raise AssertionError` semantically — not just by
    textual match). Falls back to regex for JS/TS.
    """
    issues = []
    for tf in test_files:
        fpath = project_root / tf
        if not fpath.exists():
            continue
        content = fpath.read_text(errors="replace")
        is_python = tf.endswith(".py")

        if is_python:
            trivial_findings = detect_trivial_python_ast(content)
            trivial_count = len(trivial_findings)
            # Real-assertion count: parse AST and count Assert nodes that are NOT trivial.
            try:
                tree = ast.parse(content)
                real_asserts = sum(
                    1
                    for n in ast.walk(tree)
                    if isinstance(n, ast.Assert) and not _is_trivial_assert_node(n)
                )
            except SyntaxError:
                real_asserts = 0
        else:
            trivial_findings = detect_trivial_js_tree_sitter(content)
            trivial_count = len(trivial_findings)
            real_asserts = len(re.findall(r"expect\s*\(", content))

        if trivial_count > 0 and real_asserts == 0:
            samples = ", ".join(f"L{lineno}" for lineno, _ in trivial_findings[:3])
            issues.append(
                f"{tf}: ALL {trivial_count} assertion(s) are trivial failures "
                f"(sample lines: {samples}). Tests must assert on "
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


def _scan_branch(project_root: Path) -> int:
    """Scan every commit on the branch (git log main..HEAD) for trivial-fail tests.

    Used by the orchestrator in preflight mode. Returns 0 if clean, 1 if any
    commit contains a test file that is 100% trivial-fail assertions.
    """
    try:
        base = subprocess.run(
            ["git", "merge-base", "origin/main", "HEAD"],
            capture_output=True, text=True, cwd=project_root, timeout=10,
        ).stdout.strip()
        if not base:
            base = subprocess.run(
                ["git", "rev-parse", "main"],
                capture_output=True, text=True, cwd=project_root, timeout=10,
            ).stdout.strip() or "HEAD~20"
        log = subprocess.run(
            ["git", "log", f"{base}..HEAD", "--format=%H"],
            capture_output=True, text=True, cwd=project_root, timeout=20,
        ).stdout.strip().splitlines()
    except Exception as exc:
        ui_warn(f"--scan-branch: could not inspect git log ({exc})")
        return 0

    issues = []
    for sha in log:
        files_out = subprocess.run(
            ["git", "show", "--name-only", "--format=", sha],
            capture_output=True, text=True, cwd=project_root, timeout=10,
        ).stdout.strip().splitlines()
        for filepath in files_out:
            if not filepath:
                continue
            if not (filepath.endswith(".py") and ("test_" in filepath or "_test" in filepath)):
                continue
            try:
                content = subprocess.run(
                    ["git", "show", f"{sha}:{filepath}"],
                    capture_output=True, text=True, cwd=project_root, timeout=10,
                ).stdout
            except Exception:
                continue
            if not content:
                continue
            findings = detect_trivial_python_ast(content)
            if findings:
                # Verify: real_asserts == 0 means the entire file is trivia.
                try:
                    tree = ast.parse(content)
                    real = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Assert) and not _is_trivial_assert_node(n))
                except SyntaxError:
                    real = 0
                if real == 0:
                    issues.append(f"{sha[:8]} {filepath} has only trivial asserts")
    if issues:
        for i in issues:
            ui_fail("RED", i, fix="replace trivial asserts with real production-behavior assertions")
        return 1
    ui_success("RED", "--scan-branch: no trivial-fail test files on branch")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check RED phase: tests must fail")
    parser.add_argument("--story", required=False, type=str, help="Story ID")
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
    parser.add_argument(
        "--scan-branch", action="store_true",
        help="Orchestrator mode: scan every commit on the current branch (main..HEAD)",
    )
    args = parser.parse_args()

    if args.scan_branch:
        return _scan_branch(find_project_root())

    if not args.story:
        ui_fail("RED", "--story is required unless --scan-branch is used",
                fix="pass --story <id> or --scan-branch")
        return 2

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
