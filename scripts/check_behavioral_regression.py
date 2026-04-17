#!/usr/bin/env python3
"""check_behavioral_regression.py — replay Playwright tests of validated stories.

Reads `_work/build/interactions-registry.yaml` (produced by
generate-interaction-tests.py and /build pipeline), then replays every
.spec.ts it lists via a user-provided Playwright run command. Runs 3
consecutive times and requires 100% pass; any flake is treated as a fail.

Exit: 0 pass, 1 fail, 2 config error.
"""
from __future__ import annotations

import argparse
import subprocess
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run-cmd", required=True, help="Playwright run command (accepts SPEC env var)")
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()

    if yaml is None:
        fail("G9.6", "PyYAML required", fix="pip install pyyaml")
        return 2
    root = find_root()
    registry = root / "_work" / "build" / "interactions-registry.yaml"
    if not registry.exists():
        warn(f"no {registry.relative_to(root)} — no validated interactions to replay")
        return 0
    data = yaml.safe_load(registry.read_text()) or {}
    specs: list[str] = []
    for sid, entry in (data.get("stories", {}) or {}).items():
        for s in entry.get("specs", []) or []:
            specs.append(s)
    if not specs:
        success("G9.6", "no interaction specs registered — nothing to replay")
        return 0
    info(f"replaying {len(specs)} spec(s), {args.runs} runs each")
    for run_i in range(1, args.runs + 1):
        for spec in specs:
            env_cmd = f"SPEC='{spec}' {args.run_cmd}"
            r = subprocess.run(env_cmd, shell=True, cwd=root)
            if r.returncode != 0:
                fail("G9.6", f"spec {spec} failed on run {run_i}/{args.runs}",
                     fix="restore the broken interaction or update the spec if intent changed")
                return 1
    success("G9.6", f"{len(specs)} spec(s) passed {args.runs} consecutive runs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
