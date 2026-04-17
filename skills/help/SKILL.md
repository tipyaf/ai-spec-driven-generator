---
name: help
description: Contextual help. `/help` with no arg lists every v5 command with a one-line summary; `/help <command>` prints full usage, arguments, flags, exit codes, and files touched. Suggests "did you mean X" on typos.
---

# /help

## Usage
/help [command]

## What it does

Discovery surface for the SDD v5 skillset.

- `/help` (no args) — lists every command with a one-line description pulled from each skill's frontmatter `description:`.
- `/help <command>` — prints the full SKILL.md body for that command (usage, arguments, flags, exit conditions, files read/written, related commands).
- `/help <typo>` — compute Levenshtein distance against every known command; when the closest match is within distance ≤ 2, print `did you mean '<match>'?` plus the top 3 candidates.

## How it works

1. Walk `skills/*/SKILL.md`, parse frontmatter.
2. If no arg: render the list sorted alphabetically, grouped by category:
   - **Pipeline**: `/spec`, `/refine`, `/ux`, `/build`, `/validate`, `/review`, `/ship`.
   - **Operations**: `/next`, `/status`, `/resume`.
   - **Quality**: `/scan`.
   - **Meta**: `/migrate`, `/help`.
3. If arg is a known command: print its SKILL.md body (strip YAML frontmatter).
4. If arg is unknown: compute distance to every command name; suggest up to 3 within distance ≤ 2; otherwise print "unknown command — use `/help` to list all commands".

## Arguments

| Arg | Required | Description |
|---|---|---|
| `command` | No | Name of a command (without leading slash). |

## Flags

None.

## Exit conditions

- **0**: always. `/help` is informational.

## Files read / written

- Reads: `skills/*/SKILL.md`.
- Writes: nothing.

## Related

- Every other skill.
