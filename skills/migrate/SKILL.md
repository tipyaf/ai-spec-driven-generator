# /migrate — Migrate project to latest framework version

## When to use
Run this skill when upgrading a project to a newer framework version.

## Supported migrations

| From | To | Script |
|------|-----|--------|
| v3.x | v4.0 | `scripts/migrate-v3-to-v4.sh` |
| v4.0.x | v4.1.0 | `scripts/migrate-v4.0-to-v4.1.sh` |

## What it does (v4.0.x → v4.1.0)
1. Backs up to `_backup_v4.0/`
2. Updates `_work/build/` templates (11 gates, red_phase, green_phase)
3. Creates `_work/ux/wireframes/` if absent
4. Adds `check_story_commits.py` to pre-commit hook
5. Updates `memory/SYNC.md` with v4.1.0 version
6. Validates the result

## What it does (v3.x → v4.0)
1. Runs `scripts/migrate-v3-to-v4.sh --dry-run` first to show planned changes
2. Asks for user confirmation
3. Runs the actual migration
4. Validates the result:
   - All expected `_work/` directories exist
   - Feature tracker is accessible
   - Story/spec files are in the right place
   - CLAUDE.md references updated correctly
5. If validation fails, offers to restore from `_backup_v3/`

## Prerequisites
- `framework/` submodule must be updated to the target version

## Instructions

### Step 1: Pre-flight check
Read `CLAUDE.md` and `specs/` directory to understand current project state.
Identify which v3.x artifacts exist and need migration.

### Step 2: Dry run
Run: `bash framework/scripts/migrate-v3-to-v4.sh --dry-run`
Show the output to the user.

### Step 3: Confirm
Ask the user to confirm the migration plan.

### Step 4: Execute
Run: `bash framework/scripts/migrate-v3-to-v4.sh`
Show the output to the user.

### Step 5: Validate
After migration, verify:
- `_work/spec/` exists and contains spec files
- `_work/build/` exists (may be empty if no manifests existed)
- `_work/stacks/` exists and contains stack profiles
- `_work/feature-tracker.yaml` exists (if it existed before)
- `CLAUDE.md` references `_work/` paths, not `specs/stories/`
- No broken symlinks in `.claude/skills/`

### Step 6: Report
Show a structured report:
- Files moved: N
- Files updated: N
- Backup location: _backup_v3/
- Status: SUCCESS or PARTIAL (with details)

### Step 7: Cleanup reminder
Remind the user to:
- Commit the migration: `git add -A && git commit -m "chore: migrate project structure v3 → v4"`
- Test that their existing workflow still works
- Remove `_backup_v3/` once satisfied
