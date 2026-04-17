---
name: review
description: Read-only diagnostic — replays all applicable gates on a story or the entire branch. Produces a PASS/FAIL verdict with evidence but NEVER creates a PR or pushes. Use freely at any time for audit.
---

# /review

## Usage
/review [--story <story-id> | --all]

## What it does

Runs the full gate chain (G1 → G14 applicable to the project type) in **read-only** mode. Every check that `/build` and `/ship` would perform is replayed, but no state transition is written beyond a diagnostic report. `/review` NEVER pushes and NEVER creates a PR — that is reserved for `/ship`.

Use `/review` to:
- Audit a story after manual tweaks without changing its tracker status.
- Confirm the whole branch is green before calling `/ship`.
- Investigate a failure without incrementing the cycles counter.

## How it works

1. Parse args: `--story <id>` for per-story audit, `--all` for branch-wide replay.
2. Invoke `python3 scripts/orchestrator.py --mode review` with the same flag.
3. The orchestrator:
   - Runs tamper detection on git history.
   - For each in-scope story: replays every gate from the active project-type YAML.
   - Aggregates results and writes a diagnostic report to `_work/build/review-<timestamp>.yaml`.
4. Relay the PASS/FAIL verdict with per-gate evidence.

## Arguments

| Arg | Required | Description |
|---|---|---|
| `--story <id>` | One of | Audit a single story. |
| `--all` | One of | Audit every story on the current branch. |

If neither is provided, default to `--all`.

## Flags

| Flag | Description |
|---|---|
| `--story <id>` | Target a single story. |
| `--all` | Target the full branch. |

## Exit conditions

- **Success** (0): every audited gate passed.
- **Failure** (1): at least one gate failed. Dev inspects report and decides whether to run `/build`, `/validate`, or manual fixes.
- **Config error** (3): missing spec / stack / manifest.

Escalation is not triggered by `/review` — read-only mode does not consume cycles.

## Files read / written

- Reads: every artefact `/build` reads plus `_work/build/sc-*.yaml` for cached gate results.
- Writes: `_work/build/review-<timestamp>.yaml` diagnostic report only. No tracker updates.

## Related

- `/build` — run the pipeline and actually change state.
- `/ship` — gate-of-last-resort; calls `/review` internally before creating the PR.
- `/status` — passive dashboard view (no gate execution).
