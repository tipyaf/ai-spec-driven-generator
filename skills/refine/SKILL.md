---
name: refine
description: Refine a user story — break it down into actionable tasks with structured acceptance criteria (AC-FUNC, AC-SEC, AC-BP) each with a verify: shell command. Creates wireframes for UI changes, validates WCAG, and syncs with PM tools.
---

## Phase guard — verify before proceeding

**Prerequisites** (check filesystem):
1. `specs/[project-name].yaml` must exist (spec done)
2. `specs/[project-name]-arch.md` must exist (architecture done)
3. `specs/feature-tracker.yaml` must exist (tracking initialized)
4. The target feature must have `status: pending` in the tracker

**If any prerequisite is missing** → Tell user: "Let's define the project first" → suggest `/spec`

## Setup — Read these files before starting

1. Read `agents/refinement.md` (core instructions)
2. Read `agents/product-owner.md` (core instructions — for AC format)
3. Read stack profiles from `stacks/` (for auto-generating AC-SEC-* and AC-BP-*)
4. Read `specs/feature-tracker.yaml` (current state)
5. Read `memory/LESSONS.md` (known pitfalls to avoid in ACs)

Only read `.ref.md` files if you need ticket templates or AC examples.

## Workflow

1. Read `specs/feature-tracker.yaml` — pick the next `pending` feature (or let user choose)
2. Read the feature from the spec YAML
3. Decompose into atomic user stories (implementable in 1 session)
4. For each story: write acceptance criteria in structured format:
   - **AC-FUNC-[FEATURE]-NN**: functional (Given/When/Then)
   - **AC-SEC-[FEATURE]-NN**: security (auto-generated from stack profile)
   - **AC-BP-[FEATURE]-NN**: best practices (auto-generated from stack profile)
5. **EVERY AC MUST have a `verify:` shell command** — no exceptions:
   - Tier 1 (preferred): `verify: grep` or `verify: bash` — runs without live service
   - Tier 2: `verify: curl` or `verify: playwright` — requires live service
   - Tier 3 (last resort): `verify: runtime-only` — minimize usage
   - **`verify: static` is BANNED** — rewrite until you have a shell command
   - **AC-SEC-* MUST be Tier 1** — check code artefacts, not runtime behavior
6. **Auto-generate validation ACs** (see validation ACs section below)
7. Define the scope (files to create/modify/read)
8. Identify edge cases
9. If feature is large (L/XL): propose breakdown options to user
10. **Wireframe gate** (UI projects only — see wireframe gate section below)
11. Present the full breakdown to the user for validation (including wireframes if applicable)
12. On validation:
    - Write story file to `specs/stories/[feature-id].yaml` (from template)
    - Update `specs/feature-tracker.yaml`: set feature status to `refined`, set `story_file` path
    - Create tickets in PM tool (if configured — see PM integration section below)
    - **NO commit here** — commit happens after `/build` validation (see `rules/agent-conduct.md` Rule 12)

## Wireframe gate (UI projects only)

**MANDATORY for web, mobile, or desktop projects when the story introduces new UI elements** (new pages, new components, modified layouts).

### When to trigger
- Story introduces a **new page or screen**
- Story adds **new UI components** not covered by existing wireframes
- Story **modifies layout or navigation** of existing pages
- Story changes **design system tokens** (colors, typography, spacing)

If the story is backend-only or modifies existing UI without layout changes, skip this gate.

### Workflow

1. **Detect new UI elements**: Compare story scope against existing wireframes in `specs/[project]-ux.md`
2. **Dispatch UX/UI agent** (`agents/ux-ui.md`): Create or update wireframes for new/modified pages and components
   - Wireframes MUST follow the project's design system (`specs/[project]-ux.md` → Design System section)
   - Wireframes are produced as **self-contained HTML files** (inline CSS with DS tokens as CSS variables)
   - Include all states: empty, loading, error, success
   - Include responsive breakpoints (320px, 768px, 1024px, 1440px)
   - Include component specs with accessibility requirements
   - **Every interactive element and significant content zone MUST have a `data-testid` attribute** (e.g., `data-testid="login-form-email"`)
   - These `data-testid` values are the **contract between wireframes and production code** — the builder reuses them exactly, E2E tests target them
3. **WCAG validation** on wireframes:
   - If WCAG audit tool is configured in the stack profile (Pa11y CLI, axe-core, or other) → use it on the wireframe HTML
   - If no tool configured → UX agent performs manual WCAG checklist (contrast ratios, keyboard nav, ARIA, touch targets)
   - **If WCAG fails** → return to step 2, fix wireframes, re-validate. **Loop until PASS.**
4. **Present wireframes to user** for validation:
   - Show all wireframes (HTML files) for each new/modified page
   - Show component specs with states and accessibility
   - Show responsive adaptations
   - **WAIT for user approval.** Do NOT proceed without explicit validation.
   - **If user rejects** → return to step 2 with user feedback, iterate.
5. **Persist wireframes**: Write validated wireframes to `_work/ux/wireframes/[story-id]/[page-name].html`
6. **Update UX spec**: Update `specs/[project]-ux.md` with new/modified wireframe sections
7. **Reference in story file**: Set `ux_ref:` field pointing to the wireframe section

### Artefacts produced
- `_work/ux/wireframes/[story-id]/[page-name].html` — self-contained HTML wireframes with `data-testid` attributes
- Updated `specs/[project]-ux.md` with new/modified wireframes
- `ux_ref:` field populated in story file

## Validation ACs (auto-generated for every story)

