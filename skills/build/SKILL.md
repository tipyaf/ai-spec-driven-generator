---
name: build
description: Build a refined story — auto-dispatches the right builder (service / frontend / infra / migration / exchange) and runs the full gate pipeline via the orchestrator. Replaces /build-service, /build-frontend, etc. in v4.
---

# /build

## Usage
/build <story-id>

## What it does

Runs the v5 build pipeline for a single refined story through `scripts/orchestrator.py`. The orchestrator is the single source of truth: it reads the story manifest, auto-dispatches the appropriate builder agent, runs the RED → GREEN → gates sequence driven by `stacks/project-types/<spec.type>.yaml`, and records the verdict in `_work/build/sc-<id>.yaml`.

The skill itself is a thin wrapper. All gate logic, tamper detection, cycle-counting and escalation live in the orchestrator. The user never invokes individual gates manually — `/build` is the one-shot entry point.

## How it works

1. Verify prerequisites (feature tracker present, story refined, manifest exists).
2. Invoke `python3 scripts/orchestrator.py --mode build --story <id>`.
3. The orchestrator:
   - Runs `check_story_commits.py` + `check_test_tampering.py` for tamper detection on git history.
   - Reads the story's `files:` and `epic:` from `specs/stories/<id>-manifest.yaml`.
   - Dispatches one builder agent via the rule table (see below).
   - Executes every gate from the active project-type YAML in declared order.
   - Writes results to `_work/build/sc-<id>.yaml`.
4. Parse the exit code and relay the orchestrator's output (already formatted via `ui_messages.py`).
5. On `EXIT_ESCALATED` (2) or `EXIT_TAMPERED` (4): show the `/resume` hint. No retry.

## Builder auto-dispatch

The dispatch agent reads the story manifest and picks **one** builder:

| If manifest says | Load agent |
|---|---|
| `epic: api` or files under `src/api/`, `backend/`, `services/` | `agents/builder-service.md` |
| `epic: ui` or files under `src/components/`, `web/`, `frontend/` | `agents/builder-frontend.md` |
| `epic: infra` or files under `infra/`, `terraform/`, `.github/` | `agents/builder-infra.md` |
| Files under `migrations/`, `alembic/`, `prisma/migrations/` | `agents/builder-migration.md` |
| `epic: exchange` or files under `integrations/`, `adapters/` | `agents/builder-exchange.md` |

If multiple patterns match, the builder with the largest file-count win. If none match, the dispatch returns a config-error and asks the user to set `epic:` in the manifest.

## Arguments

| Arg | Required | Description |
|---|---|---|
| `story-id` | Yes | Story identifier as listed in `specs/feature-tracker.yaml` (e.g. `sc-0014`) |

## Flags

None on the skill side. Orchestrator-level flags should be passed only by advanced users through a direct `python3 scripts/orchestrator.py` invocation.

## Exit conditions

- **Success** (exit 0): all gates passed, `_work/build/sc-<id>.yaml` recorded `status: validated`. Suggest `/ship <story-id>`.
- **Failure** (exit 1): at least one gate failed. Orchestrator wrote the failing gate + fix hint via `ui_messages.fail()`. Re-run `/build <story-id>` after fixes.
- **Escalation** (exit 2): 3 cycles exhausted. Story locked. Resume with `/resume <story-id> "<reason>"`.
- **Config error** (exit 3): missing spec, missing stack, bad manifest. Fix config and retry.
- **Tampered** (exit 4): bypass detected in git history (`--no-verify`, weakened assertion). Resume with `/resume <story-id> "<reason>"` after correction.

## Files read / written

- Reads: `specs/feature-tracker.yaml`, `specs/stories/<id>.yaml`, `specs/stories/<id>-manifest.yaml`, `stacks/project-types/<spec.type>.yaml`, `_work/stacks/registry.yaml`, `memory/LESSONS.md`.
- Writes: `_work/build/sc-<id>.yaml` (gate verdicts), `specs/feature-tracker.yaml` (status transitions).

## Related

- `/refine` — produces the story and manifest this skill consumes.
- `/validate` — runs the spec-contract check independently of gates.
- `/review` — read-only audit replaying all gates on the whole branch.
- `/ship` — the only way to create a PR once `/build` passes.
- `/resume` — unlock after escalation or tamper.
