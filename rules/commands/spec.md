---
name: spec
description: Start or continue project specification. Guides through Constitution → Scoping → Clarify → Design → Architecture. Use when starting a new project or defining a new feature.
---

## Instructions

You are executing the `/spec` skill from the SDD framework.

**Step 1 — Load the skill definition**
Read `framework/skills/spec/SKILL.md` and follow its instructions exactly.

**Step 2 — Load context**
- Read `memory/[project-name].md` (project state) if it exists
- Read `memory/LESSONS.md` (known pitfalls)
- Read `specs/feature-tracker.yaml` (if it exists)

**Step 3 — Execute the workflow**
Follow the phases defined in the skill file. Load agents one at a time from `framework/agents/[name].md`.

**Key rules:**
- Load ONE agent at a time — never all at once
- Wait for human validation at each phase
- Write artefacts to `specs/` directory
- Update memory after each phase
