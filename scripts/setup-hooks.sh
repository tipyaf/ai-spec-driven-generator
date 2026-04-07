#!/bin/sh
# Installs git hooks for the SSD framework.
# Run once after cloning: ./scripts/setup-hooks.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$ROOT/.git/hooks"

# --- Pre-commit hook: framework self-tests ---
cat > "$HOOKS_DIR/pre-commit" << 'HOOK'
#!/bin/sh
# Pre-commit hook — runs framework self-tests before every commit.
# Installed by: scripts/setup-hooks.sh
# Blocks the commit if any test fails.

# --- Check 1: Story commit atomicity (when specs/ files are staged) ---
SPEC_FILES=$(git diff --cached --name-only -- specs/)
if [ -n "$SPEC_FILES" ]; then
    echo "Running story commit check..."
    python3 "$(dirname "$0")/check_story_commits.py" 2>&1

    if [ $? -ne 0 ]; then
        echo ""
        echo "Story commit check FAILED — commit blocked."
        echo "Fix the issues above, then commit again."
        echo "To bypass (emergency only): git commit --no-verify"
        exit 1
    fi
fi

# --- Check 2: Framework self-tests (when framework files are staged) ---
FRAMEWORK_FILES=$(git diff --cached --name-only -- agents/ skills/ rules/ scripts/ specs/templates/ stacks/ tests/framework/)

if [ -z "$FRAMEWORK_FILES" ]; then
    exit 0
fi

echo "Running framework self-tests..."
python3 -m pytest tests/framework/ -q --tb=line 2>&1

if [ $? -ne 0 ]; then
    echo ""
    echo "Framework tests FAILED — commit blocked."
    echo "Fix the issues above, then commit again."
    echo "To bypass (emergency only): git commit --no-verify"
    exit 1
fi

echo "Framework tests passed."
HOOK

chmod +x "$HOOKS_DIR/pre-commit"

echo "Hooks installed:"
echo "  pre-commit -> story commit check + framework self-tests"
echo ""
echo "The hook runs automatically before every commit."
echo "  - Story commit check: triggers when specs/ files are staged"
echo "  - Framework self-tests: triggers when framework files are staged (agents/, skills/, rules/, scripts/, specs/templates/)"
