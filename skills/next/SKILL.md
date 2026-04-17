---
name: next
description: Morning action list — a <2s priority report classifying work into BLOCKING, IN PROGRESS, READY, PENDING SHIP, SUGGESTIONS. Each item carries the exact command to run and the relevant context (file:line, LESSONS pointer).
---

# /next

## Usage
/next [--scope blocked|in-progress|ready|ship|suggestions] [--json]

## What it does

Prints the priority action list for the project in five sections. It is the morning command: "what do I do now?". It runs fast (<2s) because it only reads YAML state files — no gate execution.

Sections:

| Section | Meaning |
|---|---|
| 🚨 BLOCKING | Stories flagged `escalated` or `tampered`. Fix these first. |
| ⏸ IN PROGRESS | Stories with `status: building` — resume where you left off. |
| ▶ READY | Stories refined and ready for `/build`, ordered by dependency graph. |
| 🚢 PENDING SHIP | Stories with `status: validated` waiting for `/ship`. |
| 💡 SUGGESTIONS | Flaky tests, perf drift, unread LESSONS, stale stack profiles. |

Each item carries the exact next command (`/build sc-0014`, `/ship sc-0012`, `/resume sc-0009 "..."`) plus context — e.g. the failing file:line, the escalation reason, or a pointer into `memory/LESSONS.md`.

## How it works

1. Invoke `python3 scripts/next_report.py` with any passthrough flags.
2. The script aggregates state from `specs/feature-tracker.yaml`, `_work/build/*.yaml`, `_work/perf-baseline/`, `_work/visual-baseline/`, `memory/LESSONS.md`, `git status`, `git log`, `gh pr list`.
3. Output is emitted via `ui_messages.py` helpers; `--json` switches to machine-readable mode for CI / dashboards.
4. Exit code is always 0 by default (informational). Use `--strict` when piping into CI to exit 1 on blockers.

## Arguments

None positional.

## Flags

| Flag | Description |
|---|---|
| `--scope blocked` | Show only BLOCKING items. |
| `--scope in-progress` | Show only IN PROGRESS. |
| `--scope ready` | Show only READY. |
| `--scope ship` | Show only PENDING SHIP. |
| `--scope suggestions` | Show only SUGGESTIONS. |
| `--json` | Emit machine-readable JSON. |
| `--strict` | Exit 1 when blockers exist (CI-friendly). |

Multiple scopes can be combined with commas (e.g. `--scope blocked,in-progress`).

## Exit conditions

- Always **0** in default mode.
- **1** when `--strict` and blockers are present.

## Files read / written

- Reads: `specs/feature-tracker.yaml`, `_work/build/*.yaml`, `_work/perf-baseline/`, `_work/visual-baseline/`, `memory/LESSONS.md`, git state.
- Writes: nothing. Purely informational.

## Related

- `/status` — passive dashboard with stats + history + embedded /next digest.
- `/resume` — unlock a BLOCKING item.
- `/build`, `/ship` — consume /next's recommendations.
