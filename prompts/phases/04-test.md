# Phase 4: Test Audit & Coverage (Auto-Validated)

## Responsible agent
`tester`

## Objective
Audit existing tests for coverage gaps, add missing edge cases, write E2E tests (Playwright) for every modified page, run WCAG accessibility audits, perform visual regression checks, and produce a machine-readable test report. This phase is **fully auto-validated** — if all gates pass, the orchestrator proceeds automatically. No human validation is needed.

> **Note:** By this phase, every feature should already have automated tests (written during Phase 3). This phase is NOT where tests are written for the first time — it is an audit and reinforcement phase that adds E2E, accessibility, and visual regression coverage.

## Prerequisites
- Phase 3 (Implement) validated
- Every feature has automated tests (unit + integration)
- Full test suite passes

## Instructions

You are in **Phase 4 — Test Audit (Auto-Validated)**. You must verify test quality, fill coverage gaps, add E2E and accessibility tests, and produce an automated pass/fail result.

### Step 1: Audit existing tests
1. Run the full test suite — all tests must pass
2. Measure code coverage
3. Identify areas with coverage below 80% on business logic
4. Identify missing edge cases for each feature

### Step 2: Fill coverage gaps (Unit Tests)
For each under-tested area:
1. Add unit tests for uncovered branches and edge cases
2. Add integration tests for untested error paths
3. Add validation tests for boundary values (null, empty, 0, -1, MAX_INT)
4. Mock all external dependencies in unit tests
5. Prioritize: business logic > controllers > utilities

### Step 3: E2E / Integration tests
> Adapt the tool and strategy to the project type:
> - **Web**: Playwright — test pages at responsive breakpoints (320px, 768px, 1440px)
> - **Mobile**: Detox/Appium — test screens on device simulators
> - **CLI**: Command invocation tests — verify exit codes, stdout, stderr
> - **API**: Integration tests (supertest, httpie) — verify endpoints end-to-end
> - **Library**: Unit + integration tests — verify public API behaves as documented

For every modified interface:
1. Write at least one E2E/integration test covering the user flow (navigation/invocation, interaction, expected result)
2. Test at three responsive breakpoints: mobile (320px), tablet (768px), desktop (1440px) (**web/mobile projects only**)
3. Take screenshots at each breakpoint for visual regression comparison (**UI projects only**)
4. Test the full flow end-to-end (frontend -> API -> database, or CLI -> service -> output)
5. Identify main user journeys from the spec and write one E2E test per journey

### Step 4: WCAG Accessibility Audit
> **Applies to**: web, mobile, desktop UI projects
> **Does NOT apply to**: API, CLI, library, embedded, data pipeline projects. Skip to Step 5.

For every modified page/screen:
1. Run `@axe-core/playwright` (or equivalent) with WCAG 2.1 AA tags
2. Verify 0 violations at AA level
3. Check contrast ratios: 4.5:1 for normal text, 3:1 for large text and UI components
4. Test keyboard navigation: tab through all interactive elements, verify logical focus order
5. Verify ARIA roles and accessible labels on all interactive elements
6. Run the audit at each responsive breakpoint (320px, 768px, 1440px) (**web projects only**)

### Step 5: Non-regression verification
1. Run the **full test suite** (unit + integration + E2E + accessibility)
2. Verify zero failures
3. Check for flaky tests — re-run any failures to confirm they are deterministic
4. Fix any flaky tests

### Step 6: Code quality gate (MANDATORY)
After writing all tests, you MUST pass the code quality gate:

1. Run the linter (`lint` command) — **must pass with zero errors** (test files included)
2. Run the formatter — **must produce no changes**
3. Run the build/compile step — **must succeed**
4. Run the full test suite — **must pass with zero failures**
5. If any of the above fails: **fix the issues immediately and re-run until all pass**

> **This is a blocking gate.** Test code must meet the same quality standards as production code.

### Step 7: Report
Produce the test report:
```markdown
## Test Report

**Suite:** [test framework name]
**Total tests:** X
**Passed:** X | **Failed:** 0 | **Skipped:** 0

### Automated Gate Results
| Gate | Status | Detail |
|------|--------|--------|
| Unit tests | PASS/FAIL | X passed / Y total |
| E2E tests | PASS/FAIL | X passed / Y total |
| WCAG audit | PASS/FAIL | X violations found |
| Visual regression | PASS/FAIL | X screenshots differ |
| Code coverage | PASS/FAIL | X% (threshold: Y%) |
| Linter | PASS/FAIL | X errors |
| Build | PASS/FAIL | — |

**Overall: ALL GATES PASSED / X GATE(S) FAILED**

### Coverage
| Module | Statements | Branches | Functions | Lines |
|--------|-----------|----------|-----------|-------|
| ... | X% | X% | X% | X% |

### Tests by feature
| Feature | Unit | Integration | E2E | Accessibility | Total |
|---------|------|-------------|-----|---------------|-------|
| ... | X | X | X | X | X |

### Gaps identified and filled
- [gap 1] -> [test added]
- [gap 2] -> [test added]

### Escalations (if any)
- [feature]: [reason it cannot be tested automatically] — MANUAL_REVIEW_REQUIRED
```

## Validation criteria (all machine-checkable)
- [ ] All unit tests pass (exit code 0)
- [ ] All E2E tests pass (Playwright exit code 0)
- [ ] WCAG audit passes (0 AA violations via axe-core) — **UI projects only, N/A for API/CLI/library/embedded**
- [ ] No visual regression in screenshots (0 unexpected differences) — **UI projects only, N/A for API/CLI/library/embedded**
- [ ] Test coverage meets project minimum (if defined)
- [ ] Each feature's acceptance criteria has a corresponding test
- [ ] No flaky (unstable) tests
- [ ] Critical edge cases are covered
- [ ] **Linter passes with zero errors on all code including tests** (blocking)
- [ ] **Build/compile succeeds** (blocking)

## Auto-validation flow
- **All criteria pass** — Phase 4 is complete. The orchestrator proceeds automatically to the next phase. No human sign-off required.
- **Any criterion fails** — The feature is sent back to the developer with a detailed failure report (same loop as Phase 3.5 Validate). The developer fixes and resubmits for re-testing.

## Escalation: untestable features
If a test cannot be written for a specific feature (e.g., external API with no sandbox, hardware dependency, third-party OAuth flow):
1. Document exactly WHY the test cannot be automated
2. List what manual verification would be needed
3. Flag the feature with `ESCALATION: MANUAL_REVIEW_REQUIRED` in the test report
4. This is the **only case** where human review is acceptable in Phase 4
