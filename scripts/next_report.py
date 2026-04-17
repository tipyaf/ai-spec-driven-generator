#!/usr/bin/env python3
"""next_report.py — /next priority report generator.

Aggregates signals from:
  * specs/feature-tracker.yaml (story statuses)
  * _work/build/*.yaml (gate results, escalations, tamper flags)
  * _work/perf-baseline/ (perf drift)
  * memory/LESSONS.md (unread lessons)
  * git status / git log / gh pr list
Then prints 5 sections: BLOCKING, IN PROGRESS, READY, PENDING SHIP,
SUGGESTIONS. `--json` prints a machine-readable document.

Exit: always 0 (informational). Use --strict to exit 1 on blockers.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ui_messages import header, info, warn, fail, success, next_step  # noqa: E402

try:
    import yaml
except ImportError:
    yaml = None


def find_root() -> Path:
    # Honour SDD_PROJECT_ROOT first (same convention as orchestrator.py) so that
    # /next can be invoked against any project, not just the framework repo it
    # lives in. Fall back to the CWD, then to the nearest .git ancestor.
    env_root = os.environ.get("SDD_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    cwd = Path.cwd()
    if (cwd / "specs" / "feature-tracker.yaml").exists():
        return cwd
    here = Path(__file__).resolve().parent
    for p in [here] + list(here.parents):
        if (p / ".git").exists():
            return p
    return cwd


def run(cmd: list[str], cwd: Path) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=15).stdout
    except Exception:
        return ""


def load_yaml(p: Path) -> dict:
    if yaml is None or not p.exists():
        return {}
    try:
        return yaml.safe_load(p.read_text()) or {}
    except Exception:
        return {}


def collect(root: Path) -> dict:
    tracker = load_yaml(root / "specs" / "feature-tracker.yaml")
    stories = {s.get("id"): s for s in tracker.get("features", []) or [] if isinstance(s, dict)}
    build_files = list((root / "_work" / "build").glob("sc-*.yaml"))
    builds = {f.stem: load_yaml(f) for f in build_files}

    blocking, in_progress, ready, pending_ship, suggestions = [], [], [], [], []
    for sid, story in stories.items():
        status = (story.get("status") or "").lower()
        if status in {"escalated", "tampered"}:
            blocking.append({"id": sid, "reason": status, "cmd": f"/resume {sid} \"reason...\""})
        elif status == "building" or status == "testing":
            in_progress.append({"id": sid, "cmd": f"/build {sid}"})
        elif status == "refined":
            ready.append({"id": sid, "cmd": f"/build {sid}"})
        elif status == "validated":
            pending_ship.append({"id": sid, "cmd": f"/ship {sid}"})

    lessons = root / "memory" / "LESSONS.md"
    if lessons.exists() and lessons.stat().st_size > 0:
        suggestions.append({"text": "unread LESSONS.md entries", "cmd": "less memory/LESSONS.md"})
    if (root / "_work" / "perf-baseline").exists():
        perf_dir = root / "_work" / "perf-baseline"
        if len(list(perf_dir.glob("*.json"))) > 0 and (root / "_work" / "perf").exists():
            suggestions.append({"text": "compare latest perf vs baseline", "cmd": "/review"})
    return {
        "blocking": blocking,
        "in_progress": in_progress,
        "ready": ready,
        "pending_ship": pending_ship,
        "suggestions": suggestions,
    }


def render_human(data: dict, scope: str | None) -> None:
    sections = [
        ("BLOCKING", "blocking"),
        ("IN PROGRESS", "in_progress"),
        ("READY", "ready"),
        ("PENDING SHIP", "pending_ship"),
        ("SUGGESTIONS", "suggestions"),
    ]
    if scope:
        sections = [(label, key) for label, key in sections if key == scope.replace("-", "_")]
    for label, key in sections:
        items = data[key]
        header(f"{label} ({len(items)})")
        if not items:
            info("  (none)")
            continue
        for item in items:
            sid = item.get("id", "")
            text = item.get("text", item.get("reason", ""))
            cmd = item.get("cmd", "")
            line = f"  • {sid}  {text}".strip()
            info(line)
            if cmd:
                next_step(cmd)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--scope", choices=["blocked", "blocking", "in-progress", "ready", "ship", "suggestions"])
    ap.add_argument("--strict", action="store_true", help="exit 1 when there are blockers")
    args = ap.parse_args()

    root = find_root()
    data = collect(root)
    scope_map = {"blocked": "blocking", "ship": "pending_ship"}
    scope_key = scope_map.get(args.scope, args.scope)
    if scope_key:
        # Normalise kebab-case to snake_case for dict lookup.
        scope_key = scope_key.replace("-", "_")
    # Strict mode inspects blockers BEFORE any scope filtering, because
    # `--scope ready --strict` should still fail on a hidden blocker.
    has_blockers = bool(data["blocking"])
    if scope_key:
        # Filter every other section to empty so JSON and human output agree.
        for key in ("blocking", "in_progress", "ready", "pending_ship", "suggestions"):
            if key != scope_key:
                data[key] = []
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        render_human(data, scope_key)
    if args.strict and has_blockers:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
