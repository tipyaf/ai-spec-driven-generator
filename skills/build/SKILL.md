---
name: build
description: Build/implement a refined story using strict TDD (RED → GREEN → 11 quality gates). Reads the story file, writes failing tests first, then code, then validates through security, tests, compilation, E2E, WCAG, AC validation, and code review.
---

## Phase guard — verify before proceeding

**Prerequisites** (check filesystem):
1. `specs/feature-tracker.yaml` must exist
2. The target feature must have `status: refined` in the tracker
3. `specs/stories/[feature-id].yaml` must exist (the build contract)
4. Read the story file — verify ALL ACs have a `verify:` field

**If any prerequisite is missing** → Tell user: "This story needs refinement first" → suggest `/refine`

## Setup — Read these files before starting

1. Read `agents/developer.md` (core instructions)
2. Read `agents/validator.md` (core instructions)
3. Read `memory/LESSONS.md` (known pitfalls)
4. Read `specs/stories/[feature-id].yaml` (THE build contract — this is your scope)
5. Read stack profiles from `stacks/` (coding rules, compilation commands, test commands)

Only read `.ref.md` files if you need a specific template during implementation.

## Workflow

### Phase 3: RED — Unit tests first (TDD)

> **Inform the user**: "Starting RED phase — writing unit tests from story ACs..."

1. Read the story file — this defines your ENTIRE scope
2. Read LESSONS.md — apply relevant lessons as constraints
3. Update `specs/feature-tracker.yaml`: set feature status to `building`

#### Step 3.1 — Create unit tests (test-engineer)
1. Dispatch `agents/test-engineer.md` to write failing tests based on story ACs and `test_intentions`
2. Run `scripts/check_red_phase.py` — confirms tests exist AND fail (red)
3. Run `scripts/check_test_intentions.py --story [ID] --spec-path specs/stories/[feature-id].yaml` — confirms every spec test_intention has a corresponding test
4. Run `scripts/check_msw_contracts.py` — confirms API mock handlers use backend field names (endpoint stories only)
5. Update `_work/build/sc-[ID].yaml` → `red_phase.tdd_red.status: done`

> **Inform the user**: "RED phase — unit tests written. Running quality checks..."

#### Step 3.2 — Quality scan on unit tests
Run code quality tool scoped to test files only (if configured in stack profile):
- If SonarQube or other quality tool configured → scan test files only (`--inclusions=**/*.test.*,**/*.spec.*`)
- If no quality tool configured → **SKIP** (not fail)
- **If FAIL** → return to Step 3.1, fix tests, re-scan. Loop until PASS.
- Update `_work/build/sc-[ID].yaml` → `red_phase.quality_scan.status`

> **Inform the user**: "Quality scan on tests — [PASS/FAIL/SKIPPED]"

#### Step 3.3 — Review unit tests
Dispatch `agents/reviewer.md` to review test files only:
- Are tests testing the right things? (match story ACs and test_intentions)
- Are assertions strong? (no weak equality, no snapshot-only, no mock-soup)
- Is test structure clean? (arrange/act/assert, descriptive names)
- Are oracle values correctly copied from story file?
- **If FAIL** → return to Step 3.1, fix tests based on review feedback. Loop until PASS.
- Update `_work/build/sc-[ID].yaml` → `red_phase.review.status`

> **Inform the user**: "Unit test review — [PASS/FAIL]"

#### Step 3.4 — Validate RED phase
If Steps 3.2 AND 3.3 both PASS (or 3.2 SKIPPED + 3.3 PASS) → proceed to GREEN phase.
Update `_work/build/sc-[ID].yaml` → `red_phase.status: validated`

> **Inform the user**: "RED phase validated ✓ — proceeding to GREEN phase (implementation)..."

### Phase 4: GREEN — Implementation

> **Inform the user**: "Starting GREEN phase — writing production code..."

**Only touch files listed in the story's `scope` section.** If an unlisted file is needed, document it and add it to scope with justification.

