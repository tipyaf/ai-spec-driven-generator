# Plan: v4.1.0 — Refine + Build Pipeline Evolution

> **Status**: VALIDATED by user — implementation pending
> **Created**: 2026-04-07
> **Plan file**: `~/.claude/plans/zesty-puzzling-russell.md` (full details)

## Summary

Two major axes of evolution for the framework:

### REFINE
- **Wireframe gate** (UI projects): auto-create/update wireframes in HTML (self-contained, with `data-testid` attributes) when story introduces new UI elements
- **WCAG validation loop**: validate accessibility on wireframes, suggest Pa11y CLI if Node.js available, loop until PASS
- **User validation**: present wireframes, WAIT for explicit approval
- **PM integration**: generic (Shortcut/Jira/GitLab/MCP), attach HTML wireframes + image preview, add validation checklist to tickets

### BUILD — Pipeline restructured (7 → 11 gates)
- **Phase RED**: TU (test-engineer) → quality scan TU (if tool configured) → review TU (reviewer) → validate TU
- **Phase GREEN**: code (builder) → compilation (stack profile command)
- **11 validation gates**: Security → Execute TU → Code quality (tool OR reviewer fallback, NEVER skipped) → Code E2E from wireframes (UI) → WCAG+wireframes (UI) → Execute E2E (UI) → Validate E2E vs wireframes (UI) → AC Validation → Story Review → Code Review (includes 0 console errors) → Final compilation
- **Commit + PR/MR**: single atomic commit after ALL gates PASS, then auto PR/MR (detect gh/glab/az, memorize)

### Key principles
1. Files in English, model responds in user's language
2. Tools optional, never imposed (reviewer fallback for code quality)
3. Specs = absolute source of truth (with or without PM tool)
4. `data-testid` contract: wireframe HTML → production code → E2E selectors
5. User informed of every step in real-time
6. `git add` explicit files only, NEVER `git add .`
7. Test files always cleaned up (pytest tmp_path), never committed

### Files to modify/create
- **22 files to modify** (skills, agents, rules, templates, tests, docs)
- **4 files to create** (check_story_commits.py, migrate script, 2 test files)
- **Full list in plan file**

### Implementation order
1. Templates (build-template, story-template)
2. Rules (agent-conduct)
3. Skills (refine, build)
4. Agents (refinement, ux-ui, developer, validator)
5. Scripts (check_story_commits, setup-hooks)
6. Tests
7. Docs (README, _docs/, CHANGELOG, VERSION)
8. Migration (script + skill)
