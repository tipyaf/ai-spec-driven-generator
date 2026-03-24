---
name: validate
description: Independently validate an implementation against its story file. Executes every verify: command, takes screenshots, greps for anti-patterns. Use after development to verify before review.
---

## Phase guard — verify before proceeding

**Prerequisites** (check filesystem):
1. `specs/feature-tracker.yaml` must exist
2. The target feature must have `status: building` or `status: testing` in the tracker
3. `specs/stories/[feature-id].yaml` must exist (the build contract)

**If any prerequisite is missing** → Tell user: "Nothing to validate yet" → suggest `/build`

## Setup — Read these files before starting

1. Read `agents/validator.md` (core instructions)
2. Read `specs/stories/[feature-id].yaml` (the build contract — ACs with verify commands)
3. Read `memory/LESSONS.md` (known patterns)
4. Read stack profiles from `stacks/` (forbidden patterns)

Only read `agents/validator.ref.md` if you need the report template format.

## Workflow

1. Read the story file — extract ALL `verify:` commands
2. Read the git diff to identify what changed
3. **Execute EVERY `verify:` command** from the story file:
   - Tier 1 (`grep`/`bash`): run directly, capture output
   - Tier 2 (`curl`/`playwright`): start dev server if needed, run command
   - Tier 3 (`runtime-only`): document what was checked and how
4. Visual checks (UI projects only): screenshot modified pages, verify design system
5. Code checks: grep for anti-patterns in modified files (from stack profiles)
6. Scope check: verify git diff only touches files listed in story's `scope` section
7. Produce structured PASS/FAIL report with evidence for each AC
8. Update `specs/feature-tracker.yaml`:
   - ALL PASS → status: `validated`
   - ANY FAIL → increment `cycles`, keep status: `testing`
   - cycles >= 3 → add escalation note, keep status: `testing`

## Artefact checklist
- [ ] Validation report (structured PASS/FAIL with evidence)
- [ ] `specs/feature-tracker.yaml` — updated
