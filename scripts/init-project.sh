#!/bin/bash
# ============================================================================
# init-project.sh — Initialize a new project using the AI framework
# ============================================================================
# Usage: ./scripts/init-project.sh <project-name> [target-directory]
#
# This script sets up a new project with the framework as a git submodule.
# The project gets its own git repo with:
# - The framework as a submodule in framework/
# - A CLAUDE.md that tells Claude where everything is
# - Project-specific directories (specs, memory, stacks)
# ============================================================================

set -euo pipefail

# --- Arguments ---
PROJECT_NAME="${1:?Usage: $0 <project-name> [target-directory]}"
TARGET_DIR="${2:-.}"
FRAMEWORK_REPO="https://github.com/tipyaf/ai-spec-driven-generator.git"

# --- Resolve target ---
PROJECT_PATH="$TARGET_DIR/$PROJECT_NAME"

if [ -d "$PROJECT_PATH" ]; then
    echo "Error: Directory '$PROJECT_PATH' already exists."
    exit 1
fi

echo "Initializing project '$PROJECT_NAME'..."
echo "  Framework: $FRAMEWORK_REPO"
echo "  Target:    $PROJECT_PATH"
echo ""

# --- Create project and init git ---
mkdir -p "$PROJECT_PATH"
cd "$PROJECT_PATH"
git init

# --- Add framework as submodule ---
echo "Adding framework as git submodule..."
git submodule add "$FRAMEWORK_REPO" framework

# --- Create project-specific directories ---
mkdir -p specs memory stacks

# --- Generate CLAUDE.md from template ---
sed "s/\[project-name\]/$PROJECT_NAME/g" framework/rules/CLAUDE.md.template > CLAUDE.md

# --- Copy .cursorrules (must be at root) ---
if [ -f framework/rules/.cursorrules ]; then
    sed "s/\[project-name\]/$PROJECT_NAME/g" framework/rules/.cursorrules > .cursorrules
fi

# --- Create memory from template ---
sed "s/\[project-name\]/$PROJECT_NAME/g" framework/memory/memory-template.md \
    > "memory/$PROJECT_NAME.md"

# --- Create .gitignore ---
cat > .gitignore << 'EOF'
# Dependencies
node_modules/

# Environment
.env
.env.local
.env.*.local

# IDE
.idea/
.vscode/
*.swp
.DS_Store

# Build
dist/
build/
.next/
.cache/

# Logs
*.log
logs/
EOF

# --- Create README ---
cat > README.md << EOF
# $PROJECT_NAME

Generated with [ai-spec-driven-generator](https://github.com/tipyaf/ai-spec-driven-generator).

## Quick start

1. Open this project in Cursor or Claude Code
2. The AI reads \`CLAUDE.md\` and follows the framework workflow
3. Describe your project idea, or provide a YAML spec in \`specs/\`
4. Follow the phase-by-phase process with human validation

## Structure

\`\`\`
$PROJECT_NAME/
├── framework/           # Git submodule — AI framework (agents, prompts, rules)
├── specs/               # Project specs (YAML, UX, architecture)
├── memory/              # Project memory (decisions, phase status)
├── stacks/              # Stack profiles (coding & security contracts)
├── apps/                # Application code (created during scaffold phase)
├── packages/            # Shared packages (created during scaffold phase)
├── CLAUDE.md            # AI instructions (generated from framework template)
└── .cursorrules         # Cursor rules (generated from framework template)
\`\`\`

## Update framework

\`\`\`bash
git submodule update --remote framework
\`\`\`
EOF

# --- Initial commit ---
git add -A
git commit -m "Initialize project from ai-spec-driven-generator framework"

echo ""
echo "Project '$PROJECT_NAME' initialized successfully!"
echo ""
echo "Next steps:"
echo "  cd $PROJECT_PATH"
echo "  # Open in Cursor or Claude Code"
echo "  # Start with: describe your project idea or @scoping"
echo ""
echo "To update the framework later:"
echo "  git submodule update --remote framework"
