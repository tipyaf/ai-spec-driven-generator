---
name: resume
description: Unlock a story blocked by escalation or tamper detection. Requires a story-id AND a non-empty reason explaining why the block is resolved. The reason is appended verbatim to memory/LESSONS.md.
---

# /resume

## Usage
/resume <story-id> "<reason>"

## What it does

Unlocks a single story from the `escalated` or `tampered` state so the normal pipeline (`/build`, `/validate`, `/ship`) can proceed again. The reason is **mandatory and non-empty** — it becomes an audit entry in `memory/LESSONS.md`, ensuring every block resolution is traceable.

## How it works

1. Parse args:
   - Fewer than 2 args or empty reason → refuse with message: `resume requires a reason (why was the block resolved?)`. Exit 3.
   - Reason with embedded spaces must be passed as a single quoted argument.
2. Load `specs/feature-tracker.yaml`; confirm the story exists and is `escalated` or `tampered`.
3. Update the story's status to `building` and reset `cycles: 0`.
4. Append a line to `memory/LESSONS.md`:
   ```
   [<ISO-date>] resume <story-id>: <reason>
   ```
5. Emit a confirmation message via `ui_messages.success("/resume", ...)`.

## Arguments

| Arg | Required | Description |
|---|---|---|
| `story-id` | Yes | Story identifier. |
| `reason` | Yes | Non-empty string explaining why the block is resolved. Must be quoted if it contains spaces. |

## Flags

None.

## Exit conditions

- **Success** (0): story status reset; LESSONS entry appended.
- **Failure / config error** (3): missing args, empty reason, story not found, story not in an unlocked-ready state.

## Files read / written

- Reads: `specs/feature-tracker.yaml`.
- Writes: `specs/feature-tracker.yaml` (status transition), `memory/LESSONS.md` (append).

## Related

- `/build`, `/validate`, `/ship` — can be re-run after `/resume`.
- `/status` — shows which stories are currently blocked.
- `/next` — BLOCKING section lists stories that require `/resume`.
