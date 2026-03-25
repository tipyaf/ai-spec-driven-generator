---
name: review
description: Final review of all validated features before PR. Code quality, security audit, test coverage. Use when all features are validated.
---

## Instructions

You are executing the `/review` skill from the SDD framework.

**Step 1 — Load the skill definition**
Read `framework/skills/review/SKILL.md` and follow its instructions exactly.

**Step 2 — Load context**
- Read project memory file from `memory/` (project state)
- Read `memory/LESSONS.md` (known pitfalls)
- Read `specs/feature-tracker.yaml` (verify ALL features are `validated`)
- Read ALL `specs/stories/*.yaml` files (all build contracts)

**Step 3 — Phase guard**
Verify ALL features have `status: validated` in the tracker.
If any feature is not validated, list them with their current status and suggest the appropriate skill.

**Step 4 — Execute the workflow**
Follow the review workflow. Load agents from `framework/agents/[name].md` as needed.

**Key rules:**
- 5 review passes: KISS, Static Analysis, Safety, Security Audit, Test Quality
- Re-run EVERY `verify:` command from EVERY story file
- Produce structured PASS/FAIL report
- If FAIL → return issues with file:line references → suggest `/build` to fix
