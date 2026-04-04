#!/usr/bin/env python3
"""
check_test_quality.py -- Enforcement script for test quality rules.

Scans test files for anti-patterns that produce tests which pass but catch nothing.
Agents run this directly before committing. Blocks the commit if violations are found.

Checks:
1. .skip() / .todo() / @pytest.mark.skip -- banned, use xfail/BUG pattern
2. mock() in integration test directories -- integration tests must use real DB
3. Fixture-only tests -- INSERT without calling production code = fake coverage
4. Weak assertion banlist (Rule 2b) -- banned patterns that catch zero bugs
5. Source assertions in frontend tests -- tests must test behavior, not code shape

Language-agnostic: reads configuration from test_enforcement.json in the project root.

Usage:
    python check_test_quality.py [--backend] [--frontend] [--config PATH]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"

violations: list[str] = []
warnings: list[str] = []


def load_config(config_path: Path | None = None) -> dict:
    """Load test enforcement config from JSON file."""
    if config_path and config_path.exists():
        return json.loads(config_path.read_text())

    script_dir = Path(__file__).resolve().parent
    for parent in [script_dir] + list(script_dir.parents):
        candidate = parent / "test_enforcement.json"
        if candidate.exists():
            return json.loads(candidate.read_text())

    return {}


def find_root() -> Path:
    """Find project root by walking up from script location."""
    script_dir = Path(__file__).resolve().parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / "CLAUDE.md").exists() or (parent / ".git").exists():
            return parent
    return script_dir


# -- Check 1: No .skip() / .todo() / @pytest.mark.skip ---


def check_skip_patterns_python(test_dirs: list[Path], root: Path) -> None:
    """Scan Python test files for skip without xfail."""
    for test_dir in test_dirs:
        if not test_dir.exists():
            continue
        for f in test_dir.rglob("test_*.py"):
            content = f.read_text(encoding="utf-8", errors="replace")
            rel = str(f.relative_to(root))

            for m in re.finditer(r"@pytest\.mark\.skip\b", content):
                line_no = content[: m.start()].count("\n") + 1
                violations.append(
                    f"{rel}:{line_no} -- @pytest.mark.skip is banned. "
                    "Use @pytest.mark.xfail(reason='BUG: ...') instead."
                )

            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                stripped = line.lstrip()
                if "pytest.skip(" not in stripped:
                    continue
                nearby = "\n".join(lines[max(0, i - 1) : i + 3])
                if "allow_module_level" in nearby:
                    continue
                if stripped.startswith("pytest.skip(") and not line.startswith(
                    " " * 8
                ):
                    violations.append(
                        f"{rel}:{i} -- pytest.skip() at top level is banned. "
                        "Use @pytest.mark.xfail(reason='BUG: ...') instead."
                    )


def check_skip_patterns_frontend(frontend_dir: Path, root: Path) -> None:
    """Scan TypeScript/JavaScript test files for .skip() and .todo()."""
    if not frontend_dir.exists():
        return

    for ext in ["*.test.ts", "*.test.tsx", "*.test.js", "*.test.jsx", "*.spec.ts", "*.spec.tsx", "*.spec.js"]:
        for f in frontend_dir.rglob(ext):
            content = f.read_text(encoding="utf-8", errors="replace")
            rel = str(f.relative_to(root))

            for pattern, name in [
                (r"\b(?:it|describe|test)\.skip\(", ".skip()"),
                (r"\b(?:it|describe|test)\.todo\(", ".todo()"),
            ]:
                for m in re.finditer(pattern, content):
                    line_no = content[: m.start()].count("\n") + 1
                    violations.append(
                        f"{rel}:{line_no} -- {name} is banned. "
                        "Assert broken value with // BUG: comment instead."
                    )


# -- Check 2: No mock() in integration tests ---


def check_mock_in_integration(
    int_dirs: list[Path], root: Path, known_files: set[str]
) -> None:
    """Integration tests must not mock the database layer."""
    mock_db_patterns = [
        (r"mock.*(?:session|Session|AsyncSession)", "Mocking DB session"),
        (r"Mock.*(?:session|Session)", "Mocking DB session"),
        (r"patch.*(?:get_session|get_db|database)", "Patching DB dependency"),
        (r"AsyncMock.*(?:execute|scalar|fetch)", "Mocking query execution"),
    ]

    for int_dir in int_dirs:
        if not int_dir.exists():
            continue
        for f in int_dir.rglob("test_*.py"):
            content = f.read_text(encoding="utf-8", errors="replace")
            rel = str(f.relative_to(root))
            is_known = any(known in f.name for known in known_files)

            for pat, msg in mock_db_patterns:
                for m in re.finditer(pat, content, re.I):
                    line_no = content[: m.start()].count("\n") + 1
                    issue = (
                        f"{rel}:{line_no} -- {msg} in integration test. "
                        "Integration tests must use a real database, not mocks."
                    )
                    if is_known:
                        warnings.append(f"[KNOWN] {issue}")
                    else:
                        violations.append(issue)


# -- Check 3: Fixture-only tests ---


def check_fixture_only_tests(int_dirs: list[Path], root: Path) -> None:
    """Detect tests that INSERT fixture data without calling production code."""
    for int_dir in int_dirs:
        if not int_dir.exists():
            continue
        for f in int_dir.rglob("test_*.py"):
            content = f.read_text(encoding="utf-8", errors="replace")
            rel = str(f.relative_to(root))

            if "conftest" in f.name:
                continue

            insert_count = len(re.findall(r"INSERT\s+INTO", content, re.I))
            has_client_call = bool(
                re.search(r"client\.(get|post|put|delete|patch)\(", content)
            )
            has_service_import = bool(
                re.search(r"from app\.", content)
                or re.search(r"from src\.", content)
            )
            has_production_call = has_client_call or has_service_import

            if insert_count >= 3 and not has_production_call:
                warnings.append(
                    f"{rel} -- {insert_count} INSERT statements but no production "
                    "code calls. Tests that only INSERT fake data and SELECT it back "
                    "prove nothing about production behavior."
                )


# -- Check 4: Weak assertion banlist (Rule 2b) ---

# Python banned patterns -- terminal/sole assertions that catch zero bugs
PYTHON_BANNED_SOLE = [
    (re.compile(r"assert\s+\w[\w.\[\]\"']*\s+is\s+not\s+None\s*$", re.IGNORECASE), "bare 'is not None' -- assert a concrete value (Rule 2b)"),
    (re.compile(r"assert\s+\w[\w.\[\]\"']*\s+!=\s*None\s*$", re.IGNORECASE), "bare '!= None' -- assert a concrete value (Rule 2b)"),
    (re.compile(r"assert\s+isinstance\s*\([^)]+,\s*(?:dict|list|str|int|float)\s*\)\s*$", re.IGNORECASE), "bare isinstance() -- assert field values (Rule 2b)"),
    (re.compile(r"assert\s+len\s*\([^)]+\)\s*[>!=]+\s*0\s*$", re.IGNORECASE), "bare len() > 0 -- assert exact count (Rule 2b)"),
]

# TypeScript banned patterns -- terminal/sole assertions that catch zero bugs
TS_BANNED_SOLE = [
    (re.compile(r"\.toBeDefined\s*\(\s*\)"), "toBeDefined() -- assert concrete value (Rule 2b)"),
    (re.compile(r"\.toBeTruthy\s*\(\s*\)"), "toBeTruthy() -- assert concrete value (Rule 2b)"),
    (re.compile(r"\.toBeFalsy\s*\(\s*\)"), "toBeFalsy() -- use concrete check (Rule 2b)"),
    (re.compile(r"\.not\.toBeNull\s*\(\s*\)"), ".not.toBeNull() -- assert concrete value (Rule 2b)"),
    (re.compile(r"\.toHaveLength\s*\(\s*expect\.any\s*\("), "toHaveLength(expect.any()) -- use exact count (Rule 2b)"),
    (re.compile(r"\.toBeInstanceOf\s*\(\s*(?:Object|Array)\s*\)"), "toBeInstanceOf(Object/Array) -- assert fields (Rule 2b)"),
]

# Strong assertion patterns that indicate a guard (not sole) usage
STRONG_PATTERNS_PY = re.compile(r"(pytest\.approx|assert\s+\w[\w.\[\]\"']*\s*==)")
STRONG_PATTERNS_TS = re.compile(r"(\.toBe\(|\.toEqual\(|\.toBeCloseTo\(|\.toHaveLength\(\s*\d)")


def _has_strong_followup(lines: list[str], start_idx: int, is_python: bool) -> bool:
    """Check if the next 3 lines contain a strong assertion on the same variable (guard pattern)."""
    strong_pat = STRONG_PATTERNS_PY if is_python else STRONG_PATTERNS_TS
    end = min(start_idx + 4, len(lines))  # look ahead 3 lines (indices start_idx+1..start_idx+3)
    for j in range(start_idx + 1, end):
        if strong_pat.search(lines[j]):
            return True
    return False


def _is_auth_status_check(line: str) -> bool:
    """Return True if the line asserts a non-success status code (auth rejection tests)."""
    m = re.search(r"status_code\s*==\s*(\d+)", line)
    if m:
        code = int(m.group(1))
        return code not in (200, 201)
    return False


def _function_has_body_assertion(lines: list[str], func_start: int) -> bool:
    """Check if a test function contains a body/response-data assertion after the status check."""
    for j in range(func_start, len(lines)):
        stripped = lines[j].strip()
        # Stop at next function definition
        if j > func_start and re.match(r"^(async\s+)?def\s+test_", stripped):
            break
        # Look for body/data/json assertions
        if re.search(r"(\.json\(\)|resp\.data|response\.data|resp\.body|response\.body|res\.body)", stripped):
            if re.search(r"(assert\s+|==|!=)", stripped):
                return True
        if re.search(r"assert\s+.*\[", stripped) and "status" not in stripped.lower():
            return True
    return False


def check_weak_assertions(
    test_dirs: list[Path], root: Path, write_path_keywords: list[str]
) -> None:
    """Detect banned weak assertion patterns per Rule 2b banlist.

    Scans ALL test directories (not just integration). For each banned pattern
    match, looks ahead 3 lines for a strong assertion (guard pattern). If no
    strong followup is found, it is a violation.
    """
    for test_dir in test_dirs:
        if not test_dir.exists():
            continue
        for f in test_dir.rglob("test_*.py"):
            content = f.read_text(encoding="utf-8", errors="replace")
            rel = str(f.relative_to(root))

            if "conftest" in f.name:
                continue

            lines = content.split("\n")
            for i, line in enumerate(lines):
                stripped = line.strip()

                # Skip comments
                if stripped.startswith("#"):
                    continue

                # Check Python banned patterns
                for pat, msg in PYTHON_BANNED_SOLE:
                    if pat.search(stripped):
                        # Check for guard pattern (strong assertion within next 3 lines)
                        if _has_strong_followup(lines, i, is_python=True):
                            continue
                        violations.append(
                            f"{rel}:{i + 1} -- {msg}"
                        )

                # Special check: status_code == 200/201 without body assertion
                if re.search(r"assert\s+\w+\.status_code\s*==\s*(200|201)\s*$", stripped):
                    # Find the enclosing function
                    func_start = i
                    for k in range(i, -1, -1):
                        if re.match(r"^(async\s+)?def\s+test_", lines[k].strip()):
                            func_start = k
                            break
                    if not _function_has_body_assertion(lines, func_start):
                        violations.append(
                            f"{rel}:{i + 1} -- bare status_code == 200/201 without body assertion (Rule 2b)"
                        )


def check_weak_assertions_frontend(frontend_dir: Path, root: Path) -> None:
    """Detect banned weak assertion patterns in TypeScript/JavaScript tests (Rule 2b)."""
    if not frontend_dir.exists():
        return

    for ext in ["*.test.ts", "*.test.tsx", "*.test.js", "*.test.jsx", "*.spec.ts", "*.spec.tsx", "*.spec.js"]:
        for f in frontend_dir.rglob(ext):
            content = f.read_text(encoding="utf-8", errors="replace")
            rel = str(f.relative_to(root))

            lines = content.split("\n")
            for i, line in enumerate(lines):
                stripped = line.strip()

                # Skip comments
                if stripped.startswith("//") or stripped.startswith("/*"):
                    continue

                for pat, msg in TS_BANNED_SOLE:
                    if pat.search(stripped):
                        # Check for guard pattern (strong assertion within next 3 lines)
                        if _has_strong_followup(lines, i, is_python=False):
                            continue
                        violations.append(
                            f"{rel}:{i + 1} -- {msg}"
                        )


# -- Check 5: Source assertions in frontend tests ---


def check_source_assertions_frontend(frontend_dir: Path, root: Path) -> None:
    """Frontend tests must not read source files and assert on content."""
    if not frontend_dir.exists():
        return

    for ext in ["*.test.ts", "*.test.tsx", "*.test.js", "*.test.jsx", "*.spec.ts", "*.spec.tsx"]:
        for f in frontend_dir.rglob(ext):
            content = f.read_text(encoding="utf-8", errors="replace")
            rel = str(f.relative_to(root))

            if "readFileSync" in content or "readFile(" in content:
                violations.append(
                    f"{rel} -- Reading source files in tests is banned. "
                    "Tests must test behavior, not code shape."
                )


# -- Main ---


def main() -> int:
    args = set(sys.argv[1:])

    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0

    # Strip flag values (e.g. config path) before checking which checks to run
    known_flags = {"--check-only", "--config", "--backend", "--frontend", "--help", "-h"}
    flag_only = {a for a in args if a.startswith("--") or a.startswith("-")}
    do_backend = "--backend" in args or not (flag_only - known_flags) and "--frontend" not in args
    do_frontend = "--frontend" in args or not (flag_only - known_flags) and "--backend" not in args

    config_path = None
    for i, arg in enumerate(sys.argv):
        if arg == "--config" and i + 1 < len(sys.argv):
            config_path = Path(sys.argv[i + 1])

    config = load_config(config_path)
    root = find_root()

    backend_test_dirs = [root / p for p in config.get("backend_test_dirs", [])]
    int_test_dirs = [root / p for p in config.get("integration_test_dirs", [])]
    frontend_dir = root / config.get("frontend_test_dir", "src")
    known_files = set(config.get("known_mock_files", []))
    write_path_keywords = config.get("oracle_check", {}).get(
        "write_path_keywords",
        ["order", "payment", "total", "balance", "fee", "price"],
    )

    print(f"{YELLOW}[TEST QUALITY]{NC} Scanning test files...")

    if do_backend:
        check_skip_patterns_python(backend_test_dirs, root)
        check_mock_in_integration(int_test_dirs, root, known_files)
        check_fixture_only_tests(int_test_dirs, root)
        # Rule 2b: scan ALL test dirs for weak assertions, not just integration
        all_backend_dirs = list(set(backend_test_dirs + int_test_dirs))
        check_weak_assertions(all_backend_dirs, root, write_path_keywords)

    if do_frontend:
        check_skip_patterns_frontend(frontend_dir, root)
        check_source_assertions_frontend(frontend_dir, root)
        check_weak_assertions_frontend(frontend_dir, root)

    if warnings:
        print(f"\n{YELLOW}Warnings (should fix):{NC}")
        for w in warnings:
            print(f"  {w}")

    if violations:
        print(f"\n{RED}Violations (must fix before commit):{NC}")
        for v in violations:
            print(f"  {v}")
        print(
            f"\n{RED}[FAIL]{NC} {len(violations)} test quality violation(s) found. "
            f"See rules/test-quality.md for details (Rule 2b: weak assertion banlist)."
        )
        return 1

    print(f"\n{GREEN}[PASS]{NC} Test quality check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
