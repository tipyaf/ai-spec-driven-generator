#!/usr/bin/env python3
"""
Code review hook -- reads hook-config.json and checks staged files.

Runs anti-pattern detection against git-staged files using configurable
rules from hook-config.json. Supports severity levels (error vs warning),
project-type filtering, glob-based file matching, and auto-restage.

Usage:
  python3 code_review.py                    # Check all universal rules
  python3 code_review.py --project-type web # Also run web_specific rules
  python3 code_review.py --config path.json # Custom config path
  python3 code_review.py --all-files        # Check all files, not just staged
"""

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ── constants ────────────────────────────────────────────────────────────────

DEFAULT_TIMEOUT = 30
DEFAULT_SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "_cache", "_archive",
    ".venv", "venv", "dist", ".next", "build", "target", ".idea",
}

# Map CLI --project-type values to config section names
PROJECT_TYPE_SECTIONS = {
    "web": "web_specific",
    "web-app": "web_specific",
    "fullstack": "web_specific",
    "api": "api_specific",
    "cli": "cli_specific",
    "desktop": "cli_specific",
}


# ── config loading ───────────────────────────────────────────────────────────


def find_repo_root() -> Path:
    """Walk up from cwd to find the git repo root."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return Path.cwd()


def load_config(config_path: Optional[str] = None) -> dict:
    """
    Load hook-config.json. Searches in order:
    1. Explicit --config path
    2. ./hook-config.json (same directory as this script)
    3. <repo-root>/hook-config.json
    Returns empty dict if not found.
    """
    candidates = []
    if config_path:
        candidates.append(Path(config_path))
    candidates.append(Path(__file__).resolve().parent / "hook-config.json")
    candidates.append(find_repo_root() / "hook-config.json")

    for path in candidates:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return data
            except (json.JSONDecodeError, OSError) as exc:
                print(f"Warning: failed to parse {path}: {exc}", file=sys.stderr)
                return {}

    return {}


# ── file discovery ───────────────────────────────────────────────────────────


def get_staged_files() -> list[str]:
    """Return list of staged file paths (relative to repo root)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return []
        return [
            line.strip() for line in result.stdout.splitlines()
            if line.strip()
        ]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def get_all_tracked_files() -> list[str]:
    """Return all tracked files (for --all-files mode)."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return []
        return [
            line.strip() for line in result.stdout.splitlines()
            if line.strip()
        ]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def expand_brace_glob(pattern: str) -> list[str]:
    """
    Expand brace syntax like '*.{ts,tsx,js}' into ['*.ts', '*.tsx', '*.js'].
    Also handles simple globs like '*.py' (returns as-is in a list).
    """
    match = re.match(r'^(.*)\{([^}]+)\}(.*)$', pattern)
    if match:
        prefix, alternatives, suffix = match.groups()
        return [f"{prefix}{alt.strip()}{suffix}" for alt in alternatives.split(",")]
    return [pattern]


def filter_files(files: list[str], pattern: str) -> list[str]:
    """
    Filter file paths by glob pattern. Supports brace expansion
    (e.g., '*.{ts,tsx,js}') and multi-segment paths.
    """
    expanded = expand_brace_glob(pattern)
    result = []
    for filepath in files:
        name = Path(filepath).name
        if any(fnmatch.fnmatch(name, p) for p in expanded):
            # Skip files in default skip directories
            parts = Path(filepath).parts
            if not any(part in DEFAULT_SKIP_DIRS for part in parts):
                result.append(filepath)
    return result


# ── rule collection ──────────────────────────────────────────────────────────


def collect_rules(config: dict, project_type: Optional[str] = None) -> list[dict]:
    """
    Collect applicable rules from config based on project type.
    Universal rules always apply. Type-specific rules apply when
    --project-type matches.
    """
    anti_patterns = config.get("anti_patterns", {})
    rules = list(anti_patterns.get("rules", []))

    if project_type:
        # Determine which sections to include
        sections_to_check = set()

        # Direct mapping from CLI arg
        section = PROJECT_TYPE_SECTIONS.get(project_type)
        if section:
            sections_to_check.add(section)

        # Also check all type-specific sections for applies_to matches
        for section_name in ["web_specific", "api_specific", "cli_specific"]:
            section_rules = anti_patterns.get(section_name, [])
            for rule in section_rules:
                applies_to = rule.get("applies_to", [])
                if project_type in applies_to:
                    rules.append(rule)
                elif section_name in sections_to_check and not applies_to:
                    rules.append(rule)

        # If we matched a section directly, add rules from it that
        # were not already added via applies_to
        if sections_to_check:
            for section_name in sections_to_check:
                section_rules = anti_patterns.get(section_name, [])
                for rule in section_rules:
                    if rule not in rules:
                        applies_to = rule.get("applies_to", [])
                        if not applies_to or project_type in applies_to:
                            rules.append(rule)

    return rules


# ── rule checking ────────────────────────────────────────────────────────────


def check_rule(rule: dict, files: list[str]) -> tuple[bool, list[str]]:
    """
    Run a single anti-pattern rule against the given files.
    Returns (passed, violations) where violations is a list of
    'filepath:line: matched_text' strings.
    """
    name = rule.get("name", "unnamed")
    patterns = rule.get("patterns", [])
    file_filter = rule.get("filter", "*")

    if not patterns:
        return True, []

    matched_files = filter_files(files, file_filter)
    if not matched_files:
        return True, []

    violations = []
    combined_pattern = "|".join(patterns)

    for filepath in matched_files:
        path = Path(filepath)
        if not path.exists():
            # Try relative to repo root
            root = find_repo_root()
            path = root / filepath
            if not path.exists():
                continue

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for line_num, line in enumerate(content.splitlines(), start=1):
            if re.search(combined_pattern, line):
                # Trim the line for display
                trimmed = line.strip()
                if len(trimmed) > 120:
                    trimmed = trimmed[:117] + "..."
                violations.append(f"   {filepath}:{line_num}: {trimmed}")

    passed = len(violations) == 0
    return passed, violations


# ── auto-restage ─────────────────────────────────────────────────────────────


def restage_files(files: list[str]) -> None:
    """Re-add files to the git staging area."""
    if not files:
        return
    try:
        subprocess.run(
            ["git", "add"] + files,
            capture_output=True, text=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


# ── external command checks ──────────────────────────────────────────────────


def run_command_check(
    check: dict, files: list[str], timeout: int = DEFAULT_TIMEOUT
) -> tuple[bool, str]:
    """
    Run an external command check (from hook_commands or custom checks).
    Returns (passed, output).
    """
    cmd = check.get("cmd", "")
    if not cmd:
        return True, ""

    file_filter = check.get("filter")
    matched = filter_files(files, file_filter) if file_filter else files

    if "{files}" in cmd:
        if not matched:
            return True, ""
        cmd = cmd.replace("{files}", " ".join(matched))

    check_timeout = check.get("timeout", timeout)

    try:
        result = subprocess.run(
            cmd, shell=True,
            capture_output=True, text=True,
            timeout=check_timeout,
            cwd=str(find_repo_root()),
        )
        output = (result.stdout + result.stderr).strip()
        passed = result.returncode == 0

        if check.get("auto_restage") and passed and matched:
            restage_files(matched)

        return passed, output
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {check_timeout}s"
    except FileNotFoundError:
        return False, f"Command not found: {cmd.split()[0]}"


# ── reporting ────────────────────────────────────────────────────────────────


def print_report(results: list[dict]) -> bool:
    """
    Print formatted results. Returns True if all errors passed.
    """
    print("\n\U0001f50d Running quality checks...\n")

    error_count = 0
    warning_count = 0
    pass_count = 0

    for r in results:
        name = r["name"]
        passed = r["passed"]
        severity = r["severity"]
        violations = r.get("violations", [])
        file_count = r.get("file_count", 0)

        if passed:
            pass_count += 1
            print(f"\u2705 {name}: clean (checked {file_count} files)")
        elif severity == "error":
            error_count += 1
            print(f"\u274c {name}: FAIL ({len(violations)} violations)")
            for v in violations[:20]:
                print(v)
            if len(violations) > 20:
                print(f"   ... and {len(violations) - 20} more")
        else:
            warning_count += 1
            print(f"\u26a0\ufe0f  {name}: WARNING ({len(violations)} matches)")
            for v in violations[:10]:
                print(v)
            if len(violations) > 10:
                print(f"   ... and {len(violations) - 10} more")

    # Summary
    print("\n" + "\u2501" * 40)

    parts = []
    if error_count > 0:
        parts.append(f"{error_count} error{'s' if error_count != 1 else ''}")
    if warning_count > 0:
        parts.append(f"{warning_count} warning{'s' if warning_count != 1 else ''}")
    if pass_count > 0:
        parts.append(f"{pass_count} passed")

    summary = ", ".join(parts) if parts else "no checks run"

    if error_count > 0:
        print(f"Result: \u274c FAIL ({summary})")
        print("Fix errors before committing.")
    elif warning_count > 0:
        print(f"Result: \u26a0\ufe0f  PASS with warnings ({summary})")
    else:
        print(f"Result: \u2705 PASS ({summary})")

    print()
    return error_count == 0


# ── main ─────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run quality checks on staged files using hook-config.json."
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to hook-config.json (default: auto-detect)",
        default=None,
    )
    parser.add_argument(
        "--project-type", "-p",
        help="Project type for filtering rules (e.g., web, api, cli, fullstack)",
        default=None,
    )
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Check all tracked files, not just staged ones",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Default timeout per command in seconds (default: {DEFAULT_TIMEOUT})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Load configuration
    config = load_config(args.config)
    if not config:
        print("No hook-config.json found. Nothing to check.", file=sys.stderr)
        sys.exit(0)

    # Get files to check
    if args.all_files:
        files = get_all_tracked_files()
    else:
        files = get_staged_files()

    if not files:
        print("No staged files to check.", file=sys.stderr)
        sys.exit(0)

    # Collect applicable rules
    rules = collect_rules(config, args.project_type)
    if not rules:
        print("No rules configured for this project type.", file=sys.stderr)
        sys.exit(0)

    # Run checks
    results = []
    for rule in rules:
        name = rule.get("name", "unnamed")
        severity = rule.get("severity", "error")
        file_filter = rule.get("filter", "*")
        matched_files = filter_files(files, file_filter)

        passed, violations = check_rule(rule, files)

        results.append({
            "name": name,
            "severity": severity,
            "passed": passed,
            "violations": violations,
            "file_count": len(matched_files),
            "message": rule.get("message", ""),
        })

    # Also run any external command checks if present
    for check in config.get("checks", []):
        name = check.get("name", "unnamed")
        severity = check.get("severity", "error")
        passed, output = run_command_check(check, files, args.timeout)

        violations = []
        if not passed and output:
            violations = [f"   {line}" for line in output.splitlines()[:30]]

        results.append({
            "name": name,
            "severity": severity,
            "passed": passed,
            "violations": violations,
            "file_count": len(files),
            "message": check.get("message", ""),
        })

    # Print report and exit
    all_errors_passed = print_report(results)
    sys.exit(0 if all_errors_passed else 1)


if __name__ == "__main__":
    main()
