#!/usr/bin/env bash
# migrate-v4-to-v5.sh — Migrate a v4.x SDD project to v5.0
#
# v5 brings:
#  - 18 agents (test-author, code-reviewer, observability-engineer, performance-engineer,
#    data-migration-engineer, release-manager; old tester/reviewer/developer/spec-generator removed)
#  - 14 gates (G1-G14 including G9.x UI gates, G10 perf baselines, G13 data fixtures)
#  - scripts/orchestrator.py as the single source of truth for pipeline runs
#  - new slash commands: /ship /next /status /help /resume
#  - stacks/templates/{stack}/ folder layout with profile.yaml + ac-templates.yaml
#  - new _work/ dirs: visual-baseline, perf-baseline, contracts, data-fixtures
#
# The script is idempotent and fails cleanly on any step.
#
# Usage:
#   bash scripts/migrate-v4-to-v5.sh [--dry-run] [--backup] [--rollback] \
#                                    [--project-path PATH] [--force] [--yes]
#
# Flags:
#   --dry-run         Print actions only — no filesystem changes.
#   --backup          Force a backup even if _backup_v4/ already exists (default: backup is created).
#   --rollback        Restore from _backup_v4/ and exit.
#   --project-path P  Act on project at P (defaults to current working directory).
#   --force           Proceed even if git working tree is dirty.
#   --yes             Assume non-interactive "yes" for every prompt (needed in CI/tests).

set -euo pipefail

# ── Argument parsing ────────────────────────────────────────────────────────

DRY_RUN=false
DO_BACKUP=true
DO_ROLLBACK=false
FORCE=false
ASSUME_YES=false
PROJECT_PATH_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)        DRY_RUN=true; shift ;;
    --backup)         DO_BACKUP=true; shift ;;
    --no-backup)      DO_BACKUP=false; shift ;;
    --rollback)       DO_ROLLBACK=true; shift ;;
    --force)          FORCE=true; shift ;;
    --yes|-y)         ASSUME_YES=true; shift ;;
    --project-path)   PROJECT_PATH_ARG="$2"; shift 2 ;;
    -h|--help)
      sed -n '1,30p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELPER_PY="$SCRIPT_DIR/migrate-v4-to-v5_helpers.py"

# ── Resolve project root ────────────────────────────────────────────────────

if [[ -n "$PROJECT_PATH_ARG" ]]; then
  PROJECT_ROOT="$(cd "$PROJECT_PATH_ARG" && pwd)"
else
  PROJECT_ROOT="$(pwd)"
fi

# When script is inside framework submodule of project
if [[ -d "$PROJECT_ROOT/framework" && ! -f "$PROJECT_ROOT/CLAUDE.md" && -f "$PROJECT_ROOT/../CLAUDE.md" ]]; then
  PROJECT_ROOT="$(cd "$PROJECT_ROOT/.." && pwd)"
fi

BACKUP_DIR="$PROJECT_ROOT/_backup_v4"
REPORT_FILE="$BACKUP_DIR/MIGRATION_REPORT.md"

# Counters / bookkeeping
FILES_CREATED=0
FILES_MODIFIED=0
FILES_MOVED=0
WARNINGS=0

declare -a CHANGED_FILES=()
declare -a CREATED_FILES=()
declare -a WARNS=()

# ── Helpers ─────────────────────────────────────────────────────────────────

info()  { echo "  [INFO]  $*"; }
warn()  { echo "  [WARN]  $*"; WARNINGS=$((WARNINGS+1)); WARNS+=("$*"); }
err()   { echo "  [ERR ]  $*" >&2; }
act()   { echo "  [ACT ]  $*"; }
skip()  { echo "  [SKIP]  $*"; }

dry_or() {
  # Run command unless dry-run.
  if $DRY_RUN; then
    echo "  [DRY ]  $*"
  else
    eval "$@"
  fi
}

banner() {
  echo ""
  echo "============================================================"
  echo "  $*"
  echo "============================================================"
  echo ""
}

