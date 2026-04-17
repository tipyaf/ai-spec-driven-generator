---
name: migrate
description: Migrate a project to a newer framework version. Supports v3→v4, v4.0→v4.1, and v4.x→v5.0 with dry-run, backup, and rollback.
---

# /migrate

## Usage
/migrate [--to VERSION] [--dry-run] [--backup] [--rollback]

## What it does

Runs the migration script matching the current-to-target version jump. Always offers a dry-run first; always produces a `_backup_<from>/` directory unless `--no-backup` is passed; supports `--rollback` to restore the backup bit-exact.

| From | To | Script |
|---|---|---|
| v3.x | v4.0 | `scripts/migrate-v3-to-v4.sh` |
| v4.0.x | v4.1.0 | `scripts/migrate-v4.0-to-v4.1.sh` |
| v4.x | v5.0 | `scripts/migrate-v4-to-v5.sh` |

## How it works

1. Detect current project version from `memory/SYNC.md` or `CLAUDE.md`.
2. If `--to` omitted, pick the latest supported target.
3. Run `<script> --dry-run` first; present the diff to the user.
4. On confirmation, run the script with `--backup` to create `_backup_<from>/`.
5. Validate the result: required directories exist, feature tracker intact, CLAUDE.md references updated.
6. On validation failure, offer `--rollback`.

## Arguments

None positional.

## Flags

| Flag | Description |
|---|---|
| `--to VERSION` | Target framework version (default: latest). |
| `--dry-run` | Show planned changes without applying them. |
| `--backup` | Force backup creation (default: on). |
| `--rollback` | Restore the previous backup. |

## Exit conditions

- **0**: migration applied and validated.
- **1**: validation failed after apply.
- **3**: missing target script or unsupported version jump.

## Files read / written

- Reads: `memory/SYNC.md`, `CLAUDE.md`, `specs/` tree.
- Writes: `_backup_<from>/`, updated project layout, updated `memory/SYNC.md`.

## Related

- `/status` — confirm current framework version.
- `/help migrate` — detailed version history and migration notes.
