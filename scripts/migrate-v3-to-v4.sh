#!/usr/bin/env bash
# migrate-v3-to-v4.sh — Migrate existing v3.x projects to v4.0 structure
# Usage: bash framework/scripts/migrate-v3-to-v4.sh [--dry-run]
#
# This script migrates a v3.x project layout to the v4.0 _work/ convention.
# It is idempotent: running it multiple times is safe (existing targets are skipped).
# A full backup is created in _backup_v3/ before any changes are made.

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

# Resolve project root: walk up from this script's location to find CLAUDE.md
# or fall back to pwd. The script lives at framework/scripts/migrate-v3-to-v4.sh
# so the project root is two levels up from the script directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# If invoked as framework/scripts/..., project root is ../../
if [[ -d "$SCRIPT_DIR/../../specs" ]] || [[ -f "$SCRIPT_DIR/../../CLAUDE.md" ]]; then
  PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
else
  PROJECT_ROOT="$(pwd)"
fi

# Counters
FILES_MOVED=0
FILES_UPDATED=0
FILES_SKIPPED=0
ERRORS=0

# ── Helpers ────────────────────────────────────────────────────────────────────

info()  { echo "  [INFO]  $*"; }
warn()  { echo "  [WARN]  $*"; }
skip()  { echo "  [SKIP]  $*"; FILES_SKIPPED=$((FILES_SKIPPED + 1)); }
err()   { echo "  [ERROR] $*" >&2; ERRORS=$((ERRORS + 1)); }
action(){ echo "  [MOVE]  $*"; }

# Safe copy: copy file to destination, creating parent dirs as needed.
# In dry-run mode, just prints what would happen.
safe_copy() {
  local src="$1" dst="$2"
  if [[ -f "$dst" ]]; then
    skip "$dst already exists"
    return
  fi
  if $DRY_RUN; then
    action "(dry-run) $src -> $dst"
    FILES_MOVED=$((FILES_MOVED + 1))
    return
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  action "$src -> $dst"
  FILES_MOVED=$((FILES_MOVED + 1))
}

# Safe sed-in-place: update references in a file.
safe_sed() {
  local file="$1" pattern="$2" replacement="$3"
  if [[ ! -f "$file" ]]; then
    return
  fi
  if ! grep -q "$pattern" "$file" 2>/dev/null; then
    return
  fi
  if $DRY_RUN; then
    info "(dry-run) Would update '$pattern' -> '$replacement' in $file"
    FILES_UPDATED=$((FILES_UPDATED + 1))
    return
  fi
  # macOS / GNU sed compatibility
  if sed --version 2>/dev/null | grep -q GNU; then
    sed -i "s|$pattern|$replacement|g" "$file"
  else
    sed -i '' "s|$pattern|$replacement|g" "$file"
  fi
  info "Updated '$pattern' -> '$replacement' in $file"
  FILES_UPDATED=$((FILES_UPDATED + 1))
}

# Extract a feature slug from a filename.
# e.g. "sc-1234-auth-flow.yaml" -> "sc-1234-auth-flow"
#      "auth-flow-story.yaml"   -> "sc-auth-flow"
slugify_story() {
  local basename="$1"
  # Strip .yaml extension
  basename="${basename%.yaml}"
  # Strip trailing -story suffix if present
  basename="${basename%-story}"
  # If already starts with sc-, keep it; otherwise prepend sc-
  if [[ "$basename" == sc-* ]]; then
    echo "$basename"
  else
    echo "sc-${basename}"
  fi
}

# ── Banner ─────────────────────────────────────────────────────────────────────

echo ""
echo "============================================================"
if $DRY_RUN; then
  echo "  migrate-v3-to-v4.sh  (DRY RUN)"
else
  echo "  migrate-v3-to-v4.sh"
fi
echo "  Project root: $PROJECT_ROOT"
echo "============================================================"
echo ""

cd "$PROJECT_ROOT"

# ── Pre-flight checks ─────────────────────────────────────────────────────────

HAS_SPECS=false
HAS_STACKS=false

if [[ -d "specs" ]]; then
  HAS_SPECS=true
else
  warn "No specs/ directory found — skipping spec migrations"
fi

if [[ -d "stacks" ]]; then
  HAS_STACKS=true
else
  warn "No stacks/ directory found — skipping stack migrations"
fi

if ! $HAS_SPECS && ! $HAS_STACKS; then
  info "Nothing to migrate. Exiting."
  exit 0
fi

# ── Step 1: Backup ─────────────────────────────────────────────────────────────

echo "── Step 1: Backup ──────────────────────────────────────────"

if [[ -d "_backup_v3" ]]; then
  info "Backup directory _backup_v3/ already exists — skipping backup"
