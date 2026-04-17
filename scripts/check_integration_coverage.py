#!/usr/bin/env python3
"""check_integration_coverage.py — cross-story integration tests.

When the current story touches a module that is already registered as
"validated" in `_work/build/test-registry.yaml`, the story's manifest
MUST declare a cross-story integration test under `integration_tests:`.

Usage:
    python3 check_integration_coverage.py --story sc-0014
Exit: 0 pass, 1 fail, 2 config error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ui_messages import fail, success, info, warn  # noqa: E402

try:
    import yaml
except ImportError:
    yaml = None


def find_root() -> Path:
    here = Path(__file__).resolve().parent
    for p in [here] + list(here.parents):
        if (p / ".git").exists():
            return p
    return Path.cwd()


def load_registry(root: Path) -> dict:
    path = root / "_work" / "build" / "test-registry.yaml"
    if not path.exists() or yaml is None:
        return {}
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def load_story_manifest(root: Path, story_id: str) -> dict | None:
    if yaml is None:
        return None
    candidates = [
        root / "specs" / "stories" / f"{story_id}-manifest.yaml",
        root / "specs" / "stories" / f"{story_id}.manifest.yaml",
    ]
    for c in candidates:
        if c.exists():
            try:
                return yaml.safe_load(c.read_text()) or {}
            except Exception:
                return None
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--story", required=True)
    args = ap.parse_args()

    root = find_root()
    manifest = load_story_manifest(root, args.story)
    if manifest is None:
        warn(f"no manifest for {args.story} — skipping integration coverage check")
        return 0
    touched = set(manifest.get("scope", {}).get("files", []) or manifest.get("files", []))
    registry = load_registry(root)
    validated_modules = set()
    for sid, entry in (registry.get("stories", {}) or {}).items():
        if sid == args.story:
            continue
        for m in entry.get("modules", []) or []:
            validated_modules.add(m)
    overlap = [f for f in touched if any(f.startswith(m) or m.startswith(f) for m in validated_modules)]
    if not overlap:
        success("G8", "no overlap with validated modules — no cross-story test required")
        return 0
    declared = manifest.get("integration_tests", [])
    if not declared:
        fail(
            "G8",
            f"story touches validated modules {overlap} but declares no integration_tests",
            fix=f"add an integration_tests: entry in specs/stories/{args.story}-manifest.yaml",
        )
        return 1
    info(f"integration tests declared: {len(declared)}")
    success("G8", f"cross-story integration test(s) declared for {len(overlap)} overlap(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
