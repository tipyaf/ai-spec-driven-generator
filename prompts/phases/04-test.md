# Phase 4: Test

## Responsible agent
`tester`

## Objective
Write and run tests to validate that the code meets the spec.

## Prerequisites
- Phase 3 (Implement) validated
- Functional code

## Instructions

You are in **Phase 4 — Tests**. You must write and run the tests.

### Step 1: Unit tests
For each service / business logic module:
1. Test the happy path
2. Test error cases
3. Test edge cases
4. Test validations

### Step 2: Integration tests
For each API endpoint / module interaction:
1. Test valid requests (status 200/201)
2. Test invalid requests (status 400/422)
3. Test authentication (status 401/403) if applicable
4. Test non-existent resources (status 404)

### Step 3: E2E tests (if applicable, for web apps)
For each critical journey:
1. Identify main user journeys
2. Write one E2E test per journey
3. Test on target browsers

### Step 4: Execution
1. Run all tests
2. Measure coverage
3. Identify uncovered areas
4. Add tests for critical uncovered areas

### Step 5: Code quality gate (MANDATORY)
After writing all tests, you MUST pass the code quality gate:

1. Run the linter (`lint` command) — **must pass with zero errors** (test files included)
2. Run the formatter — **must produce no changes**
3. Run the build/compile step — **must succeed**
4. If any of the above fails: **fix the issues immediately and re-run until all pass**

> **This is a blocking gate.** Test code must meet the same quality standards as production code. Do NOT present results to the user until lint, format, and build all pass cleanly.

### Step 6: Report
Produce the test report (see format in `agents/tester.md`)

## Validation criteria
- [ ] All tests pass
- [ ] Coverage > 80% on business logic
- [ ] Each feature's acceptance criteria has a corresponding test
- [ ] No flaky (unstable) tests
- [ ] Critical edge cases are covered
- [ ] **Linter passes with zero errors on all code including tests** (blocking)
- [ ] **Build/compile succeeds** (blocking)
