#!/usr/bin/env python3
"""
check_test_quality.py -- Enforcement script for test quality rules.

Scans test files for anti-patterns that produce tests which pass but catch nothing.
Agents run this directly before committing. Blocks the commit if violations are found.

Checks:
1. .skip() / .todo() / @pytest.mark.skip -- banned, use xfail/BUG pattern
2. mock() in integration test directories -- integration tests must use real DB
3. Fixture-only tests -- INSERT without calling production code = fake coverage
4. Weak assertions -- "is not None" without value assertions = catches nothing
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


# -- Check 4: Weak assertions in write-path tests ---


def check_weak_assertions(
    int_dirs: list[Path], root: Path, write_path_keywords: list[str]
) -> None:
    """Detect tests that only assert 'is not None' without computed values."""
    for int_dir in int_dirs:
        if not int_dir.exists():
            continue
        for f in int_dir.rglob("test_*.py"):
            content = f.read_text(encoding="utf-8", errors="replace")
            rel = str(f.relative_to(root))

            if "conftest" in f.name:
                continue

            content_lower = content.lower()
            is_write_path = any(kw in content_lower for kw in write_path_keywords)
            if not is_write_path:
                continue

            assertions = re.findall(r"assert\s+.+", content)
            if not assertions:
                continue

            weak = 0
            strong = 0
            for a in assertions:
                a_lower = a.lower()
                if "is not none" in a_lower or "is none" in a_lower:
                    weak += 1
                elif "status_code" in a_lower:
                    weak += 1
                elif "pytest.approx" in a or "==" in a or ">=" in a or "<=" in a:
                    strong += 1
                else:
                    strong += 1

            if weak > 0 and strong == 0:
                warnings.append(
                    f"{rel} -- All {weak} assertions are weak (is not None / "
                    "status_code only). Add at least one value assertion."
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

    do_backend = "--backend" in args or not (args - {"--check-only", "--config"})
    do_frontend = "--frontend" in args or not (args - {"--check-only", "--config"})

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
        check_weak_assertions(int_test_dirs, root, write_path_keywords)

    if do_frontend:
        check_skip_patterns_frontend(frontend_dir, root)
        check_source_assertions_frontend(frontend_dir, root)

    if warnings:
        print(f"\n{YELLOW}Warnings (should fix):{NC}")
        for w in warnings:
            print(f"  {w}")

    if violations:
        print(f"\n{RED}Violations (must fix before commit):{NC}")
        for v in violations:
            print(f"  {v}")
        print(
            f"\n{RED}[FAIL]{NC} {len(violations)} test quality violation(s) found."
        )
        return 1

    print(f"\n{GREEN}[PASS]{NC} Test quality check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
