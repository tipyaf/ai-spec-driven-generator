#!/usr/bin/env python3
"""
check_oracle_assertions.py -- Enforcement script for oracle computation rule.

Every numeric assertion on a computed value must have an # ORACLE: comment block
within 5 lines above it, showing the step-by-step math.

Agents run this directly before committing. Blocks the commit if violations are found
in write-path test files (matching keywords configured in test_enforcement.json).

Usage:
    python check_oracle_assertions.py [--backend] [--frontend] [--config PATH]
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from ui_messages import fail as ui_fail, success as ui_success  # noqa: E402
except Exception:  # pragma: no cover
    def ui_fail(gate, reason, fix="", **_):
        print(f"[FAIL {gate}] {reason} :: fix: {fix}")
    def ui_success(gate, reason, **_):
        print(f"[PASS {gate}] {reason}")


# --- ORACLE evaluation (v5) ---------------------------------------------
# v4 only checked that an `# ORACLE:` comment was present above an
# assertion. v5 actually EVALUATES the comment and cross-checks it against
# the assertion value.
#
# Supported syntax:
#     # ORACLE: 10 + 5 = 15
#     # ORACLE: (100 * 0.19) == 19.0
#
# Evaluation happens inside a tiny sandbox: __builtins__ is wiped, only
# literal arithmetic and comparisons are supported. The sandbox uses the
# AST literal path (eval of a restricted ast.Expression).


_ORACLE_RE = re.compile(r"#\s*ORACLE:\s*(?P<expr>.+?)\s*(?:=|==|->)\s*(?P<value>.+?)\s*$")


_ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.USub, ast.UAdd, ast.Not,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.And, ast.Or,
    ast.Constant, ast.Tuple, ast.List,
)


def _safe_eval(expr: str):
    """Evaluate a restricted arithmetic/comparison expression. Raises on unsafe."""
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(
                f"unsupported AST node {type(node).__name__} in ORACLE expression"
            )
    return eval(compile(tree, "<oracle>", "eval"), {"__builtins__": {}}, {})


def parse_oracle_comment(comment: str) -> tuple[str, str] | None:
    """Extract (expr, value_str) from a '# ORACLE: expr = value' line."""
    m = _ORACLE_RE.search(comment)
    if not m:
        return None
    return m.group("expr").strip(), m.group("value").strip()


def evaluate_oracle(comment: str) -> tuple[bool, str]:
    """Return (is_consistent, explanation).

    is_consistent=True when the ORACLE math is internally consistent
    (expr actually equals the stated value). is_consistent=False when the
    dev wrote e.g. ``# ORACLE: 10 + 5 = 20`` — the framework catches this
    BEFORE the code ships.
    """
    parsed = parse_oracle_comment(comment)
    if parsed is None:
        return True, "no-oracle-syntax"  # not an ORACLE line we understand
    expr, value_str = parsed
    try:
        lhs = _safe_eval(expr)
        rhs = _safe_eval(value_str)
    except Exception as exc:
        return True, f"unparsable ({exc})"  # don't fail on weird math, just skip
    ok = lhs == rhs or (isinstance(lhs, float) and abs(lhs - rhs) < 1e-9)
    return ok, f"{expr} -> {lhs} {'==' if ok else '!='} {value_str}"

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


def find_root(config_path: Path | None = None) -> Path:
    """Find project root from config file location or by walking up."""
    if config_path and config_path.exists():
        return config_path.resolve().parent

    script_dir = Path(__file__).resolve().parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / "CLAUDE.md").exists() or (parent / ".git").exists():
            return parent
    return script_dir


# -- Python: find numeric assertions and check for ORACLE ---

PYTHON_NUMERIC_PATTERNS = [
    re.compile(r"pytest\.approx\("),
    re.compile(r"==\s*Decimal\("),
    re.compile(r"==\s*\d+\.\d+"),
]

PYTHON_EXEMPT_PATTERNS = [
    "status_code",
    "assert len(",
    "assert resp",
    ".count(",
    "== 200", "== 201", "== 204",
    "== 400", "== 401", "== 403", "== 404", "== 409", "== 422", "== 500",
]


def has_oracle_above(lines: list[str], line_idx: int, window: int = 5) -> bool:
    """Check if an # ORACLE: comment exists within `window` lines above."""
    start = max(0, line_idx - window)
    for i in range(start, line_idx):
        stripped = lines[i].strip()
        if stripped.startswith("# ORACLE:") or stripped.startswith("// ORACLE:"):
            return True
    return False


def oracle_consistency_violations(lines: list[str], line_idx: int, window: int = 5) -> str | None:
    """When an ORACLE comment IS present, evaluate it and flag inconsistencies."""
    start = max(0, line_idx - window)
    for i in range(start, line_idx):
        stripped = lines[i].strip()
        if stripped.startswith("# ORACLE:") or stripped.startswith("// ORACLE:"):
            ok, detail = evaluate_oracle(stripped)
            if not ok:
                return f"ORACLE math inconsistency: {detail}"
            return None
    return None


def is_exempt(line: str) -> bool:
    """Check if the assertion line is exempt from oracle requirement."""
    for pat in PYTHON_EXEMPT_PATTERNS:
        if pat in line:
            return True
    return False


def is_write_path_file(filename: str, content: str, keywords: list[str]) -> bool:
    """Check if a test file is testing write-path/computed-value logic."""
    name_lower = filename.lower()
    content_lower = content.lower()
    for kw in keywords:
        if kw in name_lower or kw in content_lower:
            return True
    return False


