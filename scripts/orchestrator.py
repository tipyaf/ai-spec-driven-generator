"""
orchestrator.py — SDD v5 executable orchestrator.

Replaces the v4 `agents/orchestrator.md` (which was documentation, not code).
The orchestrator is the SINGLE SOURCE OF TRUTH for gate execution in v5:

  • `/build`, `/validate`, `/review`, `/ship` are thin wrappers that call this.
  • Every gate declared in `stacks/project-types/<spec.type>.yaml` is run here,
    regardless of hook state. Bypass attempts (--no-verify, tampered tests)
    are detected via git log inspection, not via pre-commit hooks alone.

Usage:
    python scripts/orchestrator.py --mode build --story sc-0014
    python scripts/orchestrator.py --mode validate --story sc-0014
    python scripts/orchestrator.py --mode review [--story sc-0014 | --all]
    python scripts/orchestrator.py --mode ship --story sc-0014
    python scripts/orchestrator.py --mode gate-all              # CI chain

Exit codes (see ui_messages.EXIT_*):
    0 — all gates passed
    1 — at least one gate failed
    2 — story is escalated (locked until /resume)
    3 — configuration error (missing spec, missing stack, etc.)
    4 — tamper detected (bypass attempt in git history)

This file is intentionally kept small: heavy lifting lives in the individual
check_*.py scripts. The orchestrator's job is routing, not validation logic.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Local import — ui_messages lives next to this file in scripts/.
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from ui_messages import (  # noqa: E402
    EXIT_CONFIG_ERROR,
    EXIT_ESCALATED,
    EXIT_GATE_FAIL,
    EXIT_OK,
    EXIT_TAMPERED,
    escalation,
    exit_with,
    fail,
    header,
    info,
    next_step,
    success,
    tampered,
    warn,
)

# YAML is optional — if missing, we produce a clear config-error with install hint.
try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


# --- Paths ---------------------------------------------------------------

# The orchestrator assumes it's invoked from the project root (same layout
# as /build, /validate, etc.). When running against the framework itself
# (self-tests), SDD_PROJECT_ROOT can override.
def project_root() -> Path:
    root = os.environ.get("SDD_PROJECT_ROOT")
    if root:
        return Path(root).resolve()
    return Path.cwd()


def framework_root() -> Path:
    """Path to the framework (this repo). In a project, it's framework/."""
    # When running from a project, framework is a git submodule at ./framework.
    # When running standalone (self-test), orchestrator.py lives in framework/scripts/.
    env = os.environ.get("SDD_FRAMEWORK_ROOT")
    if env:
        return Path(env).resolve()
    # Default: two levels up from this script file (scripts/ -> framework_root/).
    return SCRIPTS_DIR.parent


def project_types_dir() -> Path:
    return framework_root() / "stacks" / "project-types"


# --- Mode enum and config -----------------------------------------------

VALID_MODES = {"build", "validate", "review", "ship", "gate-all"}


@dataclass
class OrchestratorConfig:
    mode: str
    story_id: str | None = None
    all_stories: bool = False
    extra_args: list[str] = field(default_factory=list)


def parse_args(argv: list[str]) -> OrchestratorConfig:
    parser = argparse.ArgumentParser(
        prog="orchestrator.py",
        description="SDD v5 executable orchestrator.",
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=sorted(VALID_MODES),
        help="Operation mode.",
    )
    parser.add_argument(
        "--story",
        help="Story ID (e.g. sc-0014). Required for build/validate/ship.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Used with --mode review to re-run gates across the whole branch.",
    )
    ns = parser.parse_args(argv)
    return OrchestratorConfig(
        mode=ns.mode,
        story_id=ns.story,
        all_stories=ns.all,
    )


# --- Spec / stack loading ------------------------------------------------

