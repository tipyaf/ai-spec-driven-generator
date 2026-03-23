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

## Hook Points Reference

### PreToolUse (run before the action)
| Matcher | Triggers on |
|---------|-------------|
| `Bash(git commit*)` | Any git commit |
| `Bash(git push*)` | Any git push |
| `Bash(gh pr create*)` | PR creation |

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
