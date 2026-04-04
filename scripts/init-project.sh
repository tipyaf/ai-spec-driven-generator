#!/bin/bash
# ============================================================================
# init-project.sh — Initialize a new project using the AI framework (v4.0)
# ============================================================================
# Usage: ./scripts/init-project.sh <project-name> [target-directory]
#
# This script sets up a new project with the framework as a git submodule.
# The project gets its own git repo with:
# - The framework as a submodule in framework/
# - A CLAUDE.md that tells Claude where everything is
# - Project-specific directories (specs, memory, stacks, _work/)
# - Hook configuration (hook-config.json, .claude/settings.json)
# - Symlinked skills from the framework
# - Stack profile templates copied to _work/stacks/
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
mkdir -p specs memory stacks .claude/commands

# --- Create _work/ directory structure (v4.0) ---
echo "Creating _work/ directory structure..."
mkdir -p _work/spec _work/build _work/ux _work/stacks
# Add .gitkeep so empty directories are tracked
for dir in _work/spec _work/build _work/ux _work/stacks; do
    [ -f "$dir/.gitkeep" ] || touch "$dir/.gitkeep"
done

# --- Generate CLAUDE.md from template ---
sed "s/\[project-name\]/$PROJECT_NAME/g" framework/rules/CLAUDE.md.template > CLAUDE.md

# --- Append _work/ convention to CLAUDE.md if not already present (v4.0) ---
if ! grep -q '_work/' CLAUDE.md 2>/dev/null; then
    cat >> CLAUDE.md << 'WORKDIR'

## `_work/` directory convention

All live agent working state lives under the `_work/` directory. This is project-specific content produced by agents during the build lifecycle.

| Path | Purpose | Who writes it |
|------|---------|---------------|
| `_work/spec/sc-0000-initial.yaml` | Baseline product spec (never modified by agents) | Dev (once, at project start) |
| `_work/spec/sc-[ID].yaml` | Per-story overlay (new/changed entries only) | Story Refiner |
| `_work/build/sc-[ID].yaml` | Build file: domain_context, ac_verifications, anti_patterns, gate results | Build Orchestrator (creates), Builder (extends) |
| `_work/stacks/` | Project-owned stack profiles (copied from templates) | Dev (initial), customized per project |
| `_work/ux/` | UX agent working files (prototype HTML, components YAML) | UX Designer |
WORKDIR
    echo "Appended _work/ convention to CLAUDE.md"
fi

# --- Copy .cursorrules (must be at root) ---
if [ -f framework/rules/.cursorrules ]; then
    sed "s/\[project-name\]/$PROJECT_NAME/g" framework/rules/.cursorrules > .cursorrules
fi

# --- Copy Claude Code commands (slash commands) ---
if [ -d framework/rules/commands ]; then
    cp framework/rules/commands/*.md .claude/commands/
    echo "Claude Code commands installed: /spec, /refine, /build, /validate, /review"
fi

# --- Copy stack profile templates to _work/stacks/ (v4.0) ---
if [ -d framework/stacks/templates ]; then
    for stack_file in framework/stacks/templates/*.md; do
        [ -f "$stack_file" ] || continue
        stack_name=$(basename "$stack_file")
        if [ -f "_work/stacks/$stack_name" ]; then
            echo "[SKIP] _work/stacks/$stack_name already exists"
        else
            echo "[COPY] _work/stacks/$stack_name"
            cp "$stack_file" "_work/stacks/$stack_name"
        fi
    done
fi

# --- Symlink framework skills into .claude/skills/ (v4.0) ---
if [ -d framework/.claude/skills ]; then
    mkdir -p .claude/skills
    for skill_dir in framework/.claude/skills/*/; do
        [ -d "$skill_dir" ] || continue
        skill=$(basename "$skill_dir")
        target=".claude/skills/$skill"
        if [ -e "$target" ] || [ -L "$target" ]; then
            echo "[SKIP] .claude/skills/$skill already exists"
        else
            echo "[LINK] .claude/skills/$skill -> $skill_dir"
            ln -s "../../framework/.claude/skills/$skill" "$target"
        fi
    done
