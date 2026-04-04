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

## Stack profile integration

Before writing ACs, read the stack profiles to auto-generate security and best-practice criteria:

1. Read all stack profiles from `_work/stacks/*.md` (or `stacks/*.md` if `_work/stacks/` does not exist)
2. Extract `security_rules` from each applicable stack profile
3. Extract `best_practices` from each applicable stack profile
4. **Auto-generate AC-SEC-[FEATURE]-NN** from each security rule that applies to the story's scope
5. **Auto-generate AC-BP-[FEATURE]-NN** from each best practice that applies to the story's scope

These auto-generated ACs supplement (not replace) any hand-written ACs.

## Testability tier classification

Every AC MUST be classified into a testability tier:

| Tier | Verify method | When to use |
|---|---|---|
| **Tier 1** (preferred) | `grep`, `bash`, `jq` | Static checks against code artefacts — no running service needed |
| **Tier 2** | `curl`, `playwright`, `cypress` | Requires a live service or browser |
| **Tier 3** (last resort) | `runtime-only` | Cannot be automated — minimize usage |

Rules:
- **AC-SEC-* MUST be Tier 1** — always check code artefacts, not runtime behavior
- **AC-BP-* SHOULD be Tier 1** — prefer static verification
- **`verify: static` is BANNED** — rewrite until you have a shell command

## Test intentions generation

For each AC, generate a `test_intentions` block containing:
- **Intent**: what the test proves (one sentence)
- **Oracle value**: the pre-computed expected result (e.g., expected HTTP status, expected string in output, expected file content)
- **Verify command**: the shell command that produces the actual value to compare against the oracle

This ensures the builder and test engineer have unambiguous pass/fail criteria.

## Spec overlay creation

After writing the story file, create a spec overlay:
1. Write to `_work/spec/sc-[ID].yaml`
2. The overlay captures any spec changes implied by this story (new endpoints, schema changes, config additions)
3. The overlay will be merged with the baseline spec during `/spec` regeneration

## Artefact checklist (must exist after /refine)
- [ ] `specs/stories/[feature-id].yaml` — the build contract
- [ ] `_work/spec/sc-[ID].yaml` — spec overlay (even if empty)
- [ ] `specs/feature-tracker.yaml` — updated with status: refined

## Next step — ALWAYS tell the user

After `/refine` completes, ALWAYS end your response with:

> **Next step:** Story refined and ready to build. Run `/build [feature-name]` to start the TDD pipeline (RED → GREEN → 7 quality gates). You can also `/refine [other-feature]` to refine another feature first.
