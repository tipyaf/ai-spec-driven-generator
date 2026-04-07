#!/bin/bash
# migrate-v4.0-to-v4.1.sh — Idempotent migration from v4.0.x to v4.1.0
#
# Changes:
# - Build templates: 7 gates → 11 gates, red_phase + green_phase sections
# - New directory: _work/ux/wireframes/
# - New enforcement script: check_story_commits.py in pre-commit hook
# - Updated SYNC.md version
#
# Usage:
#   bash scripts/migrate-v4.0-to-v4.1.sh [--dry-run]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DRY_RUN=false

if [ "$1" = "--dry-run" ]; then
    DRY_RUN=true
    echo "=== DRY RUN — no changes will be made ==="
    echo ""
fi

# Find project root (parent of scripts/ or framework/scripts/)
if [ -d "$SCRIPT_DIR/../agents" ]; then
    # Running from framework root
    FRAMEWORK_ROOT="$SCRIPT_DIR/.."
    PROJECT_ROOT="$SCRIPT_DIR/../.."
else
    FRAMEWORK_ROOT="$SCRIPT_DIR/.."
    PROJECT_ROOT="$SCRIPT_DIR/.."
fi

# If project root has a framework/ submodule, use project root
if [ -d "$PROJECT_ROOT/framework" ]; then
    FRAMEWORK_ROOT="$PROJECT_ROOT/framework"
fi

echo "Framework root: $FRAMEWORK_ROOT"
echo "Project root: $PROJECT_ROOT"
echo ""

CHANGES=0

# --- Step 1: Backup ---
BACKUP_DIR="$PROJECT_ROOT/_backup_v4.0"
if [ "$DRY_RUN" = false ] && [ ! -d "$BACKUP_DIR" ]; then
    echo "Step 1: Creating backup at $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    # Backup build files if they exist
    if [ -d "$PROJECT_ROOT/_work/build" ]; then
        cp -r "$PROJECT_ROOT/_work/build" "$BACKUP_DIR/"
    fi
    if [ -f "$PROJECT_ROOT/memory/SYNC.md" ]; then
        cp "$PROJECT_ROOT/memory/SYNC.md" "$BACKUP_DIR/"
    fi
    CHANGES=$((CHANGES + 1))
else
    echo "Step 1: Backup ${DRY_RUN:+would be created}${DRY_RUN:- already exists} at $BACKUP_DIR"
fi

# --- Step 2: Create _work/ux/wireframes/ ---
UX_DIR="$PROJECT_ROOT/_work/ux/wireframes"
if [ ! -d "$UX_DIR" ]; then
    echo "Step 2: Creating $UX_DIR"
    if [ "$DRY_RUN" = false ]; then
        mkdir -p "$UX_DIR"
        echo "# Wireframe HTML files for UI stories" > "$UX_DIR/.gitkeep"
    fi
    CHANGES=$((CHANGES + 1))
else
    echo "Step 2: $UX_DIR already exists — skipping"
fi

# --- Step 3: Update pre-commit hook with check_story_commits.py ---
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
if [ -d "$HOOKS_DIR" ] && [ -f "$HOOKS_DIR/pre-commit" ]; then
    if ! grep -q "check_story_commits" "$HOOKS_DIR/pre-commit" 2>/dev/null; then
        echo "Step 3: Adding check_story_commits.py to pre-commit hook"
        if [ "$DRY_RUN" = false ]; then
            # Re-run setup-hooks.sh to update the hook
            bash "$FRAMEWORK_ROOT/scripts/setup-hooks.sh"
        fi
        CHANGES=$((CHANGES + 1))
    else
        echo "Step 3: check_story_commits.py already in pre-commit hook — skipping"
    fi
else
    echo "Step 3: No pre-commit hook found — run scripts/setup-hooks.sh to create one"
fi

# --- Step 4: Update memory/SYNC.md ---
SYNC_FILE="$PROJECT_ROOT/memory/SYNC.md"
if [ -f "$SYNC_FILE" ]; then
    if ! grep -q "4.1.0" "$SYNC_FILE" 2>/dev/null; then
        echo "Step 4: Updating SYNC.md to v4.1.0"
        if [ "$DRY_RUN" = false ]; then
            echo "" >> "$SYNC_FILE"
            echo "## v4.1.0 Migration ($(date +%Y-%m-%d))" >> "$SYNC_FILE"
            echo "- Build pipeline: 7 gates → 11 gates" >> "$SYNC_FILE"
            echo "- Refine: wireframe gate + WCAG validation + PM integration" >> "$SYNC_FILE"
            echo "- Commit: atomic after ALL gates pass + auto PR/MR" >> "$SYNC_FILE"
            echo "- New script: check_story_commits.py" >> "$SYNC_FILE"
            echo "- New rules: agent-conduct Rules 11-17" >> "$SYNC_FILE"
        fi
        CHANGES=$((CHANGES + 1))
    else
        echo "Step 4: SYNC.md already references v4.1.0 — skipping"
    fi
else
    echo "Step 4: No SYNC.md found — skipping (will be created on next session start)"
fi

# --- Step 5: Warn about existing build files ---
BUILD_DIR="$PROJECT_ROOT/_work/build"
if [ -d "$BUILD_DIR" ] && ls "$BUILD_DIR"/sc-*.yaml >/dev/null 2>&1; then
    echo ""
    echo "WARNING: Existing build files found in $BUILD_DIR"
    echo "These use the old 7-gate format. They will still work but won't track"
    echo "the new gates (e2e_code, wcag_wireframes, e2e_execution, e2e_wireframe_validation,"
    echo "final_compilation). New builds will use the updated template automatically."
    echo ""
fi

# --- Summary ---
echo ""
echo "=== Migration Summary ==="
echo "Changes: $CHANGES"
if [ "$DRY_RUN" = true ]; then
    echo "Mode: DRY RUN (no changes made)"
    echo ""
    echo "Run without --dry-run to apply changes."
else
    echo "Mode: APPLIED"
    echo "Backup: $BACKUP_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Review the changes"
    echo "  2. Commit: git add _work/ memory/ && git commit -m 'chore: migrate to v4.1.0'"
    echo "  3. Remove backup once satisfied: rm -rf $BACKUP_DIR"
fi