need_helper() {
  if [[ ! -f "$HELPER_PY" ]]; then
    err "Helper missing: $HELPER_PY"
    exit 3
  fi
}

py() {
  # Run the helper with a subcommand. Prefer a repo venv if present.
  local py_bin="python3"
  for candidate in \
    "$PROJECT_ROOT/.venv-sdd-dev/bin/python3" \
    "$PROJECT_ROOT/.venv/bin/python3" \
    "$SCRIPT_DIR/../.venv-sdd-dev/bin/python3" \
    "$SCRIPT_DIR/../.venv/bin/python3"; do
    if [[ -x "$candidate" ]]; then
      py_bin="$candidate"
      break
    fi
  done
  "$py_bin" "$HELPER_PY" "$@"
}

confirm() {
  local prompt="$1"
  if $ASSUME_YES || $DRY_RUN; then
    return 0
  fi
  read -r -p "$prompt [y/N] " ans
  [[ "$ans" =~ ^[Yy]([Ee][Ss])?$ ]]
}

# ── Rollback path ───────────────────────────────────────────────────────────

do_rollback() {
  banner "migrate-v4-to-v5.sh — ROLLBACK"
  if [[ ! -d "$BACKUP_DIR" ]]; then
    err "No backup found at $BACKUP_DIR — cannot rollback."
    exit 4
  fi
  info "Restoring from $BACKUP_DIR …"

  local targets=(specs _work memory CLAUDE.md .claude)
  for t in "${targets[@]}"; do
    if [[ -e "$BACKUP_DIR/$t" ]]; then
      dry_or "rm -rf \"$PROJECT_ROOT/$t\""
      dry_or "cp -R \"$BACKUP_DIR/$t\" \"$PROJECT_ROOT/$t\""
      info "Restored $t"
    fi
  done

  if [[ -f "$BACKUP_DIR/git-head.txt" ]]; then
    info "Git HEAD at backup was $(cat "$BACKUP_DIR/git-head.txt")"
    info "(Not resetting git automatically — do it manually if desired.)"
  fi

  echo ""
  echo "Rollback complete. Your project is back on v4."
  exit 0
}

if $DO_ROLLBACK; then
  do_rollback
fi

# ── Pre-flight checks ───────────────────────────────────────────────────────

banner "migrate-v4-to-v5.sh — MIGRATION $( $DRY_RUN && echo '(DRY RUN)' )"

info "Project root: $PROJECT_ROOT"

if [[ ! -d "$PROJECT_ROOT" ]]; then
  err "Project root does not exist: $PROJECT_ROOT"
  exit 2
fi

cd "$PROJECT_ROOT"

# Must be a v4.x SDD project.
# Detection strategy: the PROJECT's own state (CLAUDE.md) is the source of
# truth for "what version is this project on". The framework/VERSION only
# tells us which framework release is pinned — but that release can be v5
# while the project content is still v4 (submodule bumped before migration).
HAS_FRAMEWORK_SUBMODULE=false
HAS_CLAUDE_MD=false
FRAMEWORK_VERSION="unknown"
PROJECT_VERSION="unknown"

if [[ -d "$PROJECT_ROOT/framework" ]]; then
  HAS_FRAMEWORK_SUBMODULE=true
  if [[ -f "$PROJECT_ROOT/framework/VERSION" ]]; then
    FRAMEWORK_VERSION=$(cat "$PROJECT_ROOT/framework/VERSION" | tr -d '[:space:]')
  fi
fi

if [[ -f "$PROJECT_ROOT/CLAUDE.md" ]]; then
  HAS_CLAUDE_MD=true
  # Look for explicit version markers in the project's CLAUDE.md.
  if grep -qE "framework v5|v5\\.0|G1-G14|G1\\u2013G14|18 agents|20 enforcement scripts" "$PROJECT_ROOT/CLAUDE.md" 2>/dev/null; then
    PROJECT_VERSION="5.x"
  elif grep -qE "framework v4|v4\\.[01]|11 quality gates|11 gates|19 specialized agents|10 enforcement scripts" "$PROJECT_ROOT/CLAUDE.md" 2>/dev/null; then
    PROJECT_VERSION="4.x"
  fi