#### Step 4.1 — Code (builder)
1. Dispatch the appropriate builder agent (see dispatch table below)
2. Builder writes production code to make all unit tests pass
3. Follow the developer agent workflow
4. Self-check against ALL acceptance criteria
5. Run `scripts/check_tdd_order.py` — confirms test files committed before implementation
6. Run `scripts/check_test_tampering.py` — confirms test assertions NOT weakened
7. Update `_work/build/sc-[ID].yaml` → `green_phase.tdd_green.status`

> **Inform the user**: "Implementation complete. Running compilation..."

#### Step 4.2 — Compilation
Run the project's build/compile command from the stack profile:
- The compilation command is defined in the stack profile or project config (e.g., `tsc --noEmit`, `npm run build`, `go build ./...`, `mvn compile`, `cargo build`, `python -m py_compile`)
- The framework does NOT hardcode compilation commands — it reads them from the stack profile
- **If compilation FAILS** → return to Step 4.1, fix code, recompile. Loop until PASS.
- Update `_work/build/sc-[ID].yaml` → `green_phase.compilation.status`

> **Inform the user**: "Compilation — [PASS/FAIL]"

### Phase 5: Validate (11 sequential gates)

Run these quality gates in order. ALL must pass.

> **Inform the user**: "Starting validation — 11 quality gates..."

**Gate 1 — Security**: Check OWASP patterns, stack forbidden patterns, AC-SEC-* verify commands.
→ *On FAIL*: fix security issues, re-run Gate 1. Loop until PASS.
→ Update `_work/build/sc-[ID].yaml` → `gates.security.status`

> **Inform the user**: "Gate 1 Security — [PASS/FAIL]"

**Gate 2 — Execute unit tests**: Run unit tests only (test command from stack profile). All must pass.
→ *On FAIL*: return to Step 4.1 (builder), fix code to satisfy TDD. Re-run from Gate 2.
→ Update `_work/build/sc-[ID].yaml` → `gates.unit_tests.status`

> **Inform the user**: "Gate 2 Unit Tests — [PASS/FAIL] ([N] pass, [M] fail)"

**Gate 3 — Code quality**: This gate is **NEVER skipped**.
- If code quality tool configured (SonarQube or other) → run full scan + coverage report
- If no tool configured → dispatch `agents/reviewer.md` with extended scope: code quality, maintainability, readability, patterns, security. The reviewer's 3 passes (KISS/readability, static analysis, safety/correctness) serve as the quality gate.
→ *On FAIL*: fix code quality issues, re-run unit tests (Gate 2), then re-run Gate 3.
→ Update `_work/build/sc-[ID].yaml` → `gates.code_quality.status`

> **Inform the user**: "Gate 3 Code Quality — [PASS/FAIL] (method: [tool/reviewer])"

**Gate 4 — E2E code from wireframes** (UI projects only): Write E2E tests based on wireframes from `specs/[project]-ux.md` (referenced via story `ux_ref:`). E2E tests MUST use the `data-testid` attributes from wireframes as selectors. E2E tests validate user flows, visual rendering, responsive breakpoints, and all states (empty/loading/error/success).
→ Skip for non-UI projects.
→ Update `_work/build/sc-[ID].yaml` → `gates.e2e_code.status`

> **Inform the user**: "Gate 4 E2E Code — [PASS/FAIL/SKIPPED]"

**Gate 5 — WCAG + wireframe conformity** (UI projects only): Run WCAG 2.1 AA audit (using configured accessibility tool, or manual checklist). Screenshot pages and compare against wireframes (design system colors, layout, component placement, `data-testid` presence, responsive breakpoints).
→ *On FAIL*: return to Step 4.1 (builder), fix UI code, re-run from Gate 4.
→ Skip for non-UI projects.
→ Update `_work/build/sc-[ID].yaml` → `gates.wcag_wireframes.status`

> **Inform the user**: "Gate 5 WCAG + Wireframes — [PASS/FAIL/SKIPPED]"

**Gate 6 — Execute E2E tests** (UI projects only): Run E2E test suite (E2E tool from stack profile).
→ *On FAIL*: fix code, re-run E2E.
→ Skip for non-UI projects.
→ Update `_work/build/sc-[ID].yaml` → `gates.e2e_execution.status`