else
  if $DRY_RUN; then
    info "(dry-run) Would create _backup_v3/ with copies of specs/ and stacks/"
  else
    mkdir -p "_backup_v3"
    if $HAS_SPECS; then
      cp -R specs "_backup_v3/specs"
    fi
    if $HAS_STACKS; then
      cp -R stacks "_backup_v3/stacks"
    fi
    # Backup CLAUDE.md and .cursorrules if they exist
    [[ -f "CLAUDE.md" ]] && cp "CLAUDE.md" "_backup_v3/CLAUDE.md"
    [[ -f ".cursorrules" ]] && cp ".cursorrules" "_backup_v3/.cursorrules"
    info "Created backup at _backup_v3/"
  fi
fi
echo ""

# ── Step 2: Create _work/ directories ─────────────────────────────────────────

echo "── Step 2: Create _work/ directory structure ─────────────────"

for dir in _work/spec _work/build _work/ux _work/stacks; do
  if [[ -d "$dir" ]]; then
    skip "$dir/ already exists"
  elif $DRY_RUN; then
    info "(dry-run) Would create $dir/"
  else
    mkdir -p "$dir"
    info "Created $dir/"
  fi
done
echo ""

# ── Step 3: Migrate story specs ───────────────────────────────────────────────

echo "── Step 3: Migrate story specs ───────────────────────────────"

if $HAS_SPECS && [[ -d "specs/stories" ]]; then
  for file in specs/stories/*.yaml; do
    [[ -f "$file" ]] || continue
    basename="$(basename "$file")"

    # Skip manifest files — handled in step 4
    if [[ "$basename" == *-manifest.yaml ]] || [[ "$basename" == *-manifest.yml ]]; then
      continue
    fi

    slug="$(slugify_story "$basename")"
    safe_copy "$file" "_work/spec/${slug}.yaml"
  done
else
  info "No specs/stories/ directory — skipping story spec migration"
fi
echo ""

# ── Step 4: Migrate manifest files ────────────────────────────────────────────

echo "── Step 4: Migrate manifest files ────────────────────────────"

if $HAS_SPECS && [[ -d "specs/stories" ]]; then
  for file in specs/stories/*-manifest.yaml specs/stories/*-manifest.yml; do
    [[ -f "$file" ]] || continue
    basename="$(basename "$file")"

    # Strip -manifest suffix for the slug
    stripped="${basename%-manifest.yaml}"
    stripped="${stripped%-manifest.yml}"
    if [[ "$stripped" == sc-* ]]; then
      slug="$stripped"
    else
      slug="sc-${stripped}"
    fi

    dst="_work/build/${slug}.yaml"
    if [[ -f "$dst" ]]; then
      skip "$dst already exists"
      continue
    fi

    if $DRY_RUN; then
      action "(dry-run) $file -> $dst (will add gates section if missing)"
      FILES_MOVED=$((FILES_MOVED + 1))
    else
      mkdir -p "_work/build"
      cp "$file" "$dst"

      # Add gates section if missing
      if ! grep -q "^gates:" "$dst" 2>/dev/null; then
        cat >> "$dst" <<'GATES'

# Build gates — added during v3→v4 migration
gates:
  spec_approved: false
  tests_passing: false
  review_complete: false
GATES
        info "Added gates section to $dst"
      fi

      action "$file -> $dst"
      FILES_MOVED=$((FILES_MOVED + 1))
    fi
  done
else
  info "No specs/stories/ directory — skipping manifest migration"
fi
echo ""

# ── Step 5: Migrate UX specs ──────────────────────────────────────────────────

echo "── Step 5: Migrate UX specs ──────────────────────────────────"

if $HAS_SPECS; then
  for file in specs/*-ux.md; do
    [[ -f "$file" ]] || continue
    basename="$(basename "$file")"
    # Rename: project-ux.md -> project-ux-spec.md
    newname="${basename%.md}-spec.md"
    safe_copy "$file" "_work/ux/${newname}"
  done
else
  info "No specs/ directory — skipping UX migration"
fi
echo ""

# ── Step 6: Migrate feature tracker ──────────────────────────────────────────

echo "── Step 6: Migrate feature tracker ───────────────────────────"

if [[ -f "specs/feature-tracker.yaml" ]]; then
  safe_copy "specs/feature-tracker.yaml" "_work/feature-tracker.yaml"
elif [[ -f "specs/templates/feature-tracker.yaml" ]]; then
  info "feature-tracker.yaml found in templates only (not a project artifact) — skipping"
else
  info "No feature-tracker.yaml found — skipping"
fi
echo ""

# ── Step 7: Migrate project root spec ────────────────────────────────────────

echo "── Step 7: Migrate project root spec ─────────────────────────"

if $HAS_SPECS; then
  # Look for the main project spec (a .yaml in specs/ that is NOT *-ux.md, not in stories/, not in templates/)
  for file in specs/*.yaml; do
    [[ -f "$file" ]] || continue
    basename="$(basename "$file")"

    # Skip feature-tracker (handled above)
    [[ "$basename" == "feature-tracker.yaml" ]] && continue

    safe_copy "$file" "_work/spec/sc-0000-initial.yaml"
    # Only take the first matching project spec
    break
  done
fi
echo ""

# ── Step 8: Migrate stack profiles ───────────────────────────────────────────

echo "── Step 8: Migrate stack profiles ────────────────────────────"

if $HAS_STACKS; then
  for file in stacks/*.md; do
    [[ -f "$file" ]] || continue
    basename="$(basename "$file")"
    safe_copy "$file" "_work/stacks/${basename}"
  done
else
  info "No stacks/ directory — skipping stack migration"
fi
echo ""

# ── Step 9: Update references in CLAUDE.md and .cursorrules ──────────────────

echo "── Step 9: Update path references ────────────────────────────"

for target_file in CLAUDE.md .cursorrules; do
  if [[ -f "$target_file" ]]; then
    info "Updating references in $target_file"
    safe_sed "$target_file" "specs/stories/"   "_work/spec/"
    safe_sed "$target_file" "specs/stories"    "_work/spec"
    safe_sed "$target_file" "stacks/"          "_work/stacks/"
    # Be careful not to replace specs/templates or specs/*-arch references
    # Only replace bare specs/ references that point to feature-tracker
    safe_sed "$target_file" "specs/feature-tracker" "_work/feature-tracker"
  else
    info "No $target_file found — skipping"
  fi
done
echo ""

# ── Step 10: Migrate skills/ to .claude/skills/ symlinks ─────────────────────

echo "── Step 10: Migrate skill symlinks ───────────────────────────"

if [[ -d "skills" ]] && [[ ! -d ".claude/skills" ]]; then
  if $DRY_RUN; then
    info "(dry-run) Would create .claude/skills/ with symlinks to framework/.claude/skills/"
  else
    # Only create symlinks if this is a consumer project (has a framework/ submodule)
    if [[ -d "framework/.claude/skills" ]]; then
      mkdir -p ".claude/skills"
      for skill_dir in framework/.claude/skills/*/; do
        [[ -d "$skill_dir" ]] || continue
        skill_name="$(basename "$skill_dir")"
        if [[ ! -e ".claude/skills/$skill_name" ]]; then
          ln -s "../../framework/.claude/skills/$skill_name" ".claude/skills/$skill_name"
          info "Symlinked .claude/skills/$skill_name -> framework/.claude/skills/$skill_name"
        else
          skip ".claude/skills/$skill_name already exists"
        fi
      done
    else
      info "No framework/.claude/skills/ found — skills/ directory left as-is"
    fi
  fi
