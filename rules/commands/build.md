---
name: build
description: Build/implement a refined story. Reads the story file, writes code, runs validation gates. Usage: /build [feature-id]
---

## Instructions

You are executing the `/build` skill from the SDD framework.

**Argument**: $ARGUMENTS (the feature ID to build, e.g., "candidate-profile")

**Step 1 — Load the skill definition**
Read `framework/skills/build/SKILL.md` and follow its instructions exactly.

**Step 2 — Load context**
- Read project memory file from `memory/` (project state)
- Read `memory/LESSONS.md` (known pitfalls)
- Read `specs/feature-tracker.yaml` (verify feature is `refined`)
- Read `specs/stories/$ARGUMENTS.yaml` (THE build contract)
- Read `specs/constitution.md` (principles)

**Step 3 — Phase guard**
Verify prerequisites from the skill file. Feature must be `status: refined` and story file must exist.
If missing, tell the user what's needed and suggest `/refine`.

**Step 4 — Load stack profiles**
Read relevant stack profiles from `stacks/` directory for coding rules.

**Step 5 — Execute the workflow**
Follow the build + validate workflow. Load agents from `framework/agents/[name].md` as needed.

**Key rules:**
- Only touch files listed in the story's `scope` section
- Write tests alongside code (not after)
- Run ALL 5 validation gates after implementation
- Update `specs/feature-tracker.yaml` with status changes
- Max 3 cycles — escalate to human after that
