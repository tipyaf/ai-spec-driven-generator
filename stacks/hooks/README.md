# Quality Gate Hooks

Language-agnostic, configurable quality hooks for Claude Code. Instead of hardcoding patterns for a specific stack, hooks are driven by `hook-config.json` and adapted per project.

## Architecture

```
hook-config.json              — Pattern definitions (language-agnostic)
  |
  v
settings-hooks-example.json   — Generated Claude Code hooks (project-specific)
  |
  v
.claude/settings.local.json   — Copy relevant hooks into your project
```

## hook-config.json Format

The config file defines **what** to check, not **how** to wire it into Claude Code.

### Anti-pattern Rules

Each rule has:

| Field | Description |
|-------|-------------|
| `name` | Unique identifier for the rule |
| `description` | Human-readable explanation |
| `patterns` | Array of regex patterns to detect |
| `filter` | Glob for which files to check (e.g., `*.{py,rs,go}`) |
| `severity` | `error` (blocks commit) or `warning` (informational) |
| `message` | Feedback shown when pattern is detected |
| `applies_to` | Optional. Project types where this rule is relevant |

### Rule Categories

- **`rules`** — Universal rules (debug artifacts, secrets, incomplete code). Apply to every project.
- **`web_specific`** — Hardcoded colors, missing i18n. Apply to web-app, fullstack, mobile.
- **`api_specific`** — Hardcoded URLs. Apply to API and fullstack projects.
- **`cli_specific`** — Hardcoded file paths. Apply to CLI and desktop projects.

### Hook Command Templates

Templates use placeholders that get resolved per-rule:

| Placeholder | Resolves to |
|-------------|-------------|
| `{files}` | Staged files matching the rule's filter |
| `{file}` | Single file path (for post-edit hooks) |
| `{filter}` | The rule's file glob pattern |
| `{pattern}` | Regex pattern(s) joined for grep |
| `{name}` | Rule name |
| `{message}` | Rule's feedback message |
| `{cwd}` | Project working directory |

## Configuring for Your Language

The `filter` field determines which files are checked. Adapt it to your stack:

### Python project
```json
{
  "name": "debug-artifacts",
  "patterns": ["print\\(.*DEBUG", "breakpoint\\(\\)", "import pdb", "import ipdb"],
  "filter": "*.py",
  "severity": "error",
  "message": "Remove debug artifacts before committing"
}
```

### Rust project
```json
{
  "name": "debug-artifacts",
  "patterns": ["dbg!", "println!.*debug", "todo!", "unimplemented!"],
  "filter": "*.rs",
  "severity": "error",
  "message": "Remove debug macros before committing"
}
```

### Go project
```json
{
  "name": "debug-artifacts",
  "patterns": ["fmt\\.Println", "log\\.Print", "panic\\("],
  "filter": "*.go",
  "severity": "error",
  "message": "Remove debug prints before committing"
}
```

### Java project
```json
{
  "name": "debug-artifacts",
  "patterns": ["System\\.out\\.print", "e\\.printStackTrace", "\\.dump\\("],
  "filter": "*.java",
  "severity": "error",
  "message": "Remove debug output before committing"
}
```

## Project-Type Examples

### Web App (React/Vue/Svelte)
Use rules from: `rules` + `web_specific`
```
Checks: debug artifacts, secrets, hardcoded colors, missing i18n
Filter: *.{tsx,jsx,vue,svelte,ts,js}
```

### REST API (any language)
Use rules from: `rules` + `api_specific`
```
Checks: debug artifacts, secrets, hardcoded URLs
Filter: *.{py,rs,go,java,ts}
```

### CLI Tool
Use rules from: `rules` + `cli_specific`
```
Checks: debug artifacts, secrets, hardcoded paths
Filter: *.{py,rs,go}
```

### Library / Package
Use rules from: `rules` only (universal)
```
Checks: debug artifacts, secrets, incomplete code
Filter: *.{ts,py,rs,go,java}
```

## Adding Project-Specific Patterns

Add custom rules to `hook-config.json` under the appropriate category:

```json
{
  "name": "raw-sql",
  "description": "Raw SQL queries instead of query builder",
  "patterns": ["SELECT\\s+\\*", "DROP\\s+TABLE", "DELETE\\s+FROM"],
  "filter": "*.{py,ts,js,go,java}",
  "severity": "error",
  "message": "Use the query builder or ORM instead of raw SQL"
}
```

## Generating Claude Code Hooks from Config

To turn `hook-config.json` rules into Claude Code `settings.json` hooks:

1. **Pick your rules** — Select which rule categories apply to your project type.

2. **Expand the filter** — Convert the glob `*.{ts,tsx,js}` into separate arguments: `"*.ts" "*.tsx" "*.js"`.

3. **Join patterns for grep** — Combine the `patterns` array with `\|` for grep: `"console\\.log\|console\\.debug\|debugger"`.

4. **Apply the command template** — Substitute placeholders in `hook_commands.pre_commit.command_template`.

5. **Set the matcher** — Use `Bash(git commit*)` for pre-commit, `Edit(*.ext)` / `Write(*.ext)` for post-edit.

