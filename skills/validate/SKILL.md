---
name: validate
description: Validate a built story against its spec contract — replays every verify: command and checks AC mapping. Independent of /build; useful to confirm an implementation without rerunning the full gate chain.
---

# /validate

## Usage
/validate <story-id>

## What it does

Runs the spec-contract check for a single story via the orchestrator. Unlike `/build`, this mode does not compile, test-run, or dispatch a builder. It focuses on re-executing every `verify:` command from the story file (G5 AC validation) and confirming each AC maps to actual committed code (G6 story review in read-only mode).

Use it when the dev wants a fast confirmation after a manual fix without triggering the full RED/GREEN loop.

## How it works

1. Verify prerequisites (story file present, status at least `building`).
2. Invoke `python3 scripts/orchestrator.py --mode validate --story <id>`.
3. The orchestrator replays G5 (each `verify:` command, Tier 1 + Tier 2) and G6 (AC Tier 2/3 semantic check via `code-reviewer` mode `story`).
4. Emits PASS / FAIL / NOT_VERIFIABLE per AC via `ui_messages`.
5. Updates `_work/build/sc-<id>.yaml` validation block.

## Arguments

| Arg | Required | Description |
|---|---|---|
| `story-id` | Yes | Story to validate. |

## Flags

None.

## Exit conditions

- **Success** (0): all AC PASS or NOT_VERIFIABLE.
- **Failure** (1): at least one AC FAIL. Fix and re-run `/validate` or `/build`.
- **Escalation** (2): 3 cycles exhausted. Resume via `/resume`.
- **Config error** (3): bad story file or spec.

## Files read / written

- Reads: `specs/stories/<id>.yaml`, `specs/feature-tracker.yaml`, `_work/build/sc-<id>.yaml`.
- Writes: `_work/build/sc-<id>.yaml` (validation block), `specs/feature-tracker.yaml` (cycles).

## Related

- `/build` — full pipeline including validate.
- `/review` — replays validate across all stories.
- `/ship` — final validate before PR creation.
