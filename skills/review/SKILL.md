---
name: review
description: Review code quality, security, and test coverage for all validated features before PR. Use when all features are validated and ready for final review.
---

## Phase guard — verify before proceeding

**Prerequisites** (check filesystem):
1. `specs/feature-tracker.yaml` must exist
2. ALL features in the tracker must have `status: validated`
   - If ANY feature has a different status → Tell user which features are not ready
   - Suggest `/build` or `/validate` for incomplete features

**If prerequisites are not met** → Tell user: "Some features still need validation" → list them with status

## Setup — Read these files before starting

1. Read `agents/reviewer.md` (core instructions)
2. Read `agents/security.md` (core instructions)
3. Read `agents/tester.md` (core instructions — for test quality check)
4. Read `specs/feature-tracker.yaml` (verify all validated)
5. Read ALL `specs/stories/*.yaml` files (all build contracts)

Only read `.ref.md` files if you need detailed checklists or report templates.

## Two review modes

This skill covers two distinct review types:

### Story review (per-story, runs after each build)
- Dispatches `agents/story-reviewer.md`
- Runs immediately after a single story's build completes
- Verifies every AC in that story's file one by one
- Posts a structured PASS/FAIL verdict per AC
- Does NOT look at other stories or cross-feature concerns

### Code review (all features, runs at end)
- Dispatches `agents/reviewer.md`
- Runs when ALL features are validated and ready for PR
- Reviews all changes together for cross-cutting concerns
- Covers code quality, security, architecture, and test quality

## Workflow (Code review — full)

1. Read the git diff or PR changes
2. **Pass 1 — KISS & Readability**: function length, nesting, naming, dead code, duplication
3. **Pass 2 — Static Analysis**: linting, type checking, formatting, anti-patterns
4. **Pass 3 — Safety & Correctness**: secrets, error handling, input validation, SQL safety
5. **Pass 4 — Anti-patterns check**: read `anti_patterns` from stack profiles (`stacks/*.md`), grep for violations in changed files
6. Run security audit (OWASP Top 10, auth, secrets, dependencies)
7. Verify test quality (no mock-soup, real integration tests, forbidden patterns)
8. **MSW contract validation**: if the project uses MSW (Mock Service Worker), verify that mock handlers match the actual API contracts defined in the spec
9. **Verify ALL ACs across ALL stories**: re-run every `verify:` command from every story file
10. Produce structured PASS/FAIL report
11. If FAIL → return issues to developer with file:line references → suggest `/build` to fix
