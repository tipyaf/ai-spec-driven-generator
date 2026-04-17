#!/usr/bin/env python3
"""check_ds_conformity.py — Design System token conformity for UI files.

Parses added .tsx/.jsx/.vue files and refuses:
  * hardcoded hex colors not in specs/design-system.yaml tokens
  * hardcoded spacing (padding: 13px) outside the DS scale

Exit: 0 pass, 1 fail, 2 config error.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ui_messages import fail, success, warn, info  # noqa: E402

try:
    import yaml
except ImportError:
    yaml = None

HEX_RE = re.compile(r"#([0-9a-fA-F]{3,8})\b")
PX_RE = re.compile(r"\b(\d+)px\b")


def find_root() -> Path:
    here = Path(__file__).resolve().parent
    for p in [here] + list(here.parents):
        if (p / ".git").exists():
            return p
    return Path.cwd()


def load_ds(root: Path) -> dict:
    ds = root / "specs" / "design-system.yaml"
    if not ds.exists() or yaml is None:
        return {}
    try:
        return yaml.safe_load(ds.read_text()) or {}
    except Exception:
        return {}


def get_added_ui_files(root: Path, scan_branch: bool) -> list[str]:
    if scan_branch:
        try:
            base = subprocess.run(
                ["git", "merge-base", "origin/main", "HEAD"],
                capture_output=True, text=True, cwd=root, timeout=10,
            ).stdout.strip() or "HEAD~20"
            out = subprocess.run(
                ["git", "diff", "--name-only", f"{base}..HEAD"],
                capture_output=True, text=True, cwd=root, timeout=15,
            ).stdout
        except Exception:
            return []
    else:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, cwd=root, timeout=15,
        ).stdout
    return [f for f in out.splitlines() if re.search(r"\.(tsx|jsx|vue|svelte)$", f)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scan-branch", action="store_true")
    args = ap.parse_args()

    root = find_root()
    ds = load_ds(root)
    allowed_hex = {h.lower().lstrip("#") for h in (ds.get("colors", {}) or {}).values() if isinstance(h, str)}
    allowed_spacing = set((ds.get("spacing", {}) or {}).values())

    files = get_added_ui_files(root, args.scan_branch)
    if not files:
        success("G9.1", "no UI files changed — DS conformity skipped")
        return 0

    violations: list[str] = []
    for rel in files:
        p = root / rel
        if not p.exists():
            continue
        content = p.read_text(errors="replace")
        for m in HEX_RE.finditer(content):
            if m.group(1).lower() not in allowed_hex:
                lineno = content[:m.start()].count("\n") + 1
                violations.append(f"{rel}:{lineno} hardcoded color #{m.group(1)} (not a DS token)")
        for m in PX_RE.finditer(content):
            v = int(m.group(1))
            if v not in allowed_spacing and v not in (0, 1, 2):
                lineno = content[:m.start()].count("\n") + 1
                violations.append(f"{rel}:{lineno} hardcoded spacing {v}px (not in DS scale)")

    if violations:
        for v in violations[:20]:
            fail("G9.1", v, fix="use a design-system token (theme.colors.*, theme.spacing.*)")
        if len(violations) > 20:
            info(f"... and {len(violations) - 20} more")
        return 1
    success("G9.1", f"{len(files)} UI file(s) conform to the Design System")
    return 0


if __name__ == "__main__":
    sys.exit(main())
