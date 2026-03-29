# Phase 3: Implement

## Responsible agent
`developer`

## Objective
Implement all features defined in the spec, in the implementation plan's order.

## Prerequisites
- Phase 2 (Scaffold) validated
- Project that compiles and starts
- Read `rules/coding-standards.md` and `rules/test-quality.md` before writing any code

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

**Before writing any test**, read `test_intentions` from the story file (`specs/stories/[feature-id].yaml`). Each intention = one test function. Copy oracle values, never guess.

**API / backend tests:**
1. Write integration tests for every endpoint added or modified:
   - Happy path: valid data → correct response (status code + body)
   - Validation: invalid data → proper error response (status 400/422, not 500)
   - Auth: authenticated endpoints return 401 without token, correct data with token
   - Edge cases: duplicate entries, not found, etc.
2. Write unit tests for any non-trivial business logic in services
3. **Every numeric assertion on a computed value MUST have an `# ORACLE:` comment** showing step-by-step math (see `rules/test-quality.md` Rule 2)
4. **Write-path tests must call real write functions**, then query to verify — not INSERT fixture data + GET

**UI tests (if applicable):**
5. Write component tests for key interactions (form submit, navigation, error display)
6. API mocks must return what the backend actually sends, not what the frontend expects

**Run all tests** — they must all pass before proceeding.

> **Tests are NOT skippable.** Do not defer tests to "later" or a separate phase. Every feature ships with its tests. The test suite is the non-regression safety net for all subsequent features.
> **Oracle blocks are NOT optional.** Every `pytest.approx()`, `toBeCloseTo()`, or numeric `==` on a computed field needs an ORACLE comment.

#### Step 5b: Test reconciliation (MANDATORY)
After writing tests, reconcile against CURRENT spec and quality rules:
1. Re-read story file `specs/stories/[feature-id].yaml` — specs may have changed since you started
2. Re-read `rules/test-quality.md` — quality rules may have evolved
3. Identify gaps: missing tests, tests not matching current ACs, tests violating current rules
4. Fix all gaps before proceeding
5. Run enforcement scripts (`scripts/check_*.py`)

#### Step 5c: LLM fault scenario generation (backend/business logic only)
For each business rule or formula in the feature:
1. Generate 3-5 realistic fault scenarios (wrong field, missing accumulation, off-by-one, null propagation, stale state, wrong aggregation, boundary confusion, type coercion)
2. Each scenario: target file, target function, business rule, fault description, test oracle (concrete inputs -> correct vs faulty output)
3. Write a targeted test for each scenario
4. Run tests — verify targeted tests pass against real code

Skip for: UI-only, infra, migration-only, stories with no business logic.

#### Step 5d: Ensemble test assessment
Score each test function:

| Question | STRONG | FAIL |
|----------|--------|------|
| Calls real production code? | Yes | Only fixture/mock |
| Verifies a business rule from spec? | ORACLE traces to formula | Only assert not-None/status |
| Would fail if fault scenario introduced? | Checks exact value | Too loose |
| ORACLE computation correct? | Math verified | Error or missing |

- **STRONG**: all 4 pass
- **WEAK**: fails 1-2 (log warning, proceed)
- **USELESS**: fails 3-4 (**MUST rewrite before proceeding**)

#### Step 6: Code quality gate (MANDATORY)
Before considering a feature done, you MUST pass **all** checks below. Fix and re-run until every check passes.

**6.0 Manifest validation:**
1. Verify manifest `phase` is `"complete"`
2. Verify all files in git diff are declared in manifest (`files_to_modify` or `files_to_create`)
3. Verify `pipeline_steps` are all `"done"`
4. If manifest scope violation: fix manifest or revert undeclared changes

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
