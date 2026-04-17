---
name: status
description: Passive dashboard — global counts by status, gate stats for in-progress stories, active escalations, recent release history, and a condensed "Recommended actions" block that wraps /next for blocked and in-progress items.
---

# /status

## Usage
/status [--story <story-id>]

## What it does

Gives a read-only overview of the project's health. No gate execution, no side effects.

Without `--story`, the dashboard shows:
- **Global stats**: counts of stories by status (pending, refined, building, validated, shipped, escalated, tampered).
- **Gate stats for in-progress stories**: per story, which gates passed, failed, pending.
- **Active escalations**: stories locked with their reason.
- **Recommended actions**: calls `next_report.py --scope blocked,in-progress` and embeds the result.
- **History**: last release date/tag, recent commits on the branch, flaky tests detected.

With `--story <id>`, the dashboard narrows to one story and prints the timestamped gate log plus the last build cycle.

## How it works

1. Read `specs/feature-tracker.yaml` for story states.
2. Read `_work/build/sc-*.yaml` for gate results; per-story when `--story` passed.
3. Read `memory/SYNC.md` / `CHANGELOG.md` for release history; `git log` for recent commits; `_work/flaky.yaml` if present.
4. Invoke `scripts/next_report.py --scope blocked,in-progress` and fold its output into the "Recommended actions" section.
5. Emit the composed report via `ui_messages.py`.

## Arguments

| Arg | Required | Description |
|---|---|---|
| `--story <id>` | No | Narrow the dashboard to a single story. |

## Flags

| Flag | Description |
|---|---|
| `--story <id>` | Per-story detail view with timestamped gate log. |

## Exit conditions

- Always **0** — purely informational.

## Files read / written

- Reads: `specs/feature-tracker.yaml`, `_work/build/*.yaml`, `_work/flaky.yaml`, `memory/SYNC.md`, `CHANGELOG.md`, git log.
- Writes: nothing.

## Related

- `/next` — the prioritised action list embedded in the dashboard.
- `/review` — active audit (runs gates; `/status` does not).