fi

if ! $HAS_FRAMEWORK_SUBMODULE && ! $HAS_CLAUDE_MD; then
  err "Not a SDD project: no framework/ submodule and no CLAUDE.md found."
  exit 5
fi

# SOURCE_VERSION is kept for downstream use; it reflects what we're migrating FROM.
# When the project's CLAUDE.md still says v4 but framework was bumped to v5,
# the project is mid-migration — we must proceed.
if [[ "$PROJECT_VERSION" = "4.x" ]]; then
  SOURCE_VERSION="4.x (detected in project CLAUDE.md)"
elif [[ "$PROJECT_VERSION" = "5.x" ]]; then
  SOURCE_VERSION="5.x (project already migrated)"
elif [[ "$FRAMEWORK_VERSION" =~ ^4 ]]; then
  SOURCE_VERSION="$FRAMEWORK_VERSION"
elif [[ "$FRAMEWORK_VERSION" =~ ^5 ]]; then
  # Framework is v5 but project's CLAUDE.md has neither v4 nor v5 markers —
  # likely an init-from-scratch v5 project or a very old/minimal CLAUDE.md.
  SOURCE_VERSION="5.x (framework pinned, project state unclear)"
else
  SOURCE_VERSION="$FRAMEWORK_VERSION"
fi

info "Framework pinned at: $FRAMEWORK_VERSION"
info "Project CLAUDE.md state: $PROJECT_VERSION"
info "Migration source: $SOURCE_VERSION"

case "$PROJECT_VERSION" in
  4.x)
    # Clear v4 project — proceed.
    ;;
  5.x)
    info "Project already on v5.x (detected in CLAUDE.md) — nothing to do."
    exit 0
    ;;
  unknown)
    # No clear version marker. Fall back to framework version.
    case "$FRAMEWORK_VERSION" in
      4.*) ;;
      5.*)
        warn "Framework is v5 but no v4/v5 markers found in CLAUDE.md."
        warn "Assuming project needs v5 scaffolding — proceeding."
        ;;
      unknown)
        warn "Could not detect version — continuing anyway."
        ;;
      *)
        err "Unexpected framework version '$FRAMEWORK_VERSION'."
        err "Use --force to override."
        $FORCE || exit 6
        ;;
    esac
    ;;
esac

# Git clean?
if command -v git >/dev/null 2>&1 && [[ -d "$PROJECT_ROOT/.git" ]]; then
  if ! git -C "$PROJECT_ROOT" diff --quiet HEAD 2>/dev/null \
     || [[ -n "$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null)" ]]; then
    if ! $FORCE; then
      err "Git working tree is dirty. Commit/stash changes first or pass --force."
      exit 7
    else
      warn "Proceeding with dirty working tree (--force)."
    fi
  fi
fi

need_helper

# ── Step 2: Backup ──────────────────────────────────────────────────────────

banner "Step 2 — Backup"

if $DO_BACKUP; then
  if [[ -d "$BACKUP_DIR" ]]; then
    info "Backup directory already exists at $BACKUP_DIR — reusing."
  else
    dry_or "mkdir -p \"$BACKUP_DIR\""
    for src in specs _work memory CLAUDE.md .claude; do
      if [[ -e "$PROJECT_ROOT/$src" ]]; then
        dry_or "cp -R \"$PROJECT_ROOT/$src\" \"$BACKUP_DIR/$src\""
        info "Backed up $src"
      fi
    done
    if command -v git >/dev/null 2>&1 && [[ -d "$PROJECT_ROOT/.git" ]]; then
      GITHEAD=$(git -C "$PROJECT_ROOT" rev-parse HEAD 2>/dev/null || echo "")
      if [[ -n "$GITHEAD" ]]; then
        dry_or "echo \"$GITHEAD\" > \"$BACKUP_DIR/git-head.txt\""
      fi
    fi
  fi
