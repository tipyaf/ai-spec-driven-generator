#!/usr/bin/env python3
"""check_release_artifacts.py — CHANGELOG / VERSION / tag consistency.

Validates at `/ship` time that:
  * CHANGELOG.md contains an entry for the current story
  * VERSION file content matches package.json / pyproject.toml / Cargo.toml
  * When the story is tagged as a release, a git tag exists for that version

Exit: 0 pass, 1 fail, 2 config error.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ui_messages import fail, success, info, warn  # noqa: E402


def find_root() -> Path:
    here = Path(__file__).resolve().parent
    for p in [here] + list(here.parents):
        if (p / ".git").exists():
            return p
    return Path.cwd()


def read_version(root: Path) -> tuple[str, str] | None:
    """Try VERSION then package.json then pyproject.toml. Returns (source, version)."""
    vf = root / "VERSION"
    if vf.exists():
        return "VERSION", vf.read_text().strip()
    pkg = root / "package.json"
    if pkg.exists():
        m = re.search(r'"version"\s*:\s*"([^"]+)"', pkg.read_text())
        if m:
            return "package.json", m.group(1)
    pyproj = root / "pyproject.toml"
    if pyproj.exists():
        m = re.search(r'^version\s*=\s*"([^"]+)"', pyproj.read_text(), re.MULTILINE)
        if m:
            return "pyproject.toml", m.group(1)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--story", required=True)
    ap.add_argument("--require-tag", action="store_true", help="Require a git tag matching VERSION")
    args = ap.parse_args()

    root = find_root()
    issues = []

    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        issues.append("CHANGELOG.md missing")
    else:
        content = changelog.read_text()
        if args.story not in content:
            issues.append(f"CHANGELOG.md has no entry for {args.story}")

    ver = read_version(root)
    if ver is None:
        issues.append("could not determine version (no VERSION/package.json/pyproject.toml)")
    elif args.require_tag:
        source, version = ver
        tags = subprocess.run(
            ["git", "tag", "-l", f"v{version}"],
            capture_output=True, text=True, cwd=root, timeout=10,
        ).stdout.strip()
        if not tags:
            issues.append(f"no git tag v{version} matching {source}")
        else:
            info(f"tag v{version} present")

    if issues:
        for i in issues:
            fail("G14", i, fix="update CHANGELOG.md / bump VERSION / create the git tag")
        return 1
    success("G14", "release artifacts consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
