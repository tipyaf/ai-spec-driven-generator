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

#### Step 5: Code quality gate (MANDATORY)
Before considering a feature done, you MUST pass **all** checks below. Fix and re-run until every check passes.

**Static checks:**
1. Run the linter (`lint` command) — **must pass with zero errors**
2. Run the formatter — **must produce no changes**
3. Run the build/compile step — **must succeed with zero errors/warnings**

**Functional checks:**
4. Start the dev server (if not already running)
5. **Test every endpoint/route added or modified in this feature** with real HTTP requests:
   - Send valid data → verify correct response (status code + body)
   - Send invalid data → verify proper error response (not a 500 or stack trace)
   - Test authenticated endpoints with and without a valid token
6. If the feature has a UI: **verify the page loads and the main interactions work**
7. **Regression check**: verify that previously implemented features still respond correctly (re-run their smoke tests)
8. If any check fails: **fix the issue immediately and re-run all checks**

> **This is a blocking gate.** Do NOT move on to the next feature or present results to the user until all static and functional checks pass. A feature that compiles but doesn't work is not done.

### Progress
After each implemented feature, display:
```markdown
### Feature: [name] — ✅ Implemented

**Files created/modified:**
- `path/file.ts` — role

**What works:**
- [behavior 1]
- [behavior 2]

**Progress:** [X/Y] features implemented
```

## Validation criteria
- [ ] All `must-have` features are implemented
- [ ] `should-have` features are implemented
- [ ] **Linter passes with zero errors** (blocking — must be fixed before validation)
- [ ] **Build/compile succeeds with zero errors** (blocking)
- [ ] **Code is formatted** (no pending formatting changes)
- [ ] **Every endpoint responds correctly to real requests** (blocking — not just compilation)
- [ ] **Every UI page loads and main interactions work** (blocking)
- [ ] Each feature meets its acceptance criteria