> **Inform the user**: "Gate 6 E2E Execution — [PASS/FAIL/SKIPPED]"

**Gate 7 — Validate E2E against wireframes** (UI projects only): Verify E2E test results match wireframe expectations. Screenshots from E2E must match wireframe layouts. All user flows from wireframes must be covered. All `data-testid` from wireframes must be present in production code.
→ *On FAIL*: return to Step 4.1 (builder), fix implementation to match wireframes. Re-run from Gate 4.
→ Skip for non-UI projects.
→ Update `_work/build/sc-[ID].yaml` → `gates.e2e_wireframe_validation.status`

> **Inform the user**: "Gate 7 E2E vs Wireframes — [PASS/FAIL/SKIPPED]"

**Gate 8 — AC Validation**: Execute EVERY `verify:` command from the story file.
→ *On FAIL*: return to Step 4.1 (builder), fix code, re-run from Gate 8.
→ Update `_work/build/sc-[ID].yaml` → `gates.ac_validation.status`

> **Inform the user**: "Gate 8 AC Validation — [PASS/FAIL] ([X]/[Y] ACs pass)"

**Gate 9 — Story Review**: Dispatch `agents/story-reviewer.md` — verifies every AC against committed code with structured PASS/FAIL verdict. **Mandatory.** Story CANNOT be marked `validated` without PASS.
→ *On FAIL*: return to Step 4.1 (builder), fix based on review feedback. Re-run from Gate 8.
→ Update `_work/build/sc-[ID].yaml` → `gates.story_review.status`

> **Inform the user**: "Gate 9 Story Review — [PASS/FAIL]"

**Gate 10 — Code Review**: Dispatch `agents/reviewer.md` — code quality (SOLID/KISS/DRY/YAGNI), scope conformity (only touched listed files?), static analysis, readability. **Also verifies 0 console errors/stacktraces** (frontend browser console + backend server logs).
→ *On FAIL*: fix code quality issues from Step 4.1 (builder). Re-run from Gate 10.
→ Update `_work/build/sc-[ID].yaml` → `gates.code_review.status`

> **Inform the user**: "Gate 10 Code Review — [PASS/FAIL]"

**Gate 11 — Final compilation**: Re-run full compilation (same as Step 4.2) to confirm all fixes haven't broken the build.
→ *On FAIL*: fix and re-compile.
→ Update `_work/build/sc-[ID].yaml` → `gates.final_compilation.status`

> **Inform the user**: "Gate 11 Final Compilation — [PASS/FAIL]"

### Verdict

- **ALL GATES PASS** → Commit + PR/MR (see commit section below). Update tracker status to `validated`. Report to user.
- **ANY FAIL** → Increment `cycles` in tracker. Fix and re-validate (loop back to the correction point specified for each gate above).
- **cycles >= 3** → ESCALATE to human. Do NOT attempt a 4th cycle. Update tracker notes with what failed and why.

### Commit + PR/MR (after ALL gates pass)

**Single atomic commit** — never `git add .` or `git add -A`:
```bash
git add specs/stories/[feature-id].yaml
git add specs/stories/[feature-id]-manifest.yaml
git add specs/feature-tracker.yaml
git add [each file from story scope.files_to_create]
git add [each file from story scope.files_to_modify]
git add _work/build/sc-[ID].yaml
git add _work/ux/wireframes/[story-id]/  # if UI project
git commit -m "feat([feature-id]): [story title]"
```

**PR/MR creation** — detect tool once, memorize:
1. Read `memory/[project].md` for `pr_tool` key
2. If not set: detect available tools on machine (`gh`, `glab`, `az repos pr`)
3. If multiple found: ask user which to use
4. Memorize in `memory/[project].md` → `pr_tool: gh|glab|az|none`
5. Create PR/MR using detected tool. If none → warn user, no auto-PR.

> **Inform the user**: "All 11 gates passed ✓ — committed and PR/MR created: [URL]"

## Specialized builder dispatch

Based on story type or epic, dispatch to the appropriate builder agent:

