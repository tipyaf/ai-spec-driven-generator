# /migrate — Migrate v3.x project to v4.0 structure

## When to use
Run this skill when upgrading a project from framework v3.x to v4.0.

## What it does
1. Runs `framework/scripts/migrate-v3-to-v4.sh --dry-run` first to show planned changes
2. Asks for user confirmation
3. Runs the actual migration
4. Validates the result:
   - All expected `_work/` directories exist
   - Feature tracker is accessible
   - Story/spec files are in the right place
   - CLAUDE.md references updated correctly
5. If validation fails, offers to restore from `_backup_v3/`

## Prerequisites
- Project must have been initialized with framework v3.x
- `framework/` submodule must be updated to v4.0+

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
