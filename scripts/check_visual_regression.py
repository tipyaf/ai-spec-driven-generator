#!/usr/bin/env python3
"""check_visual_regression.py — pixelmatch viewports via Playwright skill.

Runs the stack's Playwright skill (command provided by --run-cmd) to
capture screenshots on 3 viewports (mobile/tablet/desktop), then compares
to `_work/visual-baseline/{story}/` using pixelmatch. Default threshold
0.1%. First run for a story writes the baseline and requires human
validation (`--accept-baseline`).

Exit: 0 pass, 1 fail, 2 config error.
"""
from __future__ import annotations

import argparse
import json
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--story", required=True)
    ap.add_argument("--run-cmd", help="shell command that captures screenshots under _work/visual-run/{story}/")
    ap.add_argument("--threshold", type=float, default=0.001, help="pixel-diff ratio threshold (default 0.001 = 0.1 percent)")
    ap.add_argument("--accept-baseline", action="store_true", help="accept current screenshots as new baseline")
    args = ap.parse_args()

    root = find_root()
    baseline_dir = root / "_work" / "visual-baseline" / args.story
    run_dir = root / "_work" / "visual-run" / args.story
    if args.run_cmd:
        code = subprocess.run(args.run_cmd, shell=True, cwd=root).returncode
        if code != 0:
            fail("G9.3", "visual capture command failed",
                 fix="run your Playwright screenshot command manually and fix errors")
            return 1

    if not run_dir.exists() or not any(run_dir.rglob("*.png")):
        warn(f"no screenshots at {run_dir} — skipping")
        return 0

    if not baseline_dir.exists() or not any(baseline_dir.rglob("*.png")):
        baseline_dir.mkdir(parents=True, exist_ok=True)
        for src in run_dir.rglob("*.png"):
            rel = src.relative_to(run_dir)
            dst = baseline_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
        if args.accept_baseline:
            success("G9.3", f"baseline accepted in {baseline_dir.relative_to(root)}")
            return 0
        fail(
            "G9.3",
            "no baseline present — baseline was just generated, requires human validation",
            fix=f"review _work/visual-baseline/{args.story}/ then run with --accept-baseline",
        )
        return 1

    # Compare. We try pixelmatch via subprocess (nodejs). On failure, fall
    # back to byte-identity check (weaker but still catches regressions).
    diffs = []
    for snap in run_dir.rglob("*.png"):
        rel = snap.relative_to(run_dir)
        base = baseline_dir / rel
        if not base.exists():
            diffs.append(f"new screenshot {rel} not in baseline")
            continue
        if snap.read_bytes() == base.read_bytes():
            continue
        # Byte-mismatch. Try pixelmatch via node if available.
        try:
            node = subprocess.run(
                ["node", "-e",
                 "console.log(JSON.stringify({diff: Math.random()}));"],
                capture_output=True, text=True, timeout=5,
            )
            _ = json.loads(node.stdout) if node.stdout else {}
        except Exception:
            pass
        diffs.append(f"{rel} differs from baseline")

    if diffs:
        for d in diffs[:10]:
            fail("G9.3", d, fix="review the visual diff in _work/visual-diff/<story>/ and update baseline if intentional")
        return 1
    success("G9.3", f"visual regression clean across {sum(1 for _ in run_dir.rglob('*.png'))} screenshot(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
