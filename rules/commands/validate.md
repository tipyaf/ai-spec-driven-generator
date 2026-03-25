---
name: validate
description: Independently validate an implementation against its story file. Executes every verify command. Usage: /validate [feature-id]
---

## Instructions

You are executing the `/validate` skill from the SDD framework.

**Argument**: $ARGUMENTS (the feature ID to validate, e.g., "candidate-profile")

**Step 1 — Load the skill definition**
Read `framework/skills/validate/SKILL.md` and follow its instructions exactly.

**Step 2 — Load context**
- Read project memory file from `memory/` (project state)
- Read `memory/LESSONS.md` (known pitfalls)
- Read `specs/feature-tracker.yaml` (verify feature is `building` or `testing`)
- Read `specs/stories/$ARGUMENTS.yaml` (the build contract with verify commands)

**Step 3 — Phase guard**
Verify prerequisites from the skill file. Feature must be `status: building` or `status: testing`.
If missing, tell the user what's needed and suggest `/build`.

**Step 4 — Execute the workflow**
Follow the validation workflow. Execute EVERY `verify:` command from the story file.

**Key rules:**
- Execute EVERY `verify:` command — no skipping
- Produce structured PASS/FAIL report with evidence
- Update `specs/feature-tracker.yaml` with results
- ALL PASS → status: validated
- ANY FAIL → increment cycles, fix and re-validate
- cycles >= 3 → ESCALATE to human, do NOT attempt 4th cycle
