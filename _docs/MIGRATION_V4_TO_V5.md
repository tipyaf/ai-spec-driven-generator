# Migration guide — SDD v4.x → v5.0

Status: stable · Target audience: maintainers of projects that already use SDD v4.x

## Table of contents

1. [Why migrate](#why-migrate)
2. [Prerequisites](#prerequisites)
3. [What the migration does](#what-the-migration-does)
4. [Commands](#commands)
5. [Post-migration checklist](#post-migration-checklist)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Why migrate

SDD v5.0 introduces:

- **14 gates (G1–G14)** instead of 11. New gates cover UI interactions (G9.x), performance baselines (G10), and data fixtures (G13).
- **Orchestrator is now `scripts/orchestrator.py`** — a single source of truth that every skill (`/build`, `/validate`, `/review`, `/ship`) calls into. No more drift between agent prompts and the actual pipeline.
- **New agent roster (18 total)**: `test-author` (replaces `tester` / `test-engineer`), `code-reviewer` (replaces `reviewer` / `story-reviewer`), plus `observability-engineer`, `performance-engineer`, `data-migration-engineer`, `release-manager`. `developer` and `spec-generator` are removed.
- **New slash commands**: `/ship`, `/next`, `/status`, `/help`, `/resume`.
- **Plugin-based stack templates** (`stacks/templates/{stack}/` as a directory with `profile.yaml` + `ac-templates.yaml`).
- **Contraignant escalation**: stories that were `blocked` in v4 become `escalated` in v5 — the pipeline refuses to silently leave them in limbo.

If none of those resonate, you can safely stay on v4.1.x. The v4 line still receives security fixes.

## Prerequisites

- `git` working tree is clean (`git status` shows no changes). The script will refuse to run otherwise (use `--force` to override, at your own risk).
- Framework already at **v4.1+**. Earlier v4.0.x projects should first run `migrate-v4.0-to-v4.1.sh`.
- Python 3 available on `PATH` (the helper is Python-only).
- If you use the framework as a submodule, make sure the submodule is tracked at v4.1.x before starting.

## What the migration does

In order, the script:

1. **Pre-checks**: verifies version, git cleanliness, SDD-ness of the project.
2. **Backs up** `specs/`, `_work/`, `memory/`, `CLAUDE.md`, `.claude/` into `_backup_v4/`.
3. **Renames agents** inside YAML/MD/JSON files under `specs/` and `_work/`:
   - `tester` and `test-engineer` → `test-author`
   - `reviewer` and `story-reviewer` → `code-reviewer`
   - `developer` and `spec-generator` references are flagged (left in place, but you'll see warnings)
4. **Detects `spec.type`** from existing specs, then falls back to project-file inference (`package.json`, `pyproject.toml`, `Cargo.toml`). Interactive prompt if ambiguous (`--yes` defaults to `lib`).
5. **Creates `_work/stacks/registry.yaml`** with the default plugins enabled.
6. **Creates new `_work/` subdirectories**: `visual-baseline/`, `perf-baseline/`, `contracts/`, `data-fixtures/`.
7. **Rewrites `CLAUDE.md`**: replaces v4 references (`11 gates`, `G1-G11`, …) with v5 equivalents and appends a migration note pointing at `_docs/PIPELINE.md`, `_docs/GUIDE.md`, `_docs/CHEATSHEET.md`.
8. **Merges `.claude/settings.json`** with the v5 hooks template. User-defined hooks and custom keys are preserved; v5 hooks are added where absent.
9. **Validates & upgrades `feature-tracker.yaml`**: any story with `status: blocked` becomes `status: escalated`. `validated` stories without a matching `_work/build/sc-*.yaml` get a migration note.
10. **Adds story stubs**: `interactions: []` for UI/mobile stories, `smoke_command: ""` for CLI stories. You fill them in later (via `/refine`).
11. **Updates the framework submodule** to `v5.0` if it exists (and the tag is published).
12. **Writes `_backup_v4/MIGRATION_REPORT.md`** summarizing everything.

The script is **idempotent**: a second run is a no-op for files it already migrated.

## Commands

Run these from the project root:

```bash
# 1. Dry-run first — see what will change, no modifications.
bash framework/scripts/migrate-v4-to-v5.sh --dry-run

# 2. Execute the migration. A backup is created at _backup_v4/.
bash framework/scripts/migrate-v4-to-v5.sh

# 3. Verify: inspect the report and run a smoke pipeline.
cat _backup_v4/MIGRATION_REPORT.md
/status

# 4. Commit.
git add -A && git commit -m "chore: migrate framework v4 -> v5"

# 5. Once satisfied, remove the backup.
rm -rf _backup_v4/
```

### Flags

| Flag                  | Effect                                                                |
|-----------------------|-----------------------------------------------------------------------|
| `--dry-run`           | Print actions only; no filesystem changes.                            |
| `--backup`            | Force backup (default: always on).                                    |
| `--no-backup`         | Skip backup (discouraged).                                            |
| `--rollback`          | Restore from `_backup_v4/`.                                           |
| `--project-path PATH` | Act on a different project.                                           |
| `--force`             | Proceed even with a dirty git working tree or unexpected version.     |
| `--yes` / `-y`        | Never prompt; CI-friendly. `spec.type` defaults to `lib` if ambiguous. |

### Rollback

```bash
bash framework/scripts/migrate-v4-to-v5.sh --rollback
```

This restores every backed-up file. The git HEAD is **not** auto-reset; if you already committed post-migration, reset manually (`git reset --hard <pre-migration-sha>`).

## Post-migration checklist

- [ ] Review `CLAUDE.md` for any residual v4 wording.
- [ ] Fill `interactions:` for every UI story (run `/refine <story>` on each; empty arrays trigger G9.x failures).
- [ ] Fill `smoke_command:` for every CLI story.
- [ ] Configure a code-quality backend for **G3** (mandatory in v5): SonarQube, Semgrep, Ruff, ESLint, etc. Point to it from `_work/stacks/{stack}/profile.yaml`.
- [ ] Trigger a commit to verify `.claude/settings.json` hooks still run cleanly.
- [ ] Run `/build sc-XXXX` on a representative story to confirm end-to-end flow.
- [ ] Remove `_backup_v4/` once confident.

## Troubleshooting

### `Not a SDD project: no framework/ submodule and no CLAUDE.md`

You're running the script outside a v4 project. Pass `--project-path` or `cd` into the project.

### `Git working tree is dirty`

Commit or stash first. If you really need to bypass: `--force`.

### `Tag v5.0 not yet published — leave submodule at current ref`

Harmless. Once the framework publishes the v5.0 tag, run:

```bash
cd framework && git fetch --tags && git checkout v5.0
```

### Merging `.claude/settings.json` overwrote my custom hook

The merger deep-merges and preserves user keys, but for identical hook matchers it can de-duplicate aggressively. Inspect `_backup_v4/.claude/settings.json` and re-add manually if needed.

### A story's `interactions:` field was not added

Only stories whose inferred `spec.type` is `web-ui` or `mobile` get the stub. Run `python3 framework/scripts/migrate-v4-to-v5_helpers.py stories --project . --spec-type web-ui` to force the update.

### `feature-tracker.yaml` has new `MIGRATION` notes I didn't write

Those flag stories that v5 cannot trust. Each note describes what's missing. Remove the note once you've investigated.

### I need to re-run the migration after manual edits

Safe — every step is idempotent. Use `--force` to bypass the dirty-tree check.

## FAQ

**Q: Can I migrate a monorepo with several SDD projects?**
Run the script once per project (passing `--project-path`).

**Q: Does v5 still read the v4 `_work/build/sc-XXXX.yaml` files?**
Yes. v5 reads the `gates:` map and merges v5-specific gates on top. Old `G1-G11` entries remain valid.

**Q: Do I have to migrate right now?**
No. v4.1.x keeps receiving security fixes. But the moment you want to ship a UI story with interaction contracts or enforce a performance baseline, you need v5.

**Q: What if my project has no `spec.type` field anywhere?**
The helper tries to infer it from `package.json`/`pyproject.toml`/`Cargo.toml`. If that fails, it asks interactively. In `--yes` mode it defaults to `lib` (the least restrictive) and you can fix it later with `/refine`.

**Q: Where do I report bugs in the migration?**
Open an issue on the framework repo with the full output of `--dry-run` and the pre-migration `CLAUDE.md`.
