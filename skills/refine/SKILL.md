---
name: refine
description: Refine a user story — break it down into actionable tasks with structured acceptance criteria (AC-FUNC, AC-SEC, AC-BP) each with a verify: shell command. Use when starting work on a new feature or story.
---

## Phase guard — verify before proceeding

**Prerequisites** (check filesystem):
1. `specs/[project-name].yaml` must exist (spec done)
2. `specs/[project-name]-arch.md` must exist (architecture done)
3. `specs/feature-tracker.yaml` must exist (tracking initialized)
4. The target feature must have `status: pending` in the tracker

**If any prerequisite is missing** → Tell user: "Let's define the project first" → suggest `/spec`

## Setup — Read these files before starting

1. Read `agents/refinement.md` (core instructions)
2. Read `agents/product-owner.md` (core instructions — for AC format)
3. Read stack profiles from `stacks/` (for auto-generating AC-SEC-* and AC-BP-*)
4. Read `specs/feature-tracker.yaml` (current state)
5. Read `memory/LESSONS.md` (known pitfalls to avoid in ACs)

Only read `.ref.md` files if you need ticket templates or AC examples.

## Workflow

1. Read `specs/feature-tracker.yaml` — pick the next `pending` feature (or let user choose)
2. Read the feature from the spec YAML
3. Decompose into atomic user stories (implementable in 1 session)
4. For each story: write acceptance criteria in structured format:
   - **AC-FUNC-[FEATURE]-NN**: functional (Given/When/Then)
   - **AC-SEC-[FEATURE]-NN**: security (auto-generated from stack profile)
   - **AC-BP-[FEATURE]-NN**: best practices (auto-generated from stack profile)
5. **EVERY AC MUST have a `verify:` shell command** — no exceptions:
   - Tier 1 (preferred): `verify: grep` or `verify: bash` — runs without live service
   - Tier 2: `verify: curl` or `verify: playwright` — requires live service
   - Tier 3 (last resort): `verify: runtime-only` — minimize usage
   - **`verify: static` is BANNED** — rewrite until you have a shell command
   - **AC-SEC-* MUST be Tier 1** — check code artefacts, not runtime behavior
6. Define the scope (files to create/modify/read)
7. Identify edge cases
8. If feature is large (L/XL): propose breakdown options to user
9. Present the breakdown to the user for validation
10. On validation:
    - Write story file to `specs/stories/[feature-id].yaml` (from template)
    - Update `specs/feature-tracker.yaml`: set feature status to `refined`, set `story_file` path
    - Create tickets in Shortcut (if configured)

## Artefact checklist (must exist after /refine)
- [ ] `specs/stories/[feature-id].yaml` — the build contract
- [ ] `specs/feature-tracker.yaml` — updated with status: refined
