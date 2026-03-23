---
name: refine
description: Refine a user story — break it down into actionable tasks with acceptance criteria and acceptance tests. Use when starting work on a new feature or story.
---

## Setup — Read these files before starting

1. Read `agents/refinement.md` (core instructions)
2. Read `agents/product-owner.md` (core instructions — for AC format)
3. Read stack profiles from `stacks/` (for auto-generating AC-SEC-* and AC-BP-*)

Only read `.ref.md` files if you need ticket templates or AC examples.

## Workflow

1. Read the story/feature from the spec or user description
2. Decompose into atomic user stories (implementable in 1 session)
3. For each story: write Given/When/Then acceptance criteria
4. Auto-generate AC-SEC-* and AC-BP-* from stack profiles
5. Add machine-verifiable acceptance tests (visual, runtime, grep, e2e)
6. If feature is large (L/XL): propose breakdown options to user
7. Present the breakdown to the user for validation
8. Create tickets in Shortcut (if configured)
