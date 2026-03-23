---
name: validate
description: Independently validate an implementation against its spec. Takes screenshots, greps for anti-patterns, curls endpoints. Use after development to verify before PR.
---

## Setup — Read these files before starting

1. Read `agents/validator.md` (core instructions)
2. Read the spec (acceptance criteria + acceptance tests)
3. Read the implementation manifest

Only read `agents/validator.ref.md` if you need the report template format.

## Workflow

1. Read the git diff to identify what changed
2. Visual checks: screenshot modified pages, verify design system (UI projects only)
3. Code checks: grep for anti-patterns in modified files
4. Runtime checks: curl endpoints / run commands / call API functions
5. Acceptance tests: execute each test from the spec
6. Produce structured PASS/FAIL report with evidence
7. If FAIL → list issues with file:line and evidence
