---
name: build
description: Build/implement a refined story. Reads the spec, follows the manifest, writes code, runs validation. Use after a story has been refined.
---

## Setup — Read these files before starting

1. Read `agents/developer.md` (core instructions)
2. Read `agents/validator.md` (core instructions)
3. Read `memory/LESSONS.md` (known pitfalls)
4. Read the implementation manifest from the architecture plan

Only read `agents/developer.ref.md` or `agents/validator.ref.md` if you need a specific template during implementation.

## Workflow

1. Read the refined story and its acceptance criteria
2. Read LESSONS.md — apply relevant lessons as constraints
3. Read the implementation manifest — only touch listed files
4. Follow the developer agent workflow to implement
5. Self-check against ALL acceptance criteria
6. Run the validator agent checks (Phase 3.5):
   - Visual checks (UI projects), code checks, runtime checks, acceptance tests
7. If validation fails → fix and re-validate (max 3 cycles)
8. Report structured PASS/FAIL status to user
