#!/bin/sh
# setup-hooks.sh — install SDD v5 git hooks for fast local feedback.
#
# The orchestrator (scripts/orchestrator.py) is the SOURCE OF TRUTH for
# all gate verification; these hooks only give the dev a faster signal
# before the orchestrator re-runs everything at /build, /validate,
# /review, /ship. Running `git commit --no-verify` does NOT compromise
# final quality — the orchestrator will still catch violations.
#
# Run once after cloning:    ./scripts/setup-hooks.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$ROOT/.git/hooks"

# --- Pre-commit hook ----------------------------------------------------
cat > "$HOOKS_DIR/pre-commit" << 'HOOK'
#!/bin/sh
# Pre-commit hook — SDD v5 fast feedback.
# Installed by: scripts/setup-hooks.sh
# Bypass: git commit --no-verify (the orchestrator will still re-check later).

set -e
SCRIPTS="$(dirname "$0")/../../scripts"

FAIL=0

# 1. Atomic story commit check (works on staged files).
if [ -f "$SCRIPTS/check_story_commits.py" ]; then
    python3 "$SCRIPTS/check_story_commits.py" || FAIL=1
fi

# 2. ORACLE comment evaluation (numeric asserts must have consistent math).
if [ -f "$SCRIPTS/check_oracle_assertions.py" ]; then
    python3 "$SCRIPTS/check_oracle_assertions.py" || FAIL=1
fi

# 3. Design System conformity (only touches UI files).
if [ -f "$SCRIPTS/check_ds_conformity.py" ]; then
    python3 "$SCRIPTS/check_ds_conformity.py" || FAIL=1
fi

# 4. Observability ratio (informational — won't fail commit).
if [ -f "$SCRIPTS/check_observability.py" ]; then
    python3 "$SCRIPTS/check_observability.py" || true
fi

# 5. Framework self-tests when framework files are staged.
FRAMEWORK_FILES=$(git diff --cached --name-only -- agents/ skills/ rules/ scripts/ specs/templates/ stacks/ tests/framework/)
if [ -n "$FRAMEWORK_FILES" ]; then
    python3 -m pytest tests/framework/ -q --tb=line || FAIL=1
fi

if [ $FAIL -ne 0 ]; then
    echo ""
    echo "Pre-commit failed. Fix the issues above, then commit again."
    echo "Bypass (emergency only): git commit --no-verify"
    echo "Note: the orchestrator will re-run these checks at /build."
    exit 1
fi
HOOK
chmod +x "$HOOKS_DIR/pre-commit"

# --- Pre-push hook ------------------------------------------------------
cat > "$HOOKS_DIR/pre-push" << 'HOOK'
#!/bin/sh
# Pre-push hook — SDD v5 branch-wide tamper / TDD / RED scans.
set -e
SCRIPTS="$(dirname "$0")/../../scripts"

FAIL=0
if [ -f "$SCRIPTS/check_tdd_order.py" ]; then
    python3 "$SCRIPTS/check_tdd_order.py" --scan-branch || FAIL=1
fi
if [ -f "$SCRIPTS/check_test_tampering.py" ]; then
    python3 "$SCRIPTS/check_test_tampering.py" --scan-branch || FAIL=1
fi
if [ -f "$SCRIPTS/check_story_commits.py" ]; then
    python3 "$SCRIPTS/check_story_commits.py" --scan-branch || FAIL=1
fi
if [ -f "$SCRIPTS/check_red_phase.py" ]; then
    python3 "$SCRIPTS/check_red_phase.py" --scan-branch || FAIL=1
fi

if [ $FAIL -ne 0 ]; then
    echo ""
    echo "Pre-push failed. Fix before pushing."
    echo "Bypass (emergency only): git push --no-verify"
    echo "Note: the orchestrator /review will re-catch any bypass."
    exit 1
fi
HOOK
chmod +x "$HOOKS_DIR/pre-push"

echo "Hooks installed:"
echo "  pre-commit -> atomic story commit, ORACLE eval, DS conformity, observability (advisory), framework tests"
echo "  pre-push   -> TDD order / test tampering / story commits / RED phase scans across main..HEAD"
echo ""
echo "The orchestrator (/build /validate /review /ship) is the source of truth."
echo "Hooks = fast local feedback. --no-verify does NOT compromise final quality."
