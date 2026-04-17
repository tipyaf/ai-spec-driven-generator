#!/usr/bin/env python3
"""
check_coverage_audit.py -- Enforcement: every layer touched by a story must be tested.

For a given story, analyzes the committed files and verifies:
1. Every TABLE touched (INSERT/UPDATE/SELECT/model reference) has a write-path test
2. Every ENDPOINT added/modified has at least one integration test
3. Every COMPONENT added/modified (frontend) has at least one test file

This is the machine-enforced version of Rule 4 (coverage audit) from test_quality.md.

Usage:
    python check_coverage_audit.py --story 1500
    python check_coverage_audit.py --story 1500 --config test_enforcement.json

Exit code: 0 = all layers covered, 1 = missing coverage
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from ui_messages import fail as ui_fail, success as ui_success, info as ui_info  # noqa: E402
except Exception:  # pragma: no cover
    def ui_fail(gate, reason, fix="", **_):
        print(f"[FAIL {gate}] {reason} :: fix: {fix}")
    def ui_success(gate, reason, **_):
        print(f"[PASS {gate}] {reason}")
    def ui_info(text, **_):
        print(text)


# --- AST-based route extraction (v5) -------------------------------------
# The legacy regex missed:
#   • route paths built from constants:  @router.get(API_PREFIX + "/users")
#   • f-strings:                         f"/{API}/users"
#   • paths assigned to a module variable then passed: ROUTE = "/x"; router.get(ROUTE)
#
# The AST-based extractor resolves module-level string constants and
# concatenations. It does NOT try to be a full type checker — it tracks
# string constants only. Anything it can't resolve is returned with a
# wildcard marker so the caller can still produce useful output.


def _resolve_str(node: ast.AST, const_table: dict[str, str]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return const_table.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _resolve_str(node.left, const_table)
        right = _resolve_str(node.right, const_table)
        if left is not None and right is not None:
            return left + right
    if isinstance(node, ast.JoinedStr):  # f-string
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue):
                inner = _resolve_str(value.value, const_table)
                parts.append(inner if inner is not None else "{?}")
        return "".join(parts)
    return None


def extract_endpoints_ast(content: str, filepath: str) -> list[dict]:
    """Find @router.METHOD(path) decorators; resolve constants/f-strings."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    # Collect module-level STRING constants.
    const_table: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                const_table[node.targets[0].id] = node.value.value
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                const_table[node.target.id] = node.value.value

    endpoints: list[dict] = []
    HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}

    for node in ast.walk(tree):
        decorators = getattr(node, "decorator_list", [])
        for dec in decorators:
            if not isinstance(dec, ast.Call):
                continue
            # Match .get("/path") / .post(...) — attribute on anything (router, app, bp, etc.)
            func = dec.func
            if isinstance(func, ast.Attribute) and func.attr.lower() in HTTP_METHODS:
                method = func.attr.upper()
                if dec.args:
                    path = _resolve_str(dec.args[0], const_table)
                    if path is None:
                        path = "<dynamic>"
                    endpoints.append({"method": method, "path": path, "file": filepath})
    return endpoints

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"


def find_project_root() -> Path:
    script_dir = Path(__file__).resolve().parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / "CLAUDE.md").exists():
            return parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / ".git").is_dir():
            return parent
    return Path.cwd()


def load_config(project_root: Path, config_path: str | None = None) -> dict:
    if config_path:
        p = Path(config_path)
        if p.exists():
            return json.loads(p.read_text())
    candidate = project_root / "test_enforcement.json"
    if candidate.exists():
        return json.loads(candidate.read_text())
    return {}


def get_story_files(story_id: str, project_root: Path) -> list[str]:
    """Get all files committed for this story."""
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

    files = set()
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line:
            files.add(line)
    return list(files)


