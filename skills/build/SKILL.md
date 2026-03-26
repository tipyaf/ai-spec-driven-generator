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

### Phase 3.5: Validate (5 sequential gates)
Run these quality gates in order. ALL must pass.

**Gate 1 — Security**: check OWASP patterns, stack forbidden patterns, AC-SEC-* verify commands
**Gate 2 — Tests**: run unit tests + e2e tests (if applicable)
**Gate 3 — UI** (if UI project): WCAG check + wireframe conformity
**Gate 4 — AC Validation**: execute EVERY `verify:` command from the story file
**Gate 5 — Review**: code quality, scope conformity (only touched listed files?)

### Verdict
- **ALL PASS**: Update tracker status to `testing`, then `validated`. Report to user.
- **ANY FAIL**: Increment `cycles` in tracker. Fix and re-validate.
- **cycles >= 3**: ESCALATE to human. Do NOT attempt a 4th cycle. Update tracker notes with what failed and why.

## Artefact checklist (must exist after /build)
- [ ] Implementation code (files listed in story scope)
- [ ] Tests (unit + e2e as applicable)
- [ ] `specs/feature-tracker.yaml` — updated with status: validated (or escalated)
- [ ] PR created and **URL shared with the user** — always output the PR URL in your response after `gh pr create`
