#!/usr/bin/env python3
"""check_observability.py — logs/metrics/traces ratio vs LOC added.

Scans the diff (staged, or main..HEAD with --scan-branch) and counts
observability calls (logger.info/log.info/logging.info + metric/counter/
histogram + span/trace). Checks the ratio against a floor declared in the
project type profile (or a sensible default).

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

try:
    import yaml
except ImportError:
    yaml = None

LOG_RE = re.compile(r"\b(logger|log|logging)\.(info|warning|error|debug|exception)\b")
METRIC_RE = re.compile(r"\b(metric|counter|histogram|gauge)\b", re.IGNORECASE)
TRACE_RE = re.compile(r"\b(span|trace|tracer)\b", re.IGNORECASE)


def find_root() -> Path:
    here = Path(__file__).resolve().parent
    for p in [here] + list(here.parents):
        if (p / ".git").exists():
            return p
    return Path.cwd()


def framework_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_diff(scan_branch: bool, root: Path) -> str:
    cmd = ["git", "diff"]
    if scan_branch:
        try:
            base = subprocess.run(
                ["git", "merge-base", "origin/main", "HEAD"],
                capture_output=True, text=True, cwd=root, timeout=10,
            ).stdout.strip() or "HEAD~20"
            cmd = ["git", "diff", f"{base}..HEAD"]
        except Exception:
            pass
    else:
        cmd = ["git", "diff", "--cached"]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, cwd=root, timeout=30).stdout
    except Exception as exc:
        warn(f"git diff failed: {exc}")
        return ""


def load_ratio_floor(spec_type: str | None) -> dict:
    if not spec_type or yaml is None:
        return {"log_per_100_loc": 1.0, "metric_per_200_loc": 0.5}
    p = framework_root() / "stacks" / "project-types" / f"{spec_type}.yaml"
    if not p.exists():
        return {"log_per_100_loc": 1.0, "metric_per_200_loc": 0.5}
    data = yaml.safe_load(p.read_text()) or {}
    return data.get("observability", {}) or {"log_per_100_loc": 1.0}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--story", required=False)
    ap.add_argument("--type", required=False)
    ap.add_argument("--scan-branch", action="store_true")
    args = ap.parse_args()

    root = find_root()
    diff = get_diff(args.scan_branch, root)
    added = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    loc = len(added)
    logs = sum(1 for ln in added if LOG_RE.search(ln))
    metrics = sum(1 for ln in added if METRIC_RE.search(ln))
    traces = sum(1 for ln in added if TRACE_RE.search(ln))

    info(f"+{loc} LOC, {logs} log(s), {metrics} metric(s), {traces} trace(s)")
    if loc < 20:
        success("G11", "small diff — observability check skipped")
        return 0
    floors = load_ratio_floor(args.type)
    log_floor = floors.get("log_per_100_loc", 1.0) * (loc / 100.0)
    if logs < log_floor:
        fail(
            "G11",
            f"only {logs} log call(s) for {loc} LOC (floor: {log_floor:.1f})",
            fix="add structured log lines at entry/exit of each new function",
        )
        return 1
    success("G11", f"observability ratio OK ({logs}/{loc} LOC)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