| Story type / Epic | Builder agent |
|---|---|
| Backend service / API | `agents/builder-service.md` |
| Frontend / UI | `agents/builder-frontend.md` |
| Infrastructure / DevOps | `agents/builder-infra.md` |
| Database migration | `agents/builder-migration.md` |
| External integration / exchange | `agents/builder-exchange.md` |
| General / unknown | `agents/developer.md` (default) |

Read the story's `epic` or `type` field to determine which builder to dispatch. If uncertain, use the default developer agent.

## Dependency map generation

After creating the build file and BEFORE dispatching the test-engineer:

1. Read the story's `scope.files_to_create` and `scope.files_to_modify` sections
2. For each file in scope:
   a. Search the existing codebase for imports of that file (use language-appropriate import detection from the active stack profile)
   b. Grep for function/class names exported from that file that appear in other production files
   c. Find test files that import or reference those same symbols
3. Populate `dependency_map` in `_work/build/sc-[ID].yaml`:
   - `touched_functions`: symbols in scope files that are called or modified by existing code
   - `existing_tests`: test files that reference those symbols (with their run commands)
   - `connected_components`: production files outside scope that import from scope files
4. If no existing tests are found for a touched function, note it as a coverage gap — the test-engineer's coverage audit will catch it
5. If the project is greenfield (no existing code to analyze), leave `dependency_map` arrays empty — the test-engineer falls back to its standard coverage audit

This step is lightweight (grep-based) and runs in the orchestrator context — no agent dispatch needed.

## TDD enforcement scripts

These scripts enforce TDD discipline across the RED and GREEN phases:

### RED phase enforcement (Phase 3)
- `scripts/check_red_phase.py` — confirms tests exist AND fail (red)
- `scripts/check_test_intentions.py` — confirms every spec test_intention has a corresponding test. Pass `--require-ui-intentions` for frontend stories with rendered fields (Trigger C).
- `scripts/check_msw_contracts.py` — confirms API mock handlers use backend field names (endpoint stories only)

### GREEN phase enforcement (Phase 4)
- `scripts/check_tdd_order.py` — confirms test files were committed before implementation files
- `scripts/check_test_tampering.py` — confirms test assertions were NOT weakened to pass

### Post-build enforcement (Phase 5)
- `scripts/check_coverage_audit.py` — confirms coverage meets threshold
- Story review is handled by Gate 9 in the validation phase (mandatory, blocking)

## Build file creation

Before starting implementation, create a build state file:
1. Copy `specs/templates/build-template.yaml` to `_work/build/sc-[ID].yaml`
2. Populate with story ID, gate statuses (all initially `pending`), timestamps
3. Update gate statuses as each enforcement gate passes or fails
4. This file persists build state between sessions

## Stale story detection

Before starting a new build, check for stale stories:
- Query stories with status `building` that have no commits in the last 48 hours
- Warn the user about stale stories and suggest resolution (resume or reset)

## Dev comment checking

Before building, check the story for dev comments (from PM tool or tracker):
- Read any `dev_comments` field in the story file
- Apply dev comments as additional constraints during implementation

## Artefact checklist (must exist after /build)
- [ ] Unit tests (written in RED phase, reviewed, quality-scanned)
- [ ] Implementation code (files listed in story scope)
- [ ] Compilation successful (Step 4.2 + Gate 11)
- [ ] E2E tests (if UI project — based on wireframes with `data-testid`)
- [ ] `_work/build/sc-[ID].yaml` — build state file with all 11 gates recorded
- [ ] `specs/feature-tracker.yaml` — updated with status: validated (or escalated)
- [ ] PR/MR created and **URL shared with the user**

## Next step — tell the user ONLY when manual action is required

Only display a "Next step" when the user needs to act. Do NOT display during automatic loops (fix → re-validate).

**If ALL gates passed (validated):**
> **Next step:** Feature `[name]` is validated (all 11 gates passed). You can:
> - `/build [next-feature]` to build the next refined story
> - `/refine [feature]` to refine another feature
> - `/review` to run the final cross-feature review (requires ALL features validated)
> Remaining: [list features with their status from tracker].

**If ESCALATED (cycles >= 3):**
> **Next step:** Escalated after 3 failed cycles. Failing gates: [list]. Please review the issues above and decide how to proceed.
