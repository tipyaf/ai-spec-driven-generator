#!/usr/bin/env python3
"""check_contract_diff.py — breaking-change detector for 3 contract kinds.

Modes:
    --kind api       diff OpenAPI spec against _work/contracts/{story}/openapi.yaml
    --kind library   AST diff of public exported functions/classes in Python
    --kind db        run alembic/prisma schema diff (delegated command)

A story may declare breaking changes explicitly:
    breaks: ["DELETE /users/{id}", "CustomerCreate.age"]
Breakages on that allowlist are accepted; others fail the gate.

Exit: 0 pass, 1 fail, 2 config error.
"""
from __future__ import annotations

import argparse
import ast
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


def load_story_breaks(root: Path, story: str) -> list[str]:
    if yaml is None:
        return []
    for candidate in (
        root / "specs" / "stories" / f"{story}.yaml",
        root / "specs" / "stories" / f"{story}-manifest.yaml",
    ):
        if candidate.exists():
            try:
                doc = yaml.safe_load(candidate.read_text()) or {}
                return list(doc.get("breaks", []) or [])
            except Exception:
                pass
    return []


# --- API mode -----------------------------------------------------------

def _endpoints(spec: dict) -> set[str]:
    endpoints = set()
    for path, methods in (spec.get("paths") or {}).items():
        for method in (methods or {}):
            endpoints.add(f"{method.upper()} {path}")
    return endpoints


def diff_openapi(current: dict, snapshot: dict) -> list[str]:
    removed = _endpoints(snapshot) - _endpoints(current)
    return sorted(removed)


# --- library mode --------------------------------------------------------

def _public_signatures(py_file: Path) -> dict[str, str]:
    try:
        tree = ast.parse(py_file.read_text())
    except Exception:
        return {}
    sigs: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            sigs[node.name] = ast.unparse(node.args) if hasattr(ast, "unparse") else str(node.args)
        if isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                sigs[node.name] = "class"
    return sigs


def diff_library(current_dir: Path, snapshot_dir: Path) -> list[str]:
    current_sigs = {}
    for f in current_dir.rglob("*.py"):
        current_sigs.update({f"{f.name}:{k}": v for k, v in _public_signatures(f).items()})
    snapshot_sigs = {}
    for f in snapshot_dir.rglob("*.py"):
        snapshot_sigs.update({f"{f.name}:{k}": v for k, v in _public_signatures(f).items()})
    removed = [k for k in snapshot_sigs if k not in current_sigs]
    changed = [k for k in snapshot_sigs if k in current_sigs and current_sigs[k] != snapshot_sigs[k]]
    return sorted(removed) + sorted(f"CHANGED {k}" for k in changed)


# --- db mode -------------------------------------------------------------

def diff_db(cmd: str, root: Path) -> list[str]:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=root, timeout=60)
    except Exception as exc:
        return [f"db diff command failed: {exc}"]
    if r.returncode != 0 or r.stdout.strip():
        return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()] or [r.stderr.strip()]
    return []


# --- main ---------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--kind", required=True, choices=["api", "library", "db"])
    ap.add_argument("--story", required=True)
    ap.add_argument("--current", help="path to current spec (api/library)")
    ap.add_argument("--snapshot", help="path to baseline snapshot dir or file")
    ap.add_argument("--db-diff-cmd", help="shell command for DB schema diff")
    args = ap.parse_args()

    root = find_root()
    breaks = load_story_breaks(root, args.story)

    breakages: list[str] = []
    if args.kind == "api":
        if yaml is None:
            fail("G2.3", "PyYAML required for api mode", fix="pip install pyyaml")
            return 2
        if not args.current or not args.snapshot:
            fail("G2.3", "--current and --snapshot required for api mode",
                 fix="pass --current spec.yaml --snapshot _work/contracts/<story>/openapi.yaml")
            return 2
        cur = yaml.safe_load(Path(args.current).read_text()) or {}
        snap = yaml.safe_load(Path(args.snapshot).read_text()) or {}
        breakages = diff_openapi(cur, snap)
    elif args.kind == "library":
        if not args.current or not args.snapshot:
            fail("G2.3", "--current and --snapshot required for library mode",
                 fix="pass --current src/ --snapshot _work/contracts/<story>/src/")
            return 2
        breakages = diff_library(Path(args.current), Path(args.snapshot))
    elif args.kind == "db":
        if not args.db_diff_cmd:
            fail("G2.3", "--db-diff-cmd required for db mode",
                 fix="pass --db-diff-cmd 'alembic current'")
            return 2
        breakages = diff_db(args.db_diff_cmd, root)

    undeclared = [b for b in breakages if b not in breaks]
    if undeclared:
        for b in undeclared:
            fail("G2.3", f"undeclared breaking change: {b}",
                 fix=f"add `breaks: [\"{b}\"]` to the story manifest with justification")
        return 1
    if breakages:
        info(f"{len(breakages)} declared break(s) acknowledged")
    success("G2.3", f"contract diff clean ({args.kind})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
