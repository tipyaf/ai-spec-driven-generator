---
name: refine
description: Refine a feature into actionable stories with structured acceptance criteria and verify commands. Usage: /refine [feature-id]
---

## Instructions

You are executing the `/refine` skill from the SDD framework.

**Argument**: $ARGUMENTS (the feature ID to refine, e.g., "candidate-profile")

**Step 0 — Worktree check**
If a feature branch is currently checked out (not `main`/`develop`), create a worktree before proceeding:
`git worktree add .worktrees/chore-refine-[id] -b chore/refine-[id] origin/main`
All refinement artefacts (story files, tracker updates, CLAUDE.md changes) go in the worktree branch.

**Step 1 — Load the skill definition**
Read `framework/skills/refine/SKILL.md` and follow its instructions exactly.

**Step 2 — Load context**
- Read project memory file from `memory/` (project state)
- Read `memory/LESSONS.md` (known pitfalls)
- Read `specs/feature-tracker.yaml` (feature states)
- Read the project spec YAML from `specs/`
- Read the architecture doc from `specs/`
- Read `specs/constitution.md` (principles)
- Read the clarifications doc from `specs/` (resolved ambiguities)

**Step 3 — Phase guard**
Verify prerequisites from the skill file. If missing, tell the user what's needed.

**Step 4 — Execute the workflow**
Follow the refinement workflow. Load agents from `framework/agents/[name].md` as needed.

**Key rules:**
- Every AC MUST have a `verify:` shell command — no exceptions
- `verify: static` is BANNED — rewrite until you have a real command
- AC-SEC-* must be Tier 1 (grep/bash, not runtime)
- Present breakdown to user for validation before writing story file
- Update `specs/feature-tracker.yaml` after writing story