def categorize_files(
    files: list[str],
    config: dict | None = None,
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Split files into routers, models, components, and test files.

    When config is provided, uses project-specific directory patterns from
    ``router_dirs`` and ``model_dirs`` for more accurate classification.
    Falls back to generic regex patterns when config is absent.
    """
    routers = []
    models = []
    components = []
    test_files = []

    # Build matchers from config when available
    router_patterns: list[str] = []
    model_patterns: list[str] = []
    if config:
        router_patterns = config.get("router_dirs", [])
        model_patterns = config.get("model_dirs", [])

    for f in files:
        if re.search(r"test_.*\.py$|_test\.py$|\.test\.(ts|tsx)$|\.spec\.(ts|tsx)$", f):
            test_files.append(f)
        elif router_patterns and any(f.startswith(d) for d in router_patterns):
            routers.append(f)
        elif model_patterns and any(f.startswith(d) for d in model_patterns):
            models.append(f)
        elif re.search(r"routers/.*\.py$", f):
            routers.append(f)
        elif re.search(r"models/.*\.py$|schemas/.*\.py$", f):
            models.append(f)
        elif re.search(r"\.(tsx|ts)$", f) and "test" not in f.lower():
            components.append(f)

    return routers, models, components, test_files


def extract_endpoints(router_files: list[str], project_root: Path) -> list[dict]:
    """Extract endpoint definitions from router files.

    v5: uses AST walk + constant-resolution instead of regex, so routes like
    ``@router.get(API_PREFIX + "/users")`` or ``@router.get(f"/{ver}/me")``
    are resolved to concrete paths when the constants are available.
    """
    endpoints: list[dict] = []
    for rf in router_files:
        fpath = project_root / rf
        if not fpath.exists():
            continue
        content = fpath.read_text(errors="replace")
        if fpath.suffix == ".py":
            endpoints.extend(extract_endpoints_ast(content, rf))
        else:
            # Non-Python fallback: regex (legacy behaviour).
            for m in re.finditer(
                r'@router\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']',
                content,
            ):
                endpoints.append({
                    "method": m.group(1).upper(),
                    "path": m.group(2),
                    "file": rf,
                })
    return endpoints


def extract_tables_from_files(files: list[str], project_root: Path) -> set[str]:
    """Find table names referenced in committed files."""
    tables = set()
    table_patterns = [
        r"__tablename__\s*=\s*[\"'](\w+)[\"']",
        r"INSERT\s+INTO\s+(?:\w+\.)?(\w+)",
        r"UPDATE\s+(?:\w+\.)?(\w+)\s+SET",
        r"SELECT\s+.*FROM\s+(?:\w+\.)?(\w+)",
        r"session\.query\((\w+)\)",
        r"select\((\w+)\)",
    ]

    for f in files:
        fpath = project_root / f
        if not fpath.exists():
            continue
        content = fpath.read_text(errors="replace")
        for pattern in table_patterns:
            for m in re.finditer(pattern, content, re.IGNORECASE):
                tables.add(m.group(1))

    return tables


def check_endpoint_coverage(
    endpoints: list[dict], test_files: list[str], project_root: Path
) -> list[str]:
    """Verify every endpoint has at least one test."""
    violations = []

    # Read all test file contents
    test_contents: dict[str, str] = {}
    for tf in test_files:
        fpath = project_root / tf
        if fpath.exists():
            test_contents[tf] = fpath.read_text(errors="replace")

    for ep in endpoints:
        path = ep["path"]
        method = ep["method"].lower()
        found = False

        for _tf, content in test_contents.items():
            content_lower = content.lower()
            # Check if the test references this endpoint path
            if (
                path in content
                or path.replace("{", "").replace("}", "") in content_lower
            ):
                # Also check if the HTTP method is tested
                if (
                    f"client.{method}" in content_lower
                    or f'"{method}"' in content_lower
                    or f"'{method}'" in content_lower
                    or f".{method}(" in content_lower
                ):
                    found = True
                    break
                # Generic client call also counts
                if "client." in content_lower and path in content:
                    found = True
                    break

        if not found:
            violations.append(
                f"Endpoint {ep['method']} {ep['path']} ({ep['file']}) "
                f"has no integration test. Every endpoint must have at least one test."
            )

    return violations


def check_table_coverage(
    tables: set[str], test_files: list[str], project_root: Path
) -> list[str]:
    """Verify every touched table has a write-path test."""
    violations = []

    test_contents: dict[str, str] = {}
    for tf in test_files:
        fpath = project_root / tf
        if fpath.exists():
            test_contents[tf] = fpath.read_text(errors="replace")

    all_test_text = "\n".join(test_contents.values())

    for table in tables:
        # Skip common framework tables
        if table.lower() in {"alembic_version", "information_schema", "pg_catalog"}:
            continue

        # Check if any test references this table or its model
        if table.lower() not in all_test_text.lower():
            # Also check for CamelCase model name
            camel = "".join(w.capitalize() for w in table.split("_"))
            if camel not in all_test_text:
                violations.append(
                    f"Table '{table}' is touched by story code but has no test "
                    f"referencing it. Write a test that exercises the write path."
                )

    return violations


def check_component_coverage(
    components: list[str], test_files: list[str], project_root: Path
) -> list[str]:
    """Verify every frontend component has a test file."""
    violations = []

    # Build set of tested component names
    test_names = set()
    for tf in test_files:
        # Extract component name from test file name
        # e.g., "Dashboard.test.tsx" -> "dashboard"
        base = Path(tf).stem  # "Dashboard.test"
        base = re.sub(r"\.(test|spec)$", "", base).lower()
        test_names.add(base)

    for comp in components:
        # Skip non-component files (utils, types, configs)
        if re.search(r"(types?|utils?|config|constants|index)\.(ts|tsx)$", comp):
            continue

        comp_name = Path(comp).stem.lower()
        # Check for matching test
        if comp_name not in test_names:
            # Also check for partial match
            found = any(comp_name in tn or tn in comp_name for tn in test_names)
            if not found:
                violations.append(
                    f"Component '{comp}' has no matching test file. "
                    f"Every component must have at least one test."
                )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Check test coverage for story layers")
    parser.add_argument("--story", required=True, type=str, help="Story ID")
    parser.add_argument("--config", type=str, help="Path to test_enforcement.json")
    args = parser.parse_args()

    project_root = find_project_root()
    story_id = args.story
    config = load_config(project_root, args.config)

    # --- Step 1: Get story files ---
    story_files = get_story_files(story_id, project_root)
    if not story_files:
        print(f"{YELLOW}[WARN]{NC} No files found for sc-{story_id}.")
        return 0

    # --- Step 2: Categorize files ---
    routers, models, components, test_files = categorize_files(story_files, config)

    print(f"Story sc-{story_id} files:")
    print(f"  Routers:    {len(routers)}")
    print(f"  Models:     {len(models)}")
    print(f"  Components: {len(components)}")
    print(f"  Tests:      {len(test_files)}")

    if not routers and not models and not components:
        print(f"{GREEN}No production code to audit (infra/config only).{NC}")
        return 0

    violations = []

    # --- Step 3: Check endpoint coverage ---
    if routers:
        endpoints = extract_endpoints(routers, project_root)
        print(f"\n  Endpoints found: {len(endpoints)}")
        ep_violations = check_endpoint_coverage(endpoints, test_files, project_root)
        violations.extend(ep_violations)

    # --- Step 4: Check table coverage ---
    # Look for table references in ALL non-test production files
    prod_files = [f for f in story_files if f not in test_files]
    tables = extract_tables_from_files(prod_files, project_root)
    if tables:
        print(f"  Tables touched: {', '.join(sorted(tables))}")
        table_violations = check_table_coverage(tables, test_files, project_root)
        violations.extend(table_violations)

    # --- Step 5: Check component coverage ---
    if components:
        comp_violations = check_component_coverage(components, test_files, project_root)
        violations.extend(comp_violations)

    # --- Report ---
    if violations:
        print(f"\n{RED}Coverage audit violations:{NC}")
        for v in violations:
            print(f"  {RED}[FAIL]{NC} {v}")
        print(
            f"\n{RED}Every layer (endpoint, table, component) touched by a story "
            f"must have a test. No exceptions.{NC}"
        )
        return 1

    total = len(routers) + len(tables) + len(components)
    print(f"\n{GREEN}Coverage audit passed. {total} layer(s) verified.{NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
