# Phase 4: Test Audit & Coverage

## Responsible agent
`tester`

## Objective
Audit existing tests for coverage gaps, add missing edge cases, write E2E tests for critical user journeys, and produce a test report.

> **Note:** By this phase, every feature should already have automated tests (written during Phase 3). This phase is NOT where tests are written for the first time — it is an audit and reinforcement phase.

## Prerequisites
- Phase 3 (Implement) validated
- Every feature has automated tests (unit + integration)
- Full test suite passes

## Instructions

You are in **Phase 4 — Test Audit**. You must verify test quality, fill coverage gaps, and add E2E tests.

### Step 1: Audit existing tests
1. Run the full test suite — all tests must pass
2. Measure code coverage
3. Identify areas with coverage below 80% on business logic
4. Identify missing edge cases for each feature

### Step 2: Fill coverage gaps
For each under-tested area:
1. Add unit tests for uncovered branches and edge cases
2. Add integration tests for untested error paths
3. Add validation tests for boundary values
4. Prioritize: business logic > controllers > utilities

### Step 3: E2E tests (if applicable, for web apps)
For each critical user journey:
1. Identify main user journeys from the spec (e.g., register → login → create profile → launch sourcing)
2. Write one E2E test per journey
3. Test the full flow end-to-end (frontend → API → database)

### Step 4: Non-regression verification
1. Run the **full test suite** (unit + integration + E2E)
2. Verify zero failures
3. Check for flaky tests — re-run any failures to confirm they are deterministic
4. Fix any flaky tests

### Step 5: Code quality gate (MANDATORY)
After writing all tests, you MUST pass the code quality gate:

1. Run the linter (`lint` command) — **must pass with zero errors** (test files included)
2. Run the formatter — **must produce no changes**
3. Run the build/compile step — **must succeed**
4. Run the full test suite — **must pass with zero failures**
5. If any of the above fails: **fix the issues immediately and re-run until all pass**

> **This is a blocking gate.** Test code must meet the same quality standards as production code.

### Step 6: Report
Produce the test report:
```markdown
## Test Report

**Suite:** [test framework name]
**Total tests:** X
**Passed:** X | **Failed:** 0 | **Skipped:** 0

### Coverage
| Module | Statements | Branches | Functions | Lines |
|--------|-----------|----------|-----------|-------|
| ... | X% | X% | X% | X% |

### Tests by feature
| Feature | Unit | Integration | E2E | Total |
|---------|------|-------------|-----|-------|
| ... | X | X | X | X |

### Gaps identified and filled
- [gap 1] → [test added]
- [gap 2] → [test added]
```

## Validation criteria
- [ ] All tests pass (zero failures, zero skipped)
- [ ] Coverage > 80% on business logic
- [ ] Each feature's acceptance criteria has a corresponding test
- [ ] No flaky (unstable) tests
- [ ] Critical edge cases are covered
- [ ] E2E tests cover main user journeys (if web app)
- [ ] **Linter passes with zero errors on all code including tests** (blocking)
- [ ] **Build/compile succeeds** (blocking)
