#!/usr/bin/env python3
"""
check_write_coverage.py -- Verify every data store with a read endpoint has a production writer.

Enforcement for test-quality.md Rule 3:
"For every data store, there must be production code that writes to it."

If a table has a GET endpoint but no production code writes to it,
the feature is incomplete -- the page will show empty data in production.

Reads configuration from test_enforcement.json in the project root.
If no config file exists, prints a warning and exits successfully.

Usage:
    python check_write_coverage.py [--report] [--config PATH]

    --report   Show coverage matrix without failing
    --config   Path to test_enforcement.json (default: project root)
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


def resolve_paths(config: dict, root: Path) -> dict:
    """Resolve all config paths relative to project root."""
    resolved = {}
    for key, value in config.items():
        if isinstance(value, list) and key.endswith(("_dirs", "_files")):
            resolved[key] = [root / p for p in value]
        elif isinstance(value, str) and key.endswith(("_dir", "_dirs")):
            resolved[key] = root / value
        else:
            resolved[key] = value
    return resolved


# -- Step 1: Find all tables from SQL schema ---


def find_tables_from_schema(
    schema_files: list[Path], migration_dirs: list[Path]
) -> list[str]:
    """Parse CREATE TABLE statements from SQL files and migrations."""
    tables: list[str] = []

    for sql_file in schema_files:
        if not sql_file.exists():
            continue
        content = sql_file.read_text(encoding="utf-8", errors="replace")
        # Match schema.table or just table
        for m in re.finditer(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"']?(\w+(?:\.\w+)?)[\"']?",
            content, re.I,
        ):
            tables.append(m.group(1))

    for mig_dir in migration_dirs:
        if not mig_dir.exists():
            continue
        for f in mig_dir.glob("*.py"):
            content = f.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(
                r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"']?(\w+(?:\.\w+)?)[\"']?",
                content, re.I,
            ):
                tables.append(m.group(1))
        # Also check SQL migration files
        for f in mig_dir.glob("*.sql"):
            content = f.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(
                r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"']?(\w+(?:\.\w+)?)[\"']?",
                content, re.I,
            ):
                tables.append(m.group(1))

    return sorted(set(tables))


# -- Step 2: Find ORM models and map to tables ---


def find_orm_models(model_dirs: list[Path]) -> dict[str, list[str]]:
    """Map table names to ORM class names by reading model files."""
    table_to_models: dict[str, list[str]] = {}

    for model_dir in model_dirs:
        if not model_dir.exists():
            continue
        for f in model_dir.rglob("*.py"):
            content = f.read_text(encoding="utf-8", errors="replace")
            for class_match in re.finditer(r"class\s+(\w+)\b[^:]*:", content):
                class_name = class_match.group(1)
                after_class = content[class_match.end():]
                next_class = re.search(r"\nclass\s+\w+", after_class)
                class_body = (
                    after_class[: next_class.start()] if next_class else after_class
                )

                table_match = re.search(
                    r'__tablename__\s*=\s*["\'](\w+)["\']', class_body
                )
                if not table_match:
                    continue
                table_name = table_match.group(1)

                schema = "public"
                schema_match = re.search(
                    r'["\']schema["\']\s*:\s*["\'](\w+)["\']', class_body
                )
                if schema_match:
                    schema = schema_match.group(1)

                key = f"{schema}.{table_name}"
                if key not in table_to_models:
                    table_to_models[key] = []
                if class_name not in table_to_models[key]:
                    table_to_models[key].append(class_name)

    return table_to_models


# -- Step 3: Check for production write paths ---


def find_production_writers(
    tables: list[str],
    table_to_model: dict[str, list[str]],
    prod_dirs: list[Path],
    root: Path,
) -> dict[str, list[str]]:
    """For each table, find production code that writes to it."""
    writers: dict[str, list[str]] = {t: [] for t in tables}
    exclude_patterns = {"tests", "test_", "conftest", "alembic", "migration"}

    for prod_dir in prod_dirs:
        if not prod_dir.exists():
            continue
        for f in prod_dir.rglob("*.py"):
            rel = str(f.relative_to(root))
            if any(p in rel.lower() for p in exclude_patterns):
                continue

            content = f.read_text(encoding="utf-8", errors="replace")

            for table in tables:
                parts = table.split(".")
                name = parts[-1] if len(parts) > 1 else parts[0]
                schema = parts[0] if len(parts) > 1 else "public"
                model_names = table_to_model.get(table, [])

                found = False
                for model_name in model_names:
                    if ".add(" in content and f"{model_name}(" in content:
                        writers[table].append(rel)
                        found = True
                        break
                if found:
                    continue

                patterns = []
                for model_name in model_names:
                    patterns.append(rf"\.add\(\s*{model_name}\s*\(")
                    patterns.append(rf"\.add\(\s*{model_name}\b")
                patterns.extend([
                    rf"INSERT\s+INTO\s+{re.escape(table)}",
                    rf"UPDATE\s+{re.escape(table)}",
                ])

                for pat in patterns:
                    if re.search(pat, content, re.I):
                        writers[table].append(rel)
                        break

    for t in writers:
        writers[t] = sorted(set(writers[t]))
    return writers


# -- Step 4: Check for read endpoints ---


def find_read_endpoints(
    tables: list[str],
    table_to_model: dict[str, list[str]],
    router_dirs: list[Path],
    root: Path,
) -> dict[str, list[str]]:
    """For each table, find router files with GET endpoints that read from it."""
    readers: dict[str, list[str]] = {t: [] for t in tables}

    for router_dir in router_dirs:
        if not router_dir.exists():
            continue
        for f in router_dir.rglob("*.py"):
            content = f.read_text(encoding="utf-8", errors="replace")
            rel = str(f.relative_to(root))

            if "@router.get" not in content and "select(" not in content.lower():
                continue

            for table in tables:
                model_names = table_to_model.get(table, [])
                parts = table.split(".")
                name = parts[-1] if len(parts) > 1 else parts[0]

                model_found = any(mn in content for mn in model_names)
                if model_found or name in content:
                    readers[table].append(rel)

    for t in readers:
        readers[t] = sorted(set(readers[t]))
    return readers


# -- Step 5: Check for write-path tests ---


def find_write_path_tests(
    tables: list[str],
    table_to_model: dict[str, list[str]],
    test_dirs: list[Path],
    root: Path,
) -> dict[str, list[str]]:
    """For each table, find test files that test production write paths."""
    test_writers: dict[str, list[str]] = {t: [] for t in tables}

    for test_dir in test_dirs:
        if not test_dir.exists():
            continue
        for f in test_dir.rglob("test_*.py"):
            content = f.read_text(encoding="utf-8", errors="replace")
            rel = str(f.relative_to(root))

            for table in tables:
                model_names = table_to_model.get(table, [])
                parts = table.split(".")
                name = parts[-1] if len(parts) > 1 else parts[0]

                has_production_import = bool(
                    re.search(r"from app\.", content)
                    or re.search(r"from src\.", content)
                    or re.search(r"import app\.", content)
                )
                references_model = any(mn in content for mn in model_names)
                references_table = name in content

                if has_production_import and (references_model or references_table):
                    has_assert = "assert " in content
                    has_production_call = bool(
                        re.search(r"await\s+\w+\.\w+\(", content)
                        or re.search(r"client\.(get|post|put|delete|patch)\(", content)
                    )
                    if has_assert and has_production_call:
                        test_writers[table].append(rel)

    for t in test_writers:
        test_writers[t] = sorted(set(test_writers[t]))
    return test_writers


# -- Main ---


def main() -> int:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return 0

    report_only = "--report" in sys.argv

    config_path = None
    for i, arg in enumerate(sys.argv):
        if arg == "--config" and i + 1 < len(sys.argv):
            config_path = Path(sys.argv[i + 1])

    config = load_config(config_path)

    if config_path and config_path.exists():
        root = config_path.resolve().parent
    elif "project_root" in config:
        root = Path(config["project_root"]).resolve()
    else:
        root = Path.cwd()
        for parent in [root] + list(root.parents):
            if (parent / "CLAUDE.md").exists() or (parent / ".git").exists():
                root = parent
                break

    resolved = resolve_paths(config, root)

    schema_files = resolved.get("schema_files", [])
    migration_dirs = resolved.get("migration_dirs", [])
    prod_dirs = resolved.get("production_dirs", [])
    router_dirs = resolved.get("router_dirs", [])
    model_dirs = resolved.get("model_dirs", [])
    int_test_dirs = resolved.get("integration_test_dirs", [])

    if not schema_files and not migration_dirs:
        print(f"{YELLOW}[WARN]{NC} No schema files or migration dirs configured.")
        print("Configure test_enforcement.json to enable write coverage checks.")
        return 0

    print(f"{YELLOW}[WRITE COVERAGE]{NC} Scanning for production write paths...")

    tables = find_tables_from_schema(schema_files, migration_dirs)
    if not tables:
        print(f"{YELLOW}[WARN]{NC} No tables found in schema files.")
        return 0

    table_to_model = find_orm_models(model_dirs)
    writers = find_production_writers(tables, table_to_model, prod_dirs, root)
    readers = find_read_endpoints(tables, table_to_model, router_dirs, root)
    test_coverage = find_write_path_tests(tables, table_to_model, int_test_dirs, root)

    violations: list[str] = []
    warnings_list: list[str] = []

    print(f"\n{'Table':<35} {'Writer?':<10} {'Reader?':<10} {'Test?':<10} {'Status'}")
    print("-" * 85)

    for table in tables:
        has_writer = bool(writers[table])
        has_reader = bool(readers[table])
        has_test = bool(test_coverage[table])

        if has_reader and not has_writer:
            status = f"{RED}NO WRITER{NC}"
            violations.append(
                f"{table}: has read endpoint(s) but NO production code writes to it. "
                f"The page will show empty data."
            )
        elif has_writer and not has_test:
            status = f"{YELLOW}NO TEST{NC}"
            warnings_list.append(
                f"{table}: has production writer but no write-path integration test."
            )
        elif has_reader and has_writer and has_test:
            status = f"{GREEN}OK{NC}"
        elif not has_reader and not has_writer:
            status = "no endpoints"
        else:
            status = f"{GREEN}OK{NC}"

        w = "yes" if has_writer else "NO"
        r = "yes" if has_reader else "no"
        t = "yes" if has_test else "no"
        print(f"  {table:<33} {w:<10} {r:<10} {t:<10} {status}")

    print()

    if warnings_list:
        print(f"{YELLOW}Warnings (write-path tests missing):{NC}")
        for w in warnings_list:
            print(f"  {w}")
        print()

    if violations:
        print(f"{RED}VIOLATIONS (tables with readers but no writers):{NC}")
        for v in violations:
            print(f"  {v}")
        print()

        if report_only:
            print(
                f"{YELLOW}[REPORT]{NC} {len(violations)} table(s) have read "
                f"endpoints but no production writer."
            )
            return 0

        print(
            f"{RED}[FAIL]{NC} {len(violations)} table(s) have read endpoints "
            f"but no production code writes to them."
        )
        return 1

    print(f"{GREEN}[PASS]{NC} All tables with read endpoints have production writers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