else
  info "Backup disabled (--no-backup)."
fi

# ── Step 3: Agent name mapping ──────────────────────────────────────────────

banner "Step 3 — Map v4 agent names to v5"

# We scan YAML/MD files under specs/ and _work/ for references to the old names
# and rewrite them through the Python helper (safer than sed for YAML).
if [[ -d "$PROJECT_ROOT/specs" || -d "$PROJECT_ROOT/_work" ]]; then
  if $DRY_RUN; then
    info "(dry-run) Would rewrite agent names with $HELPER_PY agents"
    py agents --project "$PROJECT_ROOT" --dry-run || warn "agents step reported issues"
  else
    py agents --project "$PROJECT_ROOT" || warn "agent rename step reported issues"
  fi
fi

# ── Step 4: Detect spec.type ────────────────────────────────────────────────

banner "Step 4 — Detect / confirm spec.type"

SPEC_TYPE_RAW=""
if $DRY_RUN; then
  SPEC_TYPE_RAW=$(py spec-type --project "$PROJECT_ROOT" --probe 2>/dev/null || echo "unknown")
else
  SPEC_TYPE_RAW=$(py spec-type --project "$PROJECT_ROOT" --probe || echo "unknown")
fi

SPEC_TYPE=$(echo "$SPEC_TYPE_RAW" | tr -d '[:space:]')

if [[ -z "$SPEC_TYPE" || "$SPEC_TYPE" = "unknown" || "$SPEC_TYPE" = "ambiguous" ]]; then
  if $ASSUME_YES; then
    SPEC_TYPE="lib"
    warn "spec.type could not be inferred; defaulting to 'lib' (under --yes)."
  elif $DRY_RUN; then
    SPEC_TYPE="unknown"
    warn "(dry-run) spec.type unknown — would prompt user."
  else
    echo "Could not infer spec.type. Choose one:"
    echo "  1) web-ui"
    echo "  2) web-api"
    echo "  3) cli"
    echo "  4) lib"
    echo "  5) service"
    read -r -p "Enter number [4]: " n
    case "${n:-4}" in
      1) SPEC_TYPE="web-ui" ;;
      2) SPEC_TYPE="web-api" ;;
      3) SPEC_TYPE="cli" ;;
      5) SPEC_TYPE="service" ;;
      *) SPEC_TYPE="lib" ;;
    esac
  fi
fi

info "spec.type = $SPEC_TYPE"

if ! $DRY_RUN; then
  py spec-type --project "$PROJECT_ROOT" --write "$SPEC_TYPE" || warn "could not persist spec.type"
fi

# ── Step 5: stacks plugin registry ──────────────────────────────────────────

banner "Step 5 — _work/stacks/registry.yaml"

STACKS_DIR="$PROJECT_ROOT/_work/stacks"
REGISTRY="$STACKS_DIR/registry.yaml"

if [[ ! -f "$REGISTRY" ]]; then
  dry_or "mkdir -p \"$STACKS_DIR\""
  if ! $DRY_RUN; then
    # Delegate to the Python helper which auto-detects stacks from the
    # project's package.json / pyproject.toml / docker-compose / migrations.
    # Fallback to a static registry only if the helper isn't available.
    if need_helper && py stack-detect --project "$PROJECT_ROOT" > "$REGISTRY" 2>/dev/null; then
      :
    else
      cat > "$REGISTRY" <<YAML
# SDD v5 stack registry — fallback (helper unavailable)
# Review and enable the stacks your project actually uses.
# See stacks/CUSTOM_STACK_GUIDE.md for custom stacks.
version: 1
stacks:
  python-fastapi:
    enabled: false
    path: framework/stacks/templates/python-fastapi
  typescript-react:
    enabled: false
    path: framework/stacks/templates/typescript-react
  postgres:
    enabled: false
    path: framework/stacks/templates/postgres
  nodejs-express:
    enabled: false
    path: framework/stacks/templates/nodejs-express
