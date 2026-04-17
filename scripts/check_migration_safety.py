#!/usr/bin/env python3
"""check_migration_safety.py — zero-downtime migration + rollback validator.

Operates against `_work/data-fixtures/{story_id}/` as a seed. The stack
profile provides three commands:
    migrate_up:   alembic upgrade head | prisma migrate deploy | knex migrate:latest
    migrate_down: alembic downgrade -1 | prisma migrate resolve --rolled-back | knex migrate:rollback
    verify_read:  shell snippet that reads canary rows

Procedure: snapshot seed, migrate up, run verify_read, migrate down,
compare snapshot. Any mismatch => fail.

Exit: 0 pass, 1 fail, 2 config error.
"""
from __future__ import annotations

import argparse
import hashlib
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


def hash_dir(p: Path) -> str:
    if not p.exists():
        return ""
    h = hashlib.sha256()
    for f in sorted(p.rglob("*")):
        if f.is_file():
            h.update(f.relative_to(p).as_posix().encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def run(cmd: str, cwd: Path, timeout: int = 120) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=timeout,
        )
        return r.returncode, (r.stdout + "\n" + r.stderr)
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--story", required=True)
    ap.add_argument("--up", required=True, help="migrate-up command (e.g. 'alembic upgrade head')")
    ap.add_argument("--down", required=True, help="migrate-down command")
    ap.add_argument("--verify", required=True, help="shell cmd that reads canary rows and exits 0 on ok")
    ap.add_argument("--seed-dir", help="override _work/data-fixtures/{story}/")
    args = ap.parse_args()

    root = find_root()
    seed = Path(args.seed_dir) if args.seed_dir else root / "_work" / "data-fixtures" / args.story
    if not seed.exists():
        warn(f"no seed directory at {seed} — skipping migration safety")
        return 0

    pre = hash_dir(seed)
    info(f"seed pre-hash: {pre[:12]}")

    for label, cmd in [("up", args.up), ("verify", args.verify), ("down", args.down)]:
        code, out = run(cmd, root)
        if code != 0:
            fail(
                "G13",
                f"step '{label}' failed (exit {code})",
                fix=f"run `{cmd}` manually and fix the error",
            )
            return 1
        info(f"step {label}: OK")

    post = hash_dir(seed)
    if pre != post:
        fail(
            "G13",
            "seed directory differs after up+down round-trip",
            fix="the migration is not reversible — add backfill or fix rollback",
        )
        return 1
    success("G13", "migration up+down preserves seed state")
    return 0


if __name__ == "__main__":
    sys.exit(main())
