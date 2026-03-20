# Phase 3: Implement

## Responsible agent
`developer`

## Objective
Implement all features defined in the spec, in the implementation plan's order.

## Prerequisites
- Phase 2 (Scaffold) validated
- Project that compiles and starts

## Instructions

You are in **Phase 3 — Implementation**. You must code all project features.

### For each feature (in the plan's order):

#### Step 1: Data
1. Create/update the data schema (migration, model)
2. Create associated types/interfaces
3. Create seeders/fixtures if needed

#### Step 2: Business logic
1. Implement services / use cases
2. Implement validations
3. Handle error cases

#### Step 3: API (if applicable)
1. Create endpoints / routes
2. Implement controllers
3. Add input validation (DTOs)
4. Handle error responses

#### Step 4: UI (if applicable)
1. Create components
2. Connect to data (hooks, stores, etc.)
3. Handle states (loading, error, empty)
4. Add user interactions
5. **All visible text MUST use i18n translation keys** — no hardcoded strings in the UI. Add new keys to every supported language file as you go.

#### Step 5: Automated tests (MANDATORY — NOT OPTIONAL)
Tests are part of the feature, not a separate phase. A feature without tests is not done.

**API / backend tests:**
1. Write integration tests for every endpoint added or modified:
   - Happy path: valid data → correct response (status code + body)
   - Validation: invalid data → proper error response (status 400/422, not 500)
   - Auth: authenticated endpoints return 401 without token, correct data with token
   - Edge cases: duplicate entries, not found, etc.
2. Write unit tests for any non-trivial business logic in services

**UI tests (if applicable):**
3. Write component tests for key interactions (form submit, navigation, error display)

**Run all tests** — they must all pass before proceeding.

> **Tests are NOT skippable.** Do not defer tests to "later" or a separate phase. Every feature ships with its tests. The test suite is the non-regression safety net for all subsequent features.

#### Step 6: Code quality gate (MANDATORY)
Before considering a feature done, you MUST pass **all** checks below. Fix and re-run until every check passes.

**Static checks:**
1. Run the linter (`lint` command) — **must pass with zero errors**
2. Run the formatter — **must produce no changes**
3. Run the build/compile step — **must succeed with zero errors/warnings**

**Automated test checks:**
4. Run the full test suite (`test` command) — **must pass with zero failures**
5. New tests from step 5 must be included and passing

**Functional checks:**
6. Start the dev server (if not already running)
7. **Smoke test every endpoint/route added or modified in this feature** with real HTTP requests:
   - Send valid data → verify correct response (status code + body)
   - Send invalid data → verify proper error response (not a 500 or stack trace)
   - Test authenticated endpoints with and without a valid token
8. If the feature has a UI: **verify the page loads and the main interactions work**
9. **Regression check**: run the full test suite to verify previously implemented features are not broken
10. If any check fails: **fix the issue immediately and re-run all checks**

> **This is a blocking gate.** Do NOT move on to the next feature or present results to the user until all static, test, and functional checks pass. A feature that compiles but doesn't work is not done.

### Progress
After each implemented feature, display:
```markdown
### Feature: [name] — ✅ Implemented

**Files created/modified:**
- `path/file.ts` — role

**Tests written:**
- `path/test.spec.ts` — what it covers

**What works:**
- [behavior 1]
- [behavior 2]

**Test results:** X passed, 0 failed

**Progress:** [X/Y] features implemented
```

## Validation criteria
- [ ] All `must-have` features are implemented
- [ ] `should-have` features are implemented
- [ ] **Every feature has automated tests** (blocking — no exceptions)
- [ ] **Full test suite passes with zero failures** (blocking)
- [ ] **Linter passes with zero errors** (blocking — must be fixed before validation)
- [ ] **Build/compile succeeds with zero errors** (blocking)
- [ ] **Code is formatted** (no pending formatting changes)
- [ ] **Every endpoint responds correctly to real requests** (blocking — not just compilation)
- [ ] **Every UI page loads and main interactions work** (blocking)
- [ ] Each feature meets its acceptance criteria