### Manual example

Given the `debug-artifacts` rule with `filter: "*.py"`:

```json
{
  "matcher": "Bash(git commit*)",
  "hooks": [
    {
      "type": "command",
      "command": "bash -c 'FILES=$(git diff --cached --name-only -- \"*.py\" | head -50); if [ -n \"$FILES\" ]; then FOUND=$(echo \"$FILES\" | xargs grep -l \"print(.*DEBUG\\|breakpoint()\\|import pdb\" 2>/dev/null); if [ -n \"$FOUND\" ]; then echo \"debug-artifacts: Remove debug artifacts before committing\"; echo \"$FOUND\"; exit 1; fi; fi; exit 0'"
    }
  ]
}
```

See `settings-hooks-example.json` for a complete generated example targeting a TypeScript/React web project.

## Python Hook Script (`code_review.py`)

A standalone Python script that reads `hook-config.json` and runs anti-pattern checks against staged (or all tracked) files. No external dependencies required -- uses only the Python standard library.

### Quick Start

```bash
# Run against staged files (default)
python3 code_review.py

# Run with project-type filtering (includes type-specific rules)
python3 code_review.py --project-type web

# Run against all tracked files
python3 code_review.py --all-files

# Use a custom config path
python3 code_review.py --config /path/to/hook-config.json
```

### Integration as a Git Pre-Commit Hook

Add to your project's `.git/hooks/pre-commit`:

```bash
#!/bin/bash
python3 path/to/code_review.py --project-type web
```

Or wire it into Claude Code's `settings.local.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(git commit*)",
        "hooks": [
          {
            "type": "command",
            "command": "python3 stacks/hooks/code_review.py --project-type web"
          }
        ]
      }
    ]
  }
}
```

### How It Works

1. **Loads config** -- Finds `hook-config.json` next to the script, or in the repo root.
2. **Gets staged files** -- Runs `git diff --cached --name-only --diff-filter=ACMR`.
3. **Collects rules** -- Universal rules always run. Type-specific rules (`web_specific`, `api_specific`, `cli_specific`) run when `--project-type` matches.
4. **Filters by glob** -- Each rule's `filter` field (e.g., `*.{ts,tsx,js}`) narrows which files are checked.
5. **Scans for patterns** -- Reads each file and runs regex matching against the rule's `patterns` array.
6. **Reports results** -- Clear per-rule PASS/FAIL/WARNING output with file:line details.
7. **Exit code** -- Returns 0 if no errors, 1 if any error-severity rule has violations. Warnings never block.

### CLI Options

| Flag | Description |
|------|-------------|
| `--config`, `-c` | Path to hook-config.json (auto-detected by default) |
| `--project-type`, `-p` | Project type: `web`, `api`, `cli`, `fullstack`, `desktop` |
| `--all-files` | Check all tracked files, not just staged |
| `--timeout`, `-t` | Default timeout per external command in seconds (default: 30) |

### Severity Levels

- **`error`** -- Blocks the commit (exit code 1). Must be fixed before committing.
- **`warning`** -- Informational. Shows in output but allows the commit (exit code 0).

### External Command Checks

In addition to anti-pattern rules, the script supports external command checks via a `checks` array in `hook-config.json` (same format as the reference implementation):

```json
{
  "checks": [
    {
      "name": "typecheck",
      "cmd": "npx tsc --noEmit",
      "filter": "*.{ts,tsx}",
      "severity": "error",
      "timeout": 60,
      "auto_restage": false
    }
  ]
}
```

## Hook Points Reference

### PreToolUse (run before the action)
| Matcher | Triggers on |
|---------|-------------|
| `Bash(git commit*)` | Any git commit |
| `Bash(git push*)` | Any git push |
| `Bash(gh pr create*)` | PR creation |
| `Bash(git checkout -b*)` | Branch creation |

### Git Flow Enforcement Hooks

These hooks prevent the most common Git Flow violations. They are **blocking** (exit 1 = action denied).

| Hook | Matcher | What it blocks | Exception |
|------|---------|---------------|-----------|
| `pr-base-branch-guard` | `Bash(gh pr create*)` | PRs targeting `main` | Current branch is `release/*` |
| `push-to-main-guard` | `Bash(git push*)` | Direct push to `main` | None |
| `branch-origin-guard` | `Bash(git checkout -b*)` | Branching from `main` | None |

These hooks read `$CLAUDE_TOOL_ARG_command` to inspect the command arguments before execution. If a violation is detected, the hook prints an error and exits 1, which blocks the action in Claude Code.

### PostToolUse (run after the action)
| Matcher | Triggers on |
|---------|-------------|
| `Edit(*.ext)` | File edits matching extension |
| `Write(*.ext)` | File writes matching extension |

### Command Guidelines
- Wrap commands in `bash -c '...'`
- Exit 0 = hook passes (action proceeds)
- Exit 1 = hook fails (action is blocked)
- Use `echo` for feedback
- Keep commands fast (they run synchronously)
- Use `$CLAUDE_TOOL_ARG_file_path` in PostToolUse hooks to access the edited file path