The refinement agent MUST add these ACs to every story (from `specs/templates/story-template.yaml` → `validation_acs`):

- **AC-BP-[FEATURE]-COMPILE**: Project compiles without errors (command from stack profile)
- **AC-BP-[FEATURE]-TU**: All unit tests pass (command from stack profile)
- **AC-BP-[FEATURE]-CONSOLE**: Zero console errors/stacktraces (frontend + backend)

For UI projects (when `ux_ref` is not null), also add:
- **AC-BP-[FEATURE]-WCAG**: WCAG 2.1 AA — 0 violations
- **AC-BP-[FEATURE]-WIREFRAME**: UI matches wireframe layout, design system, and `data-testid` attributes

## Project management integration

When a PM tool is configured (Shortcut, Jira, GitLab, or via MCP), the refine phase creates and enriches tickets.

### Ticket creation
1. Create **Epic** per feature (if not already created)
   - Jira: Epic, GitLab: Milestone, Shortcut: Epic
2. Create **Story** per user story with: parent feature, size, priority, user story format, ACs, edge cases, dependencies, technical notes
3. **Attach wireframe HTML files** to the ticket (via PM tool API or MCP)
   - Also attach a screenshot image (via E2E tool if configured) for quick preview
4. **Add validation checklist** to the ticket:
   - [ ] Unit tests created, reviewed, and validated (RED phase)
   - [ ] Unit tests pass after implementation
   - [ ] Compilation OK (0 errors)
   - [ ] E2E written from wireframes (if UI)
   - [ ] E2E pass without errors (if UI)
   - [ ] Wireframes conformity OK (if UI)
   - [ ] WCAG OK (if UI)
   - [ ] Code quality OK (tool or reviewer)
   - [ ] 0 console errors (front + back)
   - [ ] Security OK
   - [ ] Code review OK
   - [ ] All ACs pass
   - [ ] Story review OK
   - [ ] Final compilation OK
5. Initial status: `Backlog` → `Refined` after user validation

### Specs are the source of truth
With or without a PM tool, the specs (`specs/stories/`, `specs/[project].yaml`) are the **absolute source of truth**. The PM tool is a mirror/facilitator, never a replacement. The product can be rebuilt entirely from specs alone.

### Supported tools
| Tool | Epic | Story | Attachments | Status sync |
|------|------|-------|-------------|-------------|
| Shortcut | Epic | Story | API upload | API |
| Jira | Epic | Story | REST API | REST API |
| GitLab | Milestone | Issue | Issue attachment | API |
| MCP | Via MCP server | Via MCP server | Via MCP server | Via MCP server |
| None | — | — | — | Specs = source of truth |

The tool is detected from project configuration (`pm_tool` field in `CLAUDE.md` or `memory/[project].md`). If not configured, skip ticket creation (log warning, specs remain authoritative).

## Stack profile integration

Before writing ACs, read the stack profiles to auto-generate security and best-practice criteria:

1. Read all stack profiles from `_work/stacks/*.md` (or `stacks/*.md` if `_work/stacks/` does not exist)
2. Extract `security_rules` from each applicable stack profile
3. Extract `best_practices` from each applicable stack profile
4. **Auto-generate AC-SEC-[FEATURE]-NN** from each security rule that applies to the story's scope
5. **Auto-generate AC-BP-[FEATURE]-NN** from each best practice that applies to the story's scope

These auto-generated ACs supplement (not replace) any hand-written ACs.

## Testability tier classification

Every AC MUST be classified into a testability tier:

| Tier | Verify method | When to use |
|---|---|---|
| **Tier 1** (preferred) | `grep`, `bash`, `jq` | Static checks against code artefacts — no running service needed |
| **Tier 2** | `curl`, `playwright`, `cypress` | Requires a live service or browser |
| **Tier 3** (last resort) | `runtime-only` | Cannot be automated — minimize usage |

Rules:
- **AC-SEC-* MUST be Tier 1** — always check code artefacts, not runtime behavior
- **AC-BP-* SHOULD be Tier 1** — prefer static verification
- **`verify: static` is BANNED** — rewrite until you have a shell command

## Test intentions generation

For each AC, generate a `test_intentions` block containing:
- **Intent**: what the test proves (one sentence)
- **Oracle value**: the pre-computed expected result (e.g., expected HTTP status, expected string in output, expected file content)
- **Verify command**: the shell command that produces the actual value to compare against the oracle

This ensures the builder and test engineer have unambiguous pass/fail criteria.

## Spec overlay creation

After writing the story file, create a spec overlay:
1. Write to `_work/spec/sc-[ID].yaml`
2. The overlay captures any spec changes implied by this story (new endpoints, schema changes, config additions)
3. The overlay will be merged with the baseline spec during `/spec` regeneration

## Artefact checklist (must exist after /refine)
- [ ] `specs/stories/[feature-id].yaml` — the build contract (with validation ACs)
- [ ] `_work/spec/sc-[ID].yaml` — spec overlay (even if empty)
- [ ] `specs/feature-tracker.yaml` — updated with status: refined
- [ ] `_work/ux/wireframes/[story-id]/` — wireframe HTML files (if UI project)
- [ ] `specs/[project]-ux.md` — updated with new wireframes (if UI project)

## Next step — ALWAYS tell the user

After `/refine` completes, ALWAYS end your response with:

> **Next step:** Story refined and ready to build. Run `/build [feature-name]` to start the TDD pipeline (RED → GREEN → 11 quality gates). You can also `/refine [other-feature]` to refine another feature first.
