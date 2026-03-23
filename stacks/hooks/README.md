# Claude Code Quality Hooks

Automated quality gates that run at key points in the development workflow. These hooks are configured in Claude Code's `settings.json` and execute automatically.

## Available Hook Points

### PreToolUse hooks
Run before specific tool calls. Use to enforce rules before actions happen.

### PostToolUse hooks
Run after specific tool calls. Use to verify results after actions complete.

## Recommended Hooks

### 1. Pre-commit: Anti-pattern check
Before any git commit, verify no anti-patterns exist in staged files.

**What it checks:**
- No hardcoded Tailwind colors in UI files (blue-200, red-500, etc.)
- No console.log/console.debug left in code
- No TODO/FIXME/HACK in committed code
- No empty catch blocks
- TypeScript compiles cleanly

### 2. Post-edit: Design system compliance
After editing a UI component file, verify CSS variables are used.

### 3. Pre-PR: Visual regression
Before creating a PR, take screenshots of modified pages and include in PR description.

## Setup

Copy the relevant hooks from `settings-hooks-example.json` into your project's `.claude/settings.local.json`.

### Project-specific anti-patterns
Add your own patterns in the hook configuration. Example for ExpatHunter:
- No hardcoded country names (use i18n-iso-countries lib)
- No hardcoded colors (use CSS variables: var(--color-*))
- API responses must include proper error codes

## Hook Configuration Format

Hooks in Claude Code settings.json use this format:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(git commit*)",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Checking anti-patterns...' && git diff --cached --name-only -- '*.tsx' '*.ts' | xargs grep -l 'blue-\\|red-\\|green-\\|console\\.log' && echo 'ANTI-PATTERNS FOUND' && exit 1 || exit 0"
          }
        ]
      }
    ]
  }
}
```

## Writing Custom Hooks

### Matcher patterns
- `Bash(git commit*)` — matches any git commit command
- `Bash(git push*)` — matches any git push command
- `Bash(gh pr create*)` — matches PR creation
- `Edit(*.tsx)` — matches edits to TSX files
- `Write(*.ts)` — matches writes to TS files

### Command guidelines
- Always wrap complex commands in `bash -c '...'`
- Exit 0 means the hook passes (tool call proceeds)
- Exit 1 means the hook fails (tool call is blocked)
- Use `echo` to provide feedback about what was checked
- Keep commands fast — they run synchronously before/after every matched tool call

### Testing hooks
Test your hook commands manually in the terminal before adding them to settings:
```bash
# Test the anti-pattern check against staged files
git diff --cached --name-only -- "*.tsx" "*.ts" | xargs grep -l "blue-[0-9]\|console\.log" 2>/dev/null
```
