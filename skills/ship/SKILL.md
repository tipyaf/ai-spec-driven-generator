---
name: ship
description: The single exit gate toward PR — replays the full /review pipeline and, on PASS, hands off to release-manager which pushes the branch, creates the PR with evidence, and tags it sdd-validated-v5. Refuses on any gate failure.
---

# /ship

## Usage
/ship <story-id>

## What it does

`/ship` is the **only** sanctioned way to produce a PR in the v5 workflow. The contract:

> Until `/ship <story-id>` emits `PR CREATED: <url> with tag sdd-validated-v5`, the code is not allowed to leave the dev's machine.

Concretely, `/ship`:
1. Runs the full `/review` pipeline internally (every applicable G1–G14 gate).
2. On PASS: loads the `release-manager` agent, which pushes the branch, runs `gh pr create`, attaches `_work/build/sc-<id>.yaml` as evidence in the PR body, and applies the `sdd-validated-v5` tag.
3. On FAIL: refuses, prints the diagnostic report, and points the dev to `/build` or `/validate`.

## How it works

1. Verify prerequisites: story has `status: validated` in the tracker, clean working tree.
2. Invoke `python3 scripts/orchestrator.py --mode ship --story <id>`.
3. The orchestrator:
   - Replays the full gate chain (same logic as `/review --all` scoped to the branch).
   - On any failure → exit 1 with report; no push, no PR.
   - On full pass → dispatch `agents/release-manager.md` with the story context.
4. `release-manager` performs the side-effects (branch push, `gh pr create`, tag).
5. Relay the final message: `PR CREATED: <url> with tag sdd-validated-v5` or the failure report.

## Arguments

| Arg | Required | Description |
|---|---|---|
| `story-id` | Yes | Story to ship. Must already be `validated` via `/build`. |

## Flags

None. `/ship` is intentionally non-configurable — the orchestrator decides.

## Exit conditions

- **Success** (0): PR created; tracker status → `shipped`.
- **Failure** (1): at least one gate failed. PR NOT created. Fix and re-run `/build <id>` or `/validate <id>` before retrying `/ship`.
- **Config error** (3): `gh` CLI missing, remote not configured, dirty working tree.
- **Escalation** (2): not used by `/ship` directly — escalation is a `/build` concept. `/ship` simply refuses.

## Files read / written

- Reads: everything `/review` reads; `_work/build/sc-<id>.yaml` for PR evidence.
- Writes: `_work/build/sc-<id>.yaml` (ship block with PR url); `specs/feature-tracker.yaml` (status → `shipped`). Pushes branch, creates PR (side effect).

## Related

- `/build` — must pass before `/ship` is usable.
- `/review` — called internally; can also be run standalone.
- `/resume` — required if `/ship` is blocked by an earlier escalation or tamper flag.
