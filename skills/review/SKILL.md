---
name: review
description: Review code quality, security, and test coverage for a story or PR. Use before creating a PR or after implementation.
---

## Setup — Read these files before starting

1. Read `agents/reviewer.md` (core instructions)
2. Read `agents/security.md` (core instructions)
3. Read `agents/tester.md` (core instructions — for test quality check)

Only read `.ref.md` files if you need detailed checklists or report templates.

## Workflow

1. Read the git diff or PR changes
2. **Pass 1 — KISS & Readability**: function length, nesting, naming, dead code, duplication
3. **Pass 2 — Static Analysis**: linting, type checking, formatting, anti-patterns
4. **Pass 3 — Safety & Correctness**: secrets, error handling, input validation, SQL safety
5. Run security audit (OWASP Top 10, auth, secrets, dependencies)
6. Verify test quality (no mock-soup, real integration tests, forbidden patterns)
7. Produce structured PASS/FAIL report
8. If FAIL → return issues to developer with file:line references