YAML
    fi
  fi
  info "Created $REGISTRY (auto-detected stacks)"
  CREATED_FILES+=("$REGISTRY")
  FILES_CREATED=$((FILES_CREATED+1))
else
  skip "$REGISTRY already exists"
fi

# Create per-stack folders in _work/stacks/ if the project references them.
for stack in python-fastapi typescript-react postgres nodejs-express; do
  d="$STACKS_DIR/$stack"
  if [[ ! -d "$d" ]]; then
    dry_or "mkdir -p \"$d\""
    dry_or "touch \"$d/.gitkeep\""
  fi
done

# ── Step 6: New _work/ directories ──────────────────────────────────────────

banner "Step 6 — New _work/ directories (visual-baseline, perf-baseline, contracts, data-fixtures)"

for sub in visual-baseline perf-baseline contracts data-fixtures; do
  d="$PROJECT_ROOT/_work/$sub"
  if [[ ! -d "$d" ]]; then
    dry_or "mkdir -p \"$d\""
    dry_or "touch \"$d/.gitkeep\""
    info "Created _work/$sub/"
    CREATED_FILES+=("_work/$sub/.gitkeep")
    FILES_CREATED=$((FILES_CREATED+1))
  else
    skip "_work/$sub/ exists"
  fi
done

# ── Step 7: CLAUDE.md ───────────────────────────────────────────────────────

banner "Step 7 — Update CLAUDE.md references to v5"

if [[ -f "$PROJECT_ROOT/CLAUDE.md" ]]; then
  if $DRY_RUN; then
    info "(dry-run) Would rewrite CLAUDE.md via helper"
  else
    py claude-md --project "$PROJECT_ROOT" && \
      { info "Rewrote CLAUDE.md"; CHANGED_FILES+=("CLAUDE.md"); FILES_MODIFIED=$((FILES_MODIFIED+1)); } || \
      warn "CLAUDE.md rewrite reported issues"
  fi
else
  warn "No CLAUDE.md — create one via framework bootstrap."
fi

# ── Step 8: .claude/settings.json merge ─────────────────────────────────────

banner "Step 8 — Merge .claude/settings.json with v5 hooks"

SETTINGS_SRC=""
if $HAS_FRAMEWORK_SUBMODULE && [[ -f "$PROJECT_ROOT/framework/stacks/hooks/settings-hooks-example.json" ]]; then
  SETTINGS_SRC="$PROJECT_ROOT/framework/stacks/hooks/settings-hooks-example.json"
elif [[ -f "$SCRIPT_DIR/../stacks/hooks/settings-hooks-example.json" ]]; then
  SETTINGS_SRC="$SCRIPT_DIR/../stacks/hooks/settings-hooks-example.json"
fi

if [[ -n "$SETTINGS_SRC" ]]; then
  info "Source hooks template: $SETTINGS_SRC"
  SETTINGS_DEST="$PROJECT_ROOT/.claude/settings.json"
  if $DRY_RUN; then
    info "(dry-run) Would merge $SETTINGS_SRC -> $SETTINGS_DEST"
  else
    mkdir -p "$PROJECT_ROOT/.claude"
    py merge-settings --template "$SETTINGS_SRC" --target "$SETTINGS_DEST" \
      && { info "Merged $SETTINGS_DEST"; CHANGED_FILES+=(".claude/settings.json"); FILES_MODIFIED=$((FILES_MODIFIED+1)); } \
      || warn "settings.json merge reported issues"
  fi
else
  warn "No hooks template found — skipping settings merge."
fi

# ── Step 9: feature-tracker.yaml validation ────────────────────────────────

banner "Step 9 — feature-tracker.yaml"

TRACKER=""
for candidate in "$PROJECT_ROOT/specs/feature-tracker.yaml" "$PROJECT_ROOT/_work/feature-tracker.yaml"; do
  if [[ -f "$candidate" ]]; then TRACKER="$candidate"; break; fi
done

