---
name: build
description: Build/implement a refined story. Reads the story file, follows the scope manifest, writes code, runs validation. Use after a story has been refined.
---

## Phase guard — verify before proceeding

**Prerequisites** (check filesystem):
1. `specs/feature-tracker.yaml` must exist
2. The target feature must have `status: refined` in the tracker
3. `specs/stories/[feature-id].yaml` must exist (the build contract)
4. Read the story file — verify ALL ACs have a `verify:` field

**If any prerequisite is missing** → Tell user: "This story needs refinement first" → suggest `/refine`

## Setup — Read these files before starting

1. Read `agents/developer.md` (core instructions)
2. Read `agents/validator.md` (core instructions)
3. Read `memory/LESSONS.md` (known pitfalls)
4. Read `specs/stories/[feature-id].yaml` (THE build contract — this is your scope)
5. Read stack profiles from `stacks/` (coding rules)

Only read `.ref.md` files if you need a specific template during implementation.

## Workflow

### Phase 3: Implement
1. Read the story file — this defines your ENTIRE scope
2. Read LESSONS.md — apply relevant lessons as constraints
3. **Only touch files listed in the story's `scope` section.** If an unlisted file is needed, document it and add it to scope with justification.
4. Follow the developer agent workflow to implement
5. Write tests alongside code (not after)
6. Self-check against ALL acceptance criteria
7. Update `specs/feature-tracker.yaml`: set feature status to `building`

### Phase 3.5: Validate (7 sequential gates)
Run these quality gates in order. ALL must pass.

**Gate 1 — Security**: check OWASP patterns, stack forbidden patterns, AC-SEC-* verify commands
**Gate 2 — Tests**: run unit tests + e2e tests (if applicable)
**Gate 3 — UI** (if UI project): WCAG check + wireframe conformity
**Gate 4 — AC Validation**: execute EVERY `verify:` command from the story file
**Gate 5 — Review**: code quality, scope conformity (only touched listed files?)
**Gate 6 — SonarQube**: run SonarQube scan on story files. Generate coverage report first (`pytest --cov` / `vitest --coverage`), then scan. Blocks if new BLOCKER or CRITICAL issues are introduced. If SonarQube is not configured (no `.env` or env vars), this gate is **skipped** (not failed) — SonarQube remains optional per project.
**Gate 7 — Story Review**: dispatch `agents/story-reviewer.md` — verifies every AC against committed code with structured PASS/FAIL verdict. **This gate is mandatory.** The story CANNOT be marked `validated` without a PASS from the story reviewer.

### Verdict
- **ALL GATES PASS**: Update tracker status to `validated`. Report to user.
- **ANY FAIL**: Increment `cycles` in tracker. Fix and re-validate (loop back to the failed gate).
- **cycles >= 3**: ESCALATE to human. Do NOT attempt a 4th cycle. Update tracker notes with what failed and why.

## Specialized builder dispatch

Based on story type or epic, dispatch to the appropriate builder agent:

| Story type / Epic | Builder agent |
|---|---|
| Backend service / API | `agents/builder-service.md` |
| Frontend / UI | `agents/builder-frontend.md` |
| Infrastructure / DevOps | `agents/builder-infra.md` |
| Database migration | `agents/builder-migration.md` |
| External integration / exchange | `agents/builder-exchange.md` |
| General / unknown | `agents/developer.md` (default) |

Read the story's `epic` or `type` field to determine which builder to dispatch. If uncertain, use the default developer agent.

## TDD pipeline — 6 enforcement gates

All builds follow strict TDD. The pipeline has two phases with enforcement scripts:

### RED phase (Test Engineer writes tests first)
1. Dispatch `agents/test-engineer.md` to write failing tests based on story ACs
2. Run `scripts/check_red_phase.py` — confirms tests exist AND fail (red)
3. Run `scripts/check_test_intentions.py` — confirms test intentions match AC verify commands

### GREEN phase (Builder makes tests pass)
4. Dispatch the appropriate builder agent (see table above)
5. Run `scripts/check_tdd_order.py` — confirms test files were committed before implementation files
6. Run `scripts/check_test_tampering.py` — confirms test assertions were NOT weakened to pass

### Post-build
- Run `scripts/check_coverage_audit.py` — confirms coverage meets threshold
- Story review is handled by Gate 6 in the validation phase (mandatory, blocking)

## Build file creation

Before starting implementation, create a build state file:
1. Copy `specs/templates/build-template.yaml` to `_work/build/sc-[ID].yaml`
2. Populate with story ID, gate statuses (all initially `pending`), timestamps
3. Update gate statuses as each enforcement gate passes or fails
4. This file persists build state between sessions

## Stale story detection

Before starting a new build, check for stale stories:
- Query stories with status `building` that have no commits in the last 48 hours
- Warn the user about stale stories and suggest resolution (resume or reset)

## Dev comment checking

Before building, check the story for dev comments (from Shortcut or tracker):
- Read any `dev_comments` field in the story file
- Apply dev comments as additional constraints during implementation

## Artefact checklist (must exist after /build)
- [ ] Implementation code (files listed in story scope)
- [ ] Tests (unit + e2e as applicable)
- [ ] `_work/build/sc-[ID].yaml` — build state file with all gates recorded
- [ ] UX spec updated if new pages/flows introduced (wireframes, sitemap, design doc)
- [ ] `specs/feature-tracker.yaml` — updated with status: validated (or escalated)
- [ ] PR created and **URL shared with the user** — always output the PR URL in your response after `gh pr create`