elif [ -d framework/skills ]; then
    mkdir -p .claude/skills
    for skill_dir in framework/skills/*/; do
        [ -d "$skill_dir" ] || continue
        skill=$(basename "$skill_dir")
        target=".claude/skills/$skill"
        if [ -e "$target" ] || [ -L "$target" ]; then
            echo "[SKIP] .claude/skills/$skill already exists"
        else
            echo "[LINK] .claude/skills/$skill -> $skill_dir"
            ln -s "../../framework/skills/$skill" "$target"
        fi
    done
fi

# --- Create hook-config.json stub (v4.0) ---
if [ -f "hook-config.json" ]; then
    echo "[SKIP] hook-config.json already exists"
else
    echo "[CREATE] hook-config.json stub..."
    cat > hook-config.json << 'HOOKJSON'
{
  "checks": [
    {
      "note": "Add your lint/test commands here. {files} = changed file paths.",
      "name": "example-lint",
      "cmd": "echo 'No checks configured yet'",
      "filter": "*.py"
    }
  ],
  "skip_dirs": ["framework", "node_modules", "__pycache__", ".venv", "dist", ".next", "build"]
}
HOOKJSON
fi

# --- Create .claude/settings.json with hook configuration (v4.0) ---
if [ -f ".claude/settings.json" ]; then
    echo "[SKIP] .claude/settings.json already exists"
else
    echo "[CREATE] .claude/settings.json..."
    cat > .claude/settings.json << 'SETTINGSJSON'
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python framework/stacks/hooks/code_review.py",
            "timeout": 300
          },
          {
            "type": "command",
            "command": "python framework/stacks/hooks/sonar_check.py",
            "timeout": 300
          }
        ]
      }
    ]
  }
}
SETTINGSJSON
fi

# --- Create memory from template ---
sed "s/\[project-name\]/$PROJECT_NAME/g" framework/memory/memory-template.md \
    > "memory/$PROJECT_NAME.md"

# --- Create LESSONS.md from template ---
cp framework/memory/LESSONS.md.template memory/LESSONS.md

# --- Create SYNC.md from template with current framework version ---
FRAMEWORK_VERSION=$(cat framework/VERSION)
SYNC_DATE=$(date +%Y-%m-%d)
sed -e "s|\[read from framework/VERSION\]|$FRAMEWORK_VERSION|g" \
    -e "s|\[date\]|$SYNC_DATE|g" \
    -e "s|YYYY-MM-DD|$SYNC_DATE|g" \
    -e "s|X.Y.Z | X.Y.Z|$FRAMEWORK_VERSION | $FRAMEWORK_VERSION|g" \
    -e "s|Brief description|Initial framework setup|g" \
    framework/memory/SYNC.md.template > SYNC.md

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

# Python
__pycache__/
*.pyc
.venv/

# Worktrees
.worktrees/
EOF

# --- Create README ---
cat > README.md << EOF
# $PROJECT_NAME

Generated with [ai-spec-driven-generator](https://github.com/tipyaf/ai-spec-driven-generator) v4.0.

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
├── _work/               # Working artifacts (v4.0)
│   ├── spec/            #   Spec drafts and iterations
│   ├── build/           #   Build outputs and logs
│   ├── ux/              #   UX artifacts (wireframes, flows)
│   └── stacks/          #   Project-local stack profile copies
├── .claude/
│   ├── commands/        #   Slash commands (/spec, /build, etc.)
│   ├── skills/          #   Symlinked skills from framework
│   └── settings.json    #   Hook configuration (code review, sonar)
├── apps/                # Application code (created during scaffold phase)
├── packages/            # Shared packages (created during scaffold phase)
├── hook-config.json     # Quality gate hook configuration
├── CLAUDE.md            # AI instructions (generated from framework template)
└── .cursorrules         # Cursor rules (generated from framework template)
\`\`\`

## Update framework

\`\`\`bash
git submodule update --remote framework
\`\`\`
EOF

# --- Copy .env.example ---
if [ -f framework/stacks/hooks/.env.example ]; then
  cp framework/stacks/hooks/.env.example .env.example
  echo "Created .env.example — copy to .env and fill in your SonarQube credentials"
fi

# --- Initial commit ---
git add -A
git commit -m "Initialize project from ai-spec-driven-generator framework"

echo ""
echo "Project '$PROJECT_NAME' initialized successfully! (v4.0)"
echo ""
echo "Next steps:"
echo "  cd $PROJECT_PATH"
echo "  1. Edit hook-config.json with your lint/test commands"
echo "  2. Open in Cursor or Claude Code"
echo "  3. Start with: describe your project idea or /spec"
echo ""
echo "To update the framework later:"
echo "  git submodule update --remote framework"
