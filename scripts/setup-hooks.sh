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

# Only run if framework files are being committed
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
echo "  pre-commit -> framework self-tests (151 tests)"
echo ""
echo "The hook runs automatically before every commit."
echo "It only triggers when framework files are staged (agents/, skills/, rules/, scripts/, specs/templates/)."
