#!/usr/bin/env python3
"""
check_msw_contracts.py -- Enforcement: MSW handlers must use backend field names.

Scans frontend test files for MSW handlers (http.get/post/etc + HttpResponse.json),
extracts the field names from the mock response objects, then cross-references them
against the Pydantic response models from the backend.

If an MSW handler returns field names that DON'T exist in the Pydantic model but
DO exist in the frontend TypeScript types, the mock was written from the frontend
perspective (wrong). The test will pass but catch no real bugs.

Usage:
    python check_msw_contracts.py --config test_enforcement.json
    python check_msw_contracts.py --story 1500   # only check files for this story

Exit code: 0 = all MSW handlers use backend fields, 1 = frontend-perspective mocks found
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
    script_dir = Path(__file__).resolve().parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / "CLAUDE.md").exists():
            return parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / ".git").is_dir():
            return parent
    return Path.cwd()


def find_pydantic_models(schema_dirs: list[Path]) -> dict[str, set[str]]:
    """Parse Pydantic response models and extract field names.

    Returns: {ModelName: {field1, field2, ...}}
    """
    models: dict[str, set[str]] = {}

    for schema_dir in schema_dirs:
        if not schema_dir.exists():
            continue
        for py_file in schema_dir.rglob("*.py"):
            content = py_file.read_text(errors="replace")

            # Find class definitions that extend BaseModel
            class_pattern = r"class\s+(\w+)\s*\([^)]*BaseModel[^)]*\):"
            for class_match in re.finditer(class_pattern, content):
                class_name = class_match.group(1)
                class_start = class_match.end()

                # Find the next class or end of file
                next_class = re.search(r"\nclass\s+\w+", content[class_start:])
                if next_class:
                    class_body = content[class_start : class_start + next_class.start()]
                else:
                    class_body = content[class_start:]

                # Extract field names (name: type or name = Field(...))
                fields = set()
                for field_match in re.finditer(
                    r"^\s+(\w+)\s*[:=]", class_body, re.MULTILINE
                ):
                    field_name = field_match.group(1)
                    # Skip dunder methods and private attrs
                    if not field_name.startswith("_") and field_name != "model_config":
                        fields.add(field_name)

                if fields:
                    models[class_name] = fields

    return models


def extract_msw_handlers(test_file: Path) -> list[dict]:
    """Extract MSW handler URLs and response field names from a test file.

    Returns: [{url: "/api/v1/bots", fields: {"id", "name", "status"}, line: 42}, ...]
    """
    content = test_file.read_text(errors="replace")
    handlers = []

    # Pattern: http.get('/api/v1/...', () => HttpResponse.json({...}))
    # or http.get(`${API}/bots`, () => HttpResponse.json({...}))
    handler_pattern = (
        r"http\.(get|post|put|delete|patch)\s*\("
        r"\s*(?:[`'\"]([^`'\"]+)[`'\"]|`\$\{[^}]+\}([^`]+)`)"
    )

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        m = re.search(handler_pattern, line)
        if not m:
            continue

        url = m.group(2) or m.group(3) or ""

        # Find the HttpResponse.json({...}) call near this handler
        # Look at this line and the next 20 lines for the JSON object
        chunk = "\n".join(lines[i - 1 : min(i + 20, len(lines))])

        # Extract field names from the JSON object literal
        # Look for HttpResponse.json( followed by object fields
        json_match = re.search(r"HttpResponse\.json\s*\(", chunk)
        if not json_match:
            continue

        # Extract top-level field names from the object
        after_json = chunk[json_match.end() :]
        fields = set()

        # Simple field extraction: look for `key:` patterns (JS object keys)
        for field_match in re.finditer(r"(\w+)\s*:", after_json):
            field = field_match.group(1)
            # Skip JS keywords, common non-field tokens, and false positives
            if field not in {
                "status",
                "headers",
                "type",
                "statusText",
                "const",
                "let",
                "var",
                "return",
                "if",
                "else",
                "function",
                "async",
                "await",
                "wrapper",  # test utility wrapper
                "target",  # DOM event target
                "value",  # DOM input value
                "checked",  # DOM checkbox
                "onChange",  # React handler
                "onClick",  # React handler
                "onSubmit",  # React handler
                "className",  # React class
                "children",  # React children
                "key",  # React key
                "ref",  # React ref
                "style",  # React style
                "data",  # generic
                "error",  # generic
                "message",  # generic
                "code",  # generic
                # TanStack Query / test infrastructure
                "defaultOptions",
                "queries",
                "mutations",
                "retry",
                "args",
                "detail",
                "request",
                # Test capture patterns
                "capturedBody",
                "captured",
                "sent",
                # WebSocket / EventSource test patterns
                "onopen",
                "readyState",
                "event",
                # Pagination (query params, not response fields)
                "pageSize",
                # Component state (not API response)
                "selectedBotId",
                # Common test-only identifiers
                "ORACLE",
                "BUG",
                "TODO",
            } and not re.match(r"^\d", field):
                fields.add(field)
            # Stop after closing paren or after ~10 fields
            if len(fields) > 15:
                break

        if fields:
            handlers.append({"url": url, "fields": fields, "line": i})

    return handlers


def find_msw_test_files(project_root: Path, story_id: str | None = None) -> list[Path]:
    """Find MSW test files, optionally filtered by story."""
    if story_id:
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
            files = []
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                if line and (line.endswith(".test.tsx") or line.endswith(".test.ts")):
                    full = project_root / line
                    if full.exists():
                        # Check if file uses MSW
                        content = full.read_text(errors="replace")
                        if "HttpResponse" in content or "setupServer" in content:
                            files.append(full)
            return files
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Fallback: scan all frontend test files
    frontend_dir = project_root / "platform" / "frontend" / "src"
    if not frontend_dir.exists():
        return []

    files = []
    for ext in ["*.test.tsx", "*.test.ts", "*.msw.test.tsx", "*.msw.test.ts"]:
        for f in frontend_dir.rglob(ext):
            content = f.read_text(errors="replace")
            if "HttpResponse" in content or "setupServer" in content:
                files.append(f)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check MSW handlers use backend field names"
    )
    parser.add_argument("--story", type=str, help="Check only files for this story")
    parser.add_argument("--config", type=str, help="Path to test_enforcement.json")
    args = parser.parse_args()

    project_root = find_project_root()

    # Find schema directories
    schema_dirs = [
        project_root / "platform" / "services" / "api" / "app" / "schemas",
        project_root / "platform" / "shared" / "models",
    ]

    # --- Step 1: Parse Pydantic models ---
    pydantic_models = find_pydantic_models(schema_dirs)
    if not pydantic_models:
        print(
            f"{YELLOW}[WARN]{NC} No Pydantic models found. Cannot verify MSW contracts."
        )
        return 0

    print(f"Found {len(pydantic_models)} Pydantic response model(s)")

    # --- Step 2: Find MSW test files ---
    msw_files = find_msw_test_files(project_root, args.story)
    if not msw_files:
        print(f"{GREEN}No MSW test files found. Nothing to check.{NC}")
        return 0

    print(f"Scanning {len(msw_files)} MSW test file(s)...")

    # --- Step 3: Extract and validate handlers ---
    violations = []
    warnings = []

    # Build a set of all known Pydantic field names
    all_pydantic_fields: set[str] = set()
    for fields in pydantic_models.values():
        all_pydantic_fields.update(fields)

    for msw_file in msw_files:
        handlers = extract_msw_handlers(msw_file)
        rel_path = str(msw_file.relative_to(project_root))

        for handler in handlers:
            mock_fields = handler["fields"]
            line = handler["line"]

            # Check each mock field against known Pydantic fields
            unknown_fields = []
            for field in mock_fields:
                # Is this field in ANY Pydantic model?
                if field not in all_pydantic_fields:
                    # Could be a frontend-only field name
                    # Check if a "similar" field exists (camelCase vs snake_case)
                    snake = re.sub(r"([a-z])([A-Z])", r"\1_\2", field).lower()
                    camel = re.sub(r"_([a-z])", lambda m: m.group(1).upper(), field)
                    if (
                        snake not in all_pydantic_fields
                        and camel not in all_pydantic_fields
                    ):
                        unknown_fields.append(field)

            if unknown_fields:
                # Check if these are likely frontend-perspective fields
                # (common indicators: camelCase when Pydantic uses snake_case)
                has_camel = any(re.search(r"[a-z][A-Z]", f) for f in unknown_fields)
                if has_camel:
                    violations.append(
                        f"{rel_path}:{line} — MSW handler has camelCase fields "
                        f"not in any Pydantic model: {', '.join(unknown_fields)}. "
                        f"MSW mocks must use the EXACT backend field names "
                        f"(snake_case from Pydantic), not frontend TypeScript names."
                    )
                else:
                    warnings.append(
                        f"{rel_path}:{line} — MSW handler has fields not found in "
                        f"any Pydantic model: {', '.join(unknown_fields)}. "
                        f"Verify these match the actual backend response."
                    )

    # Report
    if warnings:
        for w in warnings:
            print(f"{YELLOW}[WARN]{NC} {w}")

    if violations:
        print(f"\n{RED}MSW contract violations:{NC}")
        for v in violations:
            print(f"  {RED}[FAIL]{NC} {v}")
        print(
            f"\n{RED}MSW handlers must return what the BACKEND sends, not what the "
            f"FRONTEND expects. Read the Pydantic model first.{NC}"
        )
        return 1

    print(
        f"\n{GREEN}MSW contract check passed. "
        f"All handler fields match Pydantic models.{NC}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