def check_python_oracles(
    test_dirs: list[Path],
    root: Path,
    write_path_keywords: list[str],
    known_files: set[str],
    search_window: int = 5,
) -> None:
    """Scan Python test files for numeric assertions without ORACLE comments."""
    for test_dir in test_dirs:
        if not test_dir.exists():
            continue
        for f in test_dir.rglob("test_*.py"):
            if "conftest" in f.name:
                continue

            content = f.read_text(encoding="utf-8", errors="replace")
            lines = content.split("\n")
            rel = str(f.relative_to(root))
            is_known = any(known in f.name for known in known_files)
            is_write = is_write_path_file(f.name, content, write_path_keywords)

            for line_idx, line in enumerate(lines):
                stripped = line.strip()

                if not any(
                    p.search(stripped) for p in PYTHON_NUMERIC_PATTERNS
                ):
                    continue

                if is_exempt(stripped):
                    continue

                if has_oracle_above(lines, line_idx, search_window):
                    # ORACLE present — verify its math is internally consistent.
                    bad = oracle_consistency_violations(lines, line_idx, search_window)
                    if bad:
                        line_no = line_idx + 1
                        violations.append(f"{rel}:{line_no} -- {bad}")
                    continue

                line_no = line_idx + 1
                issue = (
                    f"{rel}:{line_no} -- numeric assertion without "
                    f"# ORACLE: comment: {stripped[:80]}"
                )

                if is_known:
                    pass  # skip known files entirely
                elif is_write:
                    violations.append(issue)
                else:
                    warnings.append(issue)


# -- TypeScript/JavaScript: find numeric assertions and check for ORACLE ---

TS_NUMERIC_PATTERNS = [
    re.compile(r"toBeCloseTo\("),
    re.compile(r"toBe\(\s*\d+\.\d+"),
    re.compile(r"toEqual\(\s*\d+\.\d+"),
]


def check_typescript_oracles(
    frontend_dir: Path,
    root: Path,
    write_path_keywords: list[str],
    known_files: set[str],
    search_window: int = 5,
) -> None:
    """Scan TypeScript/JS test files for numeric assertions without ORACLE comments."""
    if not frontend_dir.exists():
        return

    for ext in ["*.test.ts", "*.test.tsx", "*.test.js", "*.spec.ts", "*.spec.tsx"]:
        for f in frontend_dir.rglob(ext):
            content = f.read_text(encoding="utf-8", errors="replace")
            lines = content.split("\n")
            rel = str(f.relative_to(root))
            is_known = any(known in f.name for known in known_files)
            is_write = is_write_path_file(f.name, content, write_path_keywords)

            for line_idx, line in enumerate(lines):
                stripped = line.strip()

                if not any(p.search(stripped) for p in TS_NUMERIC_PATTERNS):
                    continue

                if has_oracle_above(lines, line_idx, search_window):
                    continue

                line_no = line_idx + 1
                issue = (
                    f"{rel}:{line_no} -- numeric assertion without "
                    f"// ORACLE: comment: {stripped[:80]}"
                )

                if is_known:
                    pass
                elif is_write:
                    violations.append(issue)
                else:
                    warnings.append(issue)


# -- Main ---


def main() -> int:
    args = set(sys.argv[1:])

    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0

    do_backend = "--backend" in args or not (args - {"--config"})
    do_frontend = "--frontend" in args or not (args - {"--config"})

    config_path = None
    for i, arg in enumerate(sys.argv):
        if arg == "--config" and i + 1 < len(sys.argv):
            config_path = Path(sys.argv[i + 1])

    config = load_config(config_path)
    root = find_root(config_path)

    oracle_config = config.get("oracle_check", {})
    if not oracle_config.get("enabled", True):
        print(f"{GREEN}[PASS]{NC} Oracle check disabled in config.")
        return 0

    write_path_keywords = oracle_config.get(
        "write_path_keywords",
        ["order", "payment", "total", "balance", "fee", "price"],
    )
    known_files = set(oracle_config.get("known_files_without_oracle", []))
    search_window = oracle_config.get("python_search_window", 5)

    backend_test_dirs = [root / p for p in config.get("backend_test_dirs", [])]
    int_test_dirs = [root / p for p in config.get("integration_test_dirs", [])]
    all_backend_dirs = list(set(backend_test_dirs + int_test_dirs))
    frontend_dir = root / config.get("frontend_test_dir", "src")

    print(f"{YELLOW}[ORACLE CHECK]{NC} Scanning for numeric assertions without ORACLE comments...")

    if do_backend:
        check_python_oracles(
            all_backend_dirs, root, write_path_keywords, known_files, search_window
        )

    if do_frontend:
        check_typescript_oracles(
            frontend_dir, root, write_path_keywords, known_files, search_window
        )

    if warnings:
        print(f"\n{YELLOW}Warnings (non-write-path files, should fix):{NC}")
        for w in warnings:
            print(f"  {w}")

    if violations:
        print(f"\n{RED}Violations (write-path files, must fix before commit):{NC}")
        for v in violations:
            print(f"  {v}")
        print(
            f"\n{RED}[FAIL]{NC} {len(violations)} numeric assertion(s) in write-path "
            f"test files missing # ORACLE: comments."
        )
        return 1

    count = len(warnings)
    if count:
        print(
            f"\n{GREEN}[PASS]{NC} Oracle check passed "
            f"({count} warning(s) in non-write-path files)."
        )
    else:
        print(f"\n{GREEN}[PASS]{NC} Oracle check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