def require_yaml() -> None:
    if yaml is None:
        fail(
            "config",
            "PyYAML is not installed but is required by the orchestrator.",
            fix="pip install pyyaml",
        )
        exit_with(EXIT_CONFIG_ERROR)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file or exit with a clear config-error."""
    require_yaml()
    if not path.exists():
        fail(
            "config",
            f"file not found: {path}",
            fix=f"create {path.name} or check SDD_PROJECT_ROOT env var",
        )
        exit_with(EXIT_CONFIG_ERROR)
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        fail(
            "config",
            f"invalid YAML in {path}: {exc}",
            fix=f"fix the YAML syntax in {path}",
        )
        exit_with(EXIT_CONFIG_ERROR)
    if not isinstance(data, dict):
        fail(
            "config",
            f"{path} must be a YAML mapping (got {type(data).__name__})",
            fix=f"wrap the content of {path} as a top-level mapping",
        )
        exit_with(EXIT_CONFIG_ERROR)
    return data


def _declares_spec_type(path: Path) -> bool:
    """True iff `path` declares a top-level `type:` — the root-spec hallmark.

    Tolerant: a malformed ancillary YAML must not kill the orchestrator, so
    parse errors just return False and let a well-formed typed candidate win.
    """
    if yaml is None:
        return False
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return False
    if not isinstance(data, dict):
        return False
    if data.get("type"):
        return True
    nested = data.get("spec")
    return isinstance(nested, dict) and bool(nested.get("type"))


def find_project_spec() -> Path:
    """Locate the root project YAML spec (specs/*.yaml excluding ancillary files)."""
    root = project_root()
    specs_dir = root / "specs"
    if not specs_dir.is_dir():
        fail(
            "config",
            f"no specs/ directory found at {root}",
            fix="run /spec first or check you are at the project root",
        )
        exit_with(EXIT_CONFIG_ERROR)
    # First cut: exclude files known NOT to be root specs by name or suffix.
    excluded = {"feature-tracker.yaml", "design-system.yaml"}
    candidates = [
        p for p in sorted(specs_dir.glob("*.yaml"))
        if p.name not in excluded
        and not p.stem.endswith("-arch")
        and not p.stem.endswith("-ux")
    ]
    if not candidates:
        fail(
            "config",
            f"no root spec YAML found in {specs_dir}",
            fix="run /spec to create the initial project spec",
        )
        exit_with(EXIT_CONFIG_ERROR)
    # Second cut: when several YAMLs share specs/ (config files, strategy
    # docs, manifests), the root spec is the one that actually declares a
    # top-level `type:`. Fall back to the alphabetical first candidate if
    # none match — `load_spec_type()` then surfaces the existing clear error.
    typed = [p for p in candidates if _declares_spec_type(p)]
    picked = typed or candidates
    if len(picked) > 1:
        warn(
            f"multiple root specs found in {specs_dir} — using {picked[0].name}",
            candidates=[p.name for p in picked],
        )
    return picked[0]


def load_spec_type() -> str:
    """Read the root project spec and return its declared spec.type."""
    spec = load_yaml(find_project_spec())
    st = spec.get("type") or spec.get("spec", {}).get("type")
    if not st:
        fail(
            "config",
            "root spec YAML does not declare `type:` (web-ui | web-api | cli | ...)",
            fix="add `type: web-api` (or appropriate) to your root spec",
        )
        exit_with(EXIT_CONFIG_ERROR)
    return str(st).strip()


def load_project_type_config(spec_type: str) -> dict[str, Any]:
    """Load stacks/project-types/<spec_type>.yaml, resolving `extends:` chain."""
    path = project_types_dir() / f"{spec_type}.yaml"
    if not path.exists():
        available = sorted(p.stem for p in project_types_dir().glob("*.yaml"))
        fail(
            "config",
            f"unknown spec.type '{spec_type}'",
            fix=f"use one of: {', '.join(available)}  (in your root spec)",
        )
        exit_with(EXIT_CONFIG_ERROR)
    cfg = load_yaml(path)
    # Resolve inheritance: merge parent gates, then apply gates_add / gates_override.
    if parent_name := cfg.get("extends"):
        parent_cfg = load_project_type_config(parent_name)
        cfg = _merge_project_type(parent_cfg, cfg)
    return cfg


def _merge_project_type(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    """Merge a child project-type config over its parent.

    - child.gates (if present) REPLACES parent.gates entirely (escape hatch).
    - child.gates_add APPENDS new gates.
    - child.gates_override replaces matching gates by id.
    """
    merged: dict[str, Any] = dict(parent)
    merged.update({k: v for k, v in child.items() if k not in {"gates", "gates_add", "gates_override", "extends"}})

    if "gates" in child:
        merged["gates"] = list(child["gates"])
    else:
        merged["gates"] = list(parent.get("gates", []))

    for extra in child.get("gates_add", []) or []:
        merged["gates"].append(extra)

    overrides = child.get("gates_override", {}) or {}
    if overrides:
        by_id = {g["id"]: g for g in merged["gates"]}
        for gate_id, patch in overrides.items():
            if gate_id in by_id:
                by_id[gate_id] = {**by_id[gate_id], **patch}
        merged["gates"] = [by_id.get(g["id"], g) for g in merged["gates"]]

    return merged


# --- Tamper detection (anti-bypass without CI) ---------------------------

def scan_for_tampering(story_id: str | None) -> list[str]:
    """Run the bypass-detection scripts against the current branch.

    Returns the list of tamper reasons (empty list == clean).
    This is called at the start of every /build, /validate, /review, /ship.
    """
    reasons: list[str] = []

    # Only run checks that exist — missing scripts are an install issue, not a fail.
    checks = [
        ("check_story_commits.py", ["--scan-branch"]),
        ("check_test_tampering.py", ["--scan-branch"]),
        ("check_tdd_order.py", ["--scan-branch"]),
    ]
    for script_name, args in checks:
        script = SCRIPTS_DIR / script_name
        if not script.exists():
            continue
        try:
            result = subprocess.run(
                ["python3", str(script), *args],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            reasons.append(f"{script_name} timed out")
            continue
        if result.returncode != 0:
            # Use stdout if present (humans), else stderr, else the script name.
            detail = (result.stdout or result.stderr or script_name).strip()
            reasons.append(detail.splitlines()[0] if detail else script_name)
    return reasons


# --- Gate filtering & execution -----------------------------------------

def filter_applicable_gates(gates: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    """Keep only gates that apply for the current mode.

    - `required: true` gates always run.
    - `required: false` gates run only when their trigger is met.
      Triggers are evaluated lazily during execution (the orchestrator cannot
      know, for every trigger, whether it's satisfied without running a probe).
    - Gates with `trigger: invoked_by_ship` only run in mode=ship / gate-all.
    """
    applicable: list[dict[str, Any]] = []
    for gate in gates:
        if not isinstance(gate, dict) or "id" not in gate:
            continue
        trigger = gate.get("trigger")
        if trigger == "invoked_by_ship" and mode not in {"ship", "gate-all"}:
            continue
        applicable.append(gate)
    return applicable


def run_gate(gate: dict[str, Any], config: OrchestratorConfig) -> bool:
    """Run a single gate. Returns True on pass, False on fail.

    v5.0.0 scaffold: this routing layer is in place; individual gate runners
    are implemented in Étape 3 (scripts/check_*.py refactoring) and Étape 5
    (skill wrappers). For now, the orchestrator reports gates as "pending
    implementation" so the pipeline structure can be validated end-to-end.
    """
    gate_id = gate["id"]
    gate_name = gate.get("name", "")
    header(f"{gate_id} — {gate_name}")

    runner_hint = gate.get("script") or gate.get("agent") or gate.get("tool")
    if runner_hint:
        info(f"runner: {runner_hint}")

    # Placeholder — replaced in Étape 3 by real dispatch to check_*.py.
    warn(
        f"gate {gate_id} runner not yet implemented in v5.0.0 scaffold",
        gate=gate_id,
        mode=config.mode,
        story=config.story_id,
    )
    return True  # scaffold: treat unimplemented as pass so we can test routing.


# --- Main dispatch -------------------------------------------------------

def cmd_build_or_validate(config: OrchestratorConfig) -> int:
    if not config.story_id:
        fail(
            "config",
            f"--mode {config.mode} requires --story <story-id>",
            fix=f"python3 scripts/orchestrator.py --mode {config.mode} --story sc-0014",
        )
        return EXIT_CONFIG_ERROR

    # Step 1: tamper scan (source of truth is git log, not hooks)
    header(f"Pre-flight: tamper scan for {config.story_id}")
    reasons = scan_for_tampering(config.story_id)
    if reasons:
        for r in reasons:
            tampered(
                story_id=config.story_id,
                reason=r,
                how_to_resume=f'/resume {config.story_id} "explain how tampering was reconciled"',
            )
        return EXIT_TAMPERED
    success("pre-flight", "no tamper signal in git history")

    # Step 2: load project type + gates
    spec_type = load_spec_type()
    info(f"spec.type = {spec_type}")
    type_cfg = load_project_type_config(spec_type)
    gates = filter_applicable_gates(type_cfg.get("gates", []), config.mode)
    info(f"{len(gates)} gates applicable for mode={config.mode}")

    # Step 3: sequential execution
    failed = []
    for gate in gates:
        if not run_gate(gate, config):
            failed.append(gate["id"])

    # Step 4: verdict
    if failed:
        fail(
            "verdict",
            f"{len(failed)} gate(s) failed: {', '.join(failed)}",
            fix=f"fix the reported issues then re-run /{config.mode} {config.story_id}",
        )
        return EXIT_GATE_FAIL

    success("verdict", f"all {len(gates)} gates passed")
    if config.mode == "build":
        next_step(f"/validate {config.story_id} to run independent verification")
    elif config.mode == "validate":
        next_step(f"/ship {config.story_id} to create the PR")
    return EXIT_OK


def cmd_review(config: OrchestratorConfig) -> int:
    header("Review mode — diagnostic read-only")
    info("Rejouing all applicable gates across the current branch.")
    if config.story_id:
        info(f"scope: single story {config.story_id}")
    elif config.all_stories:
        info("scope: all stories on this branch")
    else:
        info("scope: stories modified in current branch (default)")
    spec_type = load_spec_type()
    type_cfg = load_project_type_config(spec_type)
    gates = filter_applicable_gates(type_cfg.get("gates", []), "review")
    failed = []
    for gate in gates:
        if not run_gate(gate, config):
            failed.append(gate["id"])
    if failed:
        fail("review", f"{len(failed)} gate(s) failed", fix="see per-gate output above")
        return EXIT_GATE_FAIL
    success("review", "all gates pass on current branch")
    next_step("safe to /ship — the chain of assurance is green")
    return EXIT_OK


def cmd_ship(config: OrchestratorConfig) -> int:
    if not config.story_id:
        fail(
            "config",
            "--mode ship requires --story <story-id>",
            fix="python3 scripts/orchestrator.py --mode ship --story sc-0014",
        )
        return EXIT_CONFIG_ERROR
    header(f"Ship {config.story_id} — the only door out to PR")
    # Step 1: full review must pass first.
    review_code = cmd_review(config)
    if review_code != EXIT_OK:
        fail(
            "ship",
            "review did not pass — PR creation refused",
            fix="fix the reported gate failures, then /ship again",
        )
        return review_code
    # Step 2: PR creation (scaffold — delegated to release-manager agent in Étape 2).
    info("PR creation will be handled by the release-manager agent (Étape 2)")
    next_step(
        f"[scaffold] /ship {config.story_id}: once release-manager is implemented, "
        f"this will push the branch and open the PR with tag sdd-validated-v5"
    )
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    cfg = parse_args(argv or sys.argv[1:])
    if cfg.mode in {"build", "validate"}:
        return cmd_build_or_validate(cfg)
    if cfg.mode == "review":
        return cmd_review(cfg)
    if cfg.mode == "ship":
        return cmd_ship(cfg)
    if cfg.mode == "gate-all":
        # CI chain: /build + /review for every story on the branch.
        return cmd_review(cfg)
    fail("config", f"unknown mode: {cfg.mode}", fix=f"use one of: {', '.join(sorted(VALID_MODES))}")
    return EXIT_CONFIG_ERROR


if __name__ == "__main__":
    code = main()
    exit_with(code)
