#!/bin/bash
# ============================================================================
# init-project.sh — Initialize a new project using the AI framework
# ============================================================================
# Usage: ./scripts/init-project.sh <project-name> [target-directory]
#
# This script sets up a new project directory with:
# - Symlinks to the framework (agents, prompts, specs/templates, stacks)
# - Copies of rules files (must be at project root for Cursor/Claude Code)
# - A fresh memory file from the template
# - Empty output and specs directories
# ============================================================================

set -euo pipefail

# --- Arguments ---
PROJECT_NAME="${1:?Usage: $0 <project-name> [target-directory]}"
TARGET_DIR="${2:-.}"
FRAMEWORK_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# --- Resolve target ---
PROJECT_PATH="$TARGET_DIR/$PROJECT_NAME"

if [ -d "$PROJECT_PATH" ]; then
    echo "Error: Directory '$PROJECT_PATH' already exists."
    exit 1
fi

echo "Initializing project '$PROJECT_NAME'..."
echo "  Framework: $FRAMEWORK_DIR"
echo "  Target:    $PROJECT_PATH"
echo ""

# --- Create project structure ---
mkdir -p "$PROJECT_PATH"/{specs,memory,output,stacks}

# --- Symlinks to framework (shared, read-only) ---
ln -s "$FRAMEWORK_DIR/agents" "$PROJECT_PATH/agents"
ln -s "$FRAMEWORK_DIR/prompts" "$PROJECT_PATH/prompts"
ln -s "$FRAMEWORK_DIR/specs/templates" "$PROJECT_PATH/specs/templates"
ln -s "$FRAMEWORK_DIR/examples" "$PROJECT_PATH/examples"

# --- Copy rules (must be at project root for IDE integration) ---
cp "$FRAMEWORK_DIR/rules/CLAUDE.md" "$PROJECT_PATH/CLAUDE.md"
cp "$FRAMEWORK_DIR/rules/.cursorrules" "$PROJECT_PATH/.cursorrules"

# --- Create memory from template ---
sed "s/\[project-name\]/$PROJECT_NAME/g" "$FRAMEWORK_DIR/memory/memory-template.md" \
    > "$PROJECT_PATH/memory/$PROJECT_NAME.md"

# --- Create .gitignore ---
cat > "$PROJECT_PATH/.gitignore" << 'EOF'
# Dependencies
node_modules/

# Environment
.env
.env.local

# IDE
.idea/
.vscode/
*.swp
.DS_Store

# Output (generated projects are large)
# Uncomment if you want to track generated code:
# output/
EOF

# --- Create minimal README ---
cat > "$PROJECT_PATH/README.md" << EOF
# $PROJECT_NAME

Generated with [ai-spec-driven-generator](https://github.com/your-org/ai-spec-driven-generator).

## Quick start

1. Open this project in Cursor or Claude Code
2. The AI will read \`CLAUDE.md\` / \`.cursorrules\` and follow the framework workflow
3. Describe your project idea, or provide a YAML spec in \`specs/\`
4. Follow the phase-by-phase process with human validation

## Structure

\`\`\`
agents/          → (symlink) Framework agent definitions
prompts/         → (symlink) Framework phase prompts
specs/
  templates/     → (symlink) YAML spec templates
  $PROJECT_NAME.yaml → Your project spec (created during Phase 0)
memory/
  $PROJECT_NAME.md   → Project memory (updated by agents)
output/          → Generated project code
\`\`\`

## Framework

This project uses the \`ai-spec-driven-generator\` framework.
See the framework README for full documentation.
EOF

echo ""
echo "Project '$PROJECT_NAME' initialized successfully!"
echo ""
echo "Next steps:"
echo "  cd $PROJECT_PATH"
echo "  # Open in Cursor or Claude Code"
echo "  # Start with: @scoping or describe your project idea"