if [[ -n "$TRACKER" ]]; then
  info "Found feature tracker: $TRACKER"
  if ! $DRY_RUN; then
    py tracker --project "$PROJECT_ROOT" --tracker "$TRACKER" \
      && info "feature-tracker.yaml validated & upgraded" \
      || warn "feature-tracker.yaml validation issues"
  else
    info "(dry-run) Would validate & upgrade feature-tracker.yaml"
  fi
else
  info "No feature-tracker.yaml — skipping"
fi

# ── Step 10: Story files — add interactions/smoke_command stubs ────────────

banner "Step 10 — Story files: interactions / smoke_command stubs"

if [[ -d "$PROJECT_ROOT/specs/stories" ]] || [[ -d "$PROJECT_ROOT/_work/spec" ]]; then
  if ! $DRY_RUN; then
    py stories --project "$PROJECT_ROOT" --spec-type "$SPEC_TYPE" \
      && info "Story files updated" \
      || warn "Story update reported issues"
  else
    info "(dry-run) Would add interactions/smoke_command stubs to story files"
  fi
else
  info "No stories directory — skipping"
fi

# ── Step 11: Framework submodule update ─────────────────────────────────────

banner "Step 11 — Framework submodule"

if $HAS_FRAMEWORK_SUBMODULE; then
  if $DRY_RUN; then
    info "(dry-run) Would try: cd framework && git fetch && git checkout v5.0"
  else
    if [[ -d "$PROJECT_ROOT/framework/.git" || -f "$PROJECT_ROOT/framework/.git" ]]; then
      if ( cd "$PROJECT_ROOT/framework" && git fetch --tags origin 2>/dev/null ); then
        if ( cd "$PROJECT_ROOT/framework" && git rev-parse v5.0 >/dev/null 2>&1 ); then
          ( cd "$PROJECT_ROOT/framework" && git checkout v5.0 ) && \
            info "Submodule checked out at v5.0" || \
            warn "Could not checkout v5.0"
        else
          warn "Tag v5.0 not yet published — leave submodule at current ref."
        fi
      else
        warn "Could not fetch framework submodule updates."
      fi
    else
      warn "framework/ is present but not a git submodule — skipping."
    fi
  fi
else
  info "No framework submodule — skipping."
fi

# ── Step 12: Migration report ───────────────────────────────────────────────

banner "Step 12 — Migration report"

if ! $DRY_RUN && [[ -d "$BACKUP_DIR" ]]; then
  py report \
    --project "$PROJECT_ROOT" \
    --backup "$BACKUP_DIR" \
    --report "$REPORT_FILE" \
    --source-version "$SOURCE_VERSION" \
    --target-version "5.0" \
    --spec-type "$SPEC_TYPE" \
    --created "$(IFS=,; echo "${CREATED_FILES[*]:-}")" \
    --changed "$(IFS=,; echo "${CHANGED_FILES[*]:-}")" \
    --warnings "$(IFS=,; echo "${WARNS[*]:-}")" \
    && info "Report written to $REPORT_FILE" \
    || warn "Could not write migration report."
else
  info "(dry-run / no-backup) skipping report"
fi

# ── Summary ─────────────────────────────────────────────────────────────────

banner "Summary"

echo "  Files created:   $FILES_CREATED"
echo "  Files modified:  $FILES_MODIFIED"
echo "  Files moved:     $FILES_MOVED"
echo "  Warnings:        $WARNINGS"

if $DRY_RUN; then
  echo ""
  echo "  Status: DRY RUN — no changes made."
  echo "  Re-run without --dry-run to apply."
  exit 0
fi

echo ""
echo "  Status: SUCCESS"
echo ""
echo "  Next steps:"
echo "    1. Review $REPORT_FILE"
echo "    2. Fill in interactions: for UI stories (run /refine on each)."
echo "    3. Configure a code-quality tool for G3 (sonar/semgrep/etc.)."
echo "    4. Commit: git add -A && git commit -m 'chore: migrate framework v4 -> v5'"
echo "    5. Once verified, remove backup: rm -rf $BACKUP_DIR"
echo ""
