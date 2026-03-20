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
Before considering a feature done, you MUST pass the code quality gate:

1. Run the linter (`lint` command) — **must pass with zero errors**
2. Run the formatter — **must produce no changes**
3. Run the build/compile step — **must succeed with zero errors/warnings**
4. If any of the above fails: **fix the issues immediately and re-run until all pass**

> **This is a blocking gate.** Do NOT move on to the next feature or present results to the user until lint, format, and build all pass cleanly. This applies to every feature, every time.

#### Step 6: Functional verification
1. Manually test that the feature works
2. Verify previous features are not broken

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
- [ ] Each feature meets its acceptance criteria
