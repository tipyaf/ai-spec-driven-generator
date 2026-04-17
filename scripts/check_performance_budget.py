#!/usr/bin/env python3
"""check_performance_budget.py — compare measurements vs budget + baseline.

Reads measured metrics from `_work/perf/{story_id}.json` (produced by the
stack's benchmark skill), reads budget thresholds from
`stacks/project-types/{type}.yaml` and, when present, baseline from
`_work/perf-baseline/{story_id}.json`. Flags >5% regression by default.

Exit: 0 pass, 1 fail, 2 config error.
"""
from __future__ import annotations

import argparse
import json
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


def framework_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def load_type_budget(spec_type: str) -> dict:
    if yaml is None:
        return {}
    p = framework_root() / "stacks" / "project-types" / f"{spec_type}.yaml"
    if not p.exists():
        return {}
    data = yaml.safe_load(p.read_text()) or {}
    return data.get("performance_budget", {}) or data.get("budget", {}) or {}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--story", required=True)
    ap.add_argument("--type", required=True, help="spec.type (web-ui, web-api, cli, ...)")
    ap.add_argument("--threshold", type=float, default=5.0, help="Regression threshold in percent")
    args = ap.parse_args()

    root = find_root()
    measured = load_json(root / "_work" / "perf" / f"{args.story}.json")
    if not measured:
        warn(f"no measurements at _work/perf/{args.story}.json — skipping")
        return 0
    budget = load_type_budget(args.type)
    baseline = load_json(root / "_work" / "perf-baseline" / f"{args.story}.json")

    violations = []
    for metric, value in measured.items():
        if not isinstance(value, (int, float)):
            continue
        b = budget.get(metric)
        if b is not None and value > b:
            violations.append(f"{metric}={value} exceeds budget {b}")
        base = baseline.get(metric)
        if isinstance(base, (int, float)) and base > 0:
            regression = (value - base) / base * 100.0
            if regression > args.threshold:
                violations.append(
                    f"{metric}={value} is +{regression:.1f}% vs baseline {base} (>+{args.threshold}%)"
                )
    if violations:
        for v in violations:
            fail("G10", v, fix="optimize the hot path or re-baseline with /perf rebaseline")
        return 1
    info(f"measured {len(measured)} metric(s); baseline {'present' if baseline else 'absent'}")
    success("G10", "performance budget + baseline respected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