elif [[ -d ".claude/skills" ]]; then
  skip ".claude/skills/ already exists"
else
  info "No skills/ directory at project root — skipping"
fi
echo ""

# ── Summary ────────────────────────────────────────────────────────────────────

echo "============================================================"
if $DRY_RUN; then
  echo "  DRY RUN SUMMARY"
else
  echo "  MIGRATION SUMMARY"
fi
echo "============================================================"
echo ""
echo "  Files moved/copied:  $FILES_MOVED"
echo "  Files updated:       $FILES_UPDATED"
echo "  Files skipped:       $FILES_SKIPPED"
echo "  Errors:              $ERRORS"
echo ""

if ! $DRY_RUN && [[ -d "_backup_v3" ]]; then
  echo "  Backup location:     _backup_v3/"
  echo ""
fi

if [[ $ERRORS -gt 0 ]]; then
  echo "  Status: PARTIAL — $ERRORS error(s) occurred. Review output above."
  echo ""
  echo "  To restore from backup:"
  echo "    rm -rf _work/"
  echo "    cp -R _backup_v3/specs specs"
  echo "    cp -R _backup_v3/stacks stacks"
  echo "    [[ -f _backup_v3/CLAUDE.md ]] && cp _backup_v3/CLAUDE.md CLAUDE.md"
  echo "    [[ -f _backup_v3/.cursorrules ]] && cp _backup_v3/.cursorrules .cursorrules"
  exit 1
elif $DRY_RUN; then
  echo "  Status: DRY RUN — no changes were made"
  echo ""
  echo "  Run without --dry-run to execute the migration."
else
  echo "  Status: SUCCESS"
  echo ""
  echo "  Next steps:"
  echo "    1. Verify the _work/ directory structure looks correct"
  echo "    2. Commit: git add -A && git commit -m 'chore: migrate project structure v3 -> v4'"
  echo "    3. Test your workflow"
  echo "    4. Remove backup: rm -rf _backup_v3/"
fi

echo ""
echo "============================================================"
echo ""
