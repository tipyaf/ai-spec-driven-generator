# CLAUDE.md — Rules for Claude Code

## Context
This project uses an AI-powered project generation framework. You must follow a structured, phase-based process with human validation, persistent memory, and machine-verifiable acceptance criteria.

## Fundamental Principles

These three principles apply to EVERY action, EVERY agent, EVERY phase:

| Principle | Rule |
|-----------|------|
| **Agnostic** | Adapt to the project type. Never assume web. Check `spec.type` before applying platform-specific rules (WCAG, Playwright, CSS, responsive). |
| **Autonomous** | Humans decide (product, architecture, infra), machines verify (tests, review, security). Auto-proceed when automated gates pass. Escalate to human after 3 failures only. |
| **Accompaniment** | Guide and challenge the user. Every human-validated phase ends with clear options, trade-offs, and next steps. Never leave the user without guidance. |

## Skills (primary entry points)

Use skills to dispatch to the right agent(s). Each skill loads ONLY the agents it needs — never load all agents at once.

| Skill | When to use | Agents loaded |
|-------|-------------|---------------|
| `/spec` | Start a new project or define a feature | product-owner, ux-ui, architect |
| `/refine` | Break a feature into actionable stories | refinement, product-owner |
| `/build` | Implement a refined story | developer, validator |
| `/validate` | Verify implementation against story file | validator |
| `/review` | Review all validated features before PR | reviewer, security, tester |
| `/scan` | Scan local changes only (staged + unstaged vs integration branch) | (inline) |
| `/scan-full` | Full codebase SonarQube analysis with hotspots and trends | (inline) |
| `/sonar` | SonarQube scan of local changes | (inline) |
| `/ux` | Design UI before building frontend stories | ux-ui |
| `/migrate` | Migrate a v3.x project to v4.0 structure | (inline — runs `scripts/migrate-v3-to-v4.sh`) |

**Default workflow**: `/spec` → `/refine` (per feature) → `/build` (per feature) → `/validate` (per feature) → `/review` (all features)

## Loading agents (IMPORTANT)

When you need an agent, read ONLY its core file:
- `agents/[name].md` — core instructions (always read this)
- `agents/[name].ref.md` — templates and examples (read only when you need a specific template)

**NEVER read all agent files at once.** Load the minimum needed for the current task.

## On session start

### New project (no memory file exists)
When a user describes a project idea or asks to build something:
1. Tell the user: "We'll define your project together before writing any code. I'll guide you through: Constitution → Scoping → Clarify → Design → Architecture → then we build."
2. Launch `/spec` — this guides through all conception phases with human validation at each step
3. After `/spec` is complete: launch `/refine` for the first feature
4. Only then: `/build` for each refined story

**NEVER jump to code.** Always start with `/spec`.

### Existing project (memory file exists)
1. Read `memory/[project-name].md` to restore context
2. Read `memory/LESSONS.md` for known pitfalls
3. Read `specs/feature-tracker.yaml` to know feature states
4. Summarize the project state to the user: what's done, what's next, which features are pending/refined/validated
5. Resume where it left off — use the appropriate skill

## Phase workflow

```
═══════════════════════════════════════════════════════════
PHASE 0 — CONCEPTION (/spec) — Human validation at each step
═══════════════════════════════════════════════════════════
  0.0 Constitution    → specs/constitution.md
  0.1 Scoping (PO)    → specs/[project].yaml
  0.2 Clarify         → specs/[project]-clarifications.md
  0.3 Design (UX/UI)  → specs/[project]-ux.md (skip if non-UI)
  0.5 Ordering        → features ordered in arch doc
  1.0 Architecture    → specs/[project]-arch.md
  → Initialize        → specs/feature-tracker.yaml

═══════════════════════════════════════════════════════════
PHASE 1 — SCAFFOLD (/build first run) — Auto
═══════════════════════════════════════════════════════════
  Init project, deps, structure, hooks → project compiles/starts

═══════════════════════════════════════════════════════════
PHASE 2 — CONSTRUCTION (per feature loop)
═══════════════════════════════════════════════════════════
  State tracked in: specs/feature-tracker.yaml
  Build contract in: specs/stories/[feature-id].yaml

  For each feature [pending → refined → building → testing → validated]:

  /refine  → Refinement  → ✅ Human   → story file written
  /build   → Developer   → 🤖 Auto    → code + tests
  /validate → Validator   → 🤖 Auto    → verify: commands executed
    Gate 1: Security (OWASP + stack forbidden patterns)
    Gate 2: Tests (TU + e2e)
    Gate 3: UI (WCAG + wireframe conformity) — if UI project
    Gate 4: AC Validation (every verify: command)
    Gate 5: Review (code quality + scope check)
  → PASS: status → validated
  → FAIL: cycles++ → fix → re-validate (max 3, then escalate)

═══════════════════════════════════════════════════════════
PHASE 3 — REVIEW (/review) — Auto
═══════════════════════════════════════════════════════════
  Prerequisites: ALL features status=validated in tracker
  Full code review + security audit + test quality check

═══════════════════════════════════════════════════════════
PHASE 4 — DEPLOY — ✅ Human
═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
PHASE 5 — RELEASE — ✅ Human
═══════════════════════════════════════════════════════════
```

## Validation model

| Phase | Skill | Agent | Validation | Gate (file must exist) |
|-------|-------|-------|------------|------------------------|
| 0: Constitution | /spec | — | Human | `specs/constitution.md` |
| 0.1: Scoping | /spec | PO | Human | `specs/[project].yaml` |
| 0.2: Clarify | /spec | PO | Human | `specs/[project]-clarifications.md` |
| 0.3: Design | /spec | UX/UI | Human | `specs/[project]-ux.md` |
| 0.5: Ordering | /spec | PO+Arch | Human | Features ordered in arch doc |
| 1: Plan | /spec | Architect | Human | `specs/[project]-arch.md` |
| 2: Scaffold | /build | Developer | Auto | Project compiles/starts |
| 2.5: Refine | /refine | Refinement | Human | `specs/stories/[feature].yaml` |
| 3: Implement | /build | Developer | Auto | Code + tests written |
| 3.5: Validate | /validate | Validator | Auto | ALL `verify:` commands PASS |
| 4: Review | /review | Reviewer+Security+Tester | Auto | Quality + security PASS |
| 5: Deploy | — | DevOps | Human | Infrastructure decision |
| 6: Release | — | — | Human | Go/no-go decision |

## Enforcement mechanisms

| Mechanism | What it enforces |
|-----------|-----------------|
| **Filesystem existence** | Phase gates — a phase is "done" when its artefact file exists on disk |
| **feature-tracker.yaml** | Per-feature state management (pending → refined → building → testing → validated) |
| **Story files** | Build contracts with `verify:` commands — persists between sessions |
| **verify: commands** | Machine-verifiable ACs — the validator executes these literally |
| **Cycle counter** | Max 3 validation cycles per feature before human escalation |
| **Implementation manifest** | Scope control — developer declares files before coding, reviewer verifies git diff matches |
| **Code review hook** | Automated Pass 2 — `stacks/hooks/code_review.py` runs anti-patterns + external checks |
| **Enforcement scripts** | Quality gates — `scripts/check_*.py` block commits on violations |
| **Build state (gates)** | Per-feature gate results (validation, code review, security, test quality, scope) persisted in manifest — agents resume from last state between sessions |

## Model tier recommendations (token optimization)

| Agent | Recommended model | Rationale |
|-------|-------------------|-----------|
| Developer | Opus | Must reason across files, understand data flows, write correct business logic |
| Tester | Opus | Must understand data flows end-to-end, catch subtle mismatches |
| Refinement | Opus | Reasons across dependency graphs, splits stories, pre-computes oracle values |
| Reviewer (Pass 1+3) | Opus | Must understand architecture (SOLID violations) and evaluate correctness |
| Reviewer (Pass 2) | Automated | `code_review.py` — no model needed |
| Validator | Sonnet | Systematic execution of verify: commands |
| Security | Sonnet (per-feature) / Opus (full audit) | Full audit requires cross-codebase reasoning |
| Product Owner | Sonnet | Structured spec writing, scoping |
| Architect | Opus | Cross-cutting architecture decisions |
| UX/UI | Sonnet | Wireframes, component specs, design system — structured and well-scoped |
| DevOps | Sonnet | Infrastructure config is well-scoped |
| Orchestrator | Opus | Must interpret agent verdicts, manage escalation logic, coordinate dependencies |

**Rule**: Skills SHOULD pass the recommended model tier when dispatching agents. Projects MAY override in their stack profile.

## Phase guards

Before executing a skill, verify its prerequisites exist **on the filesystem**:

| Skill | Prerequisites (files must exist) | If missing |
|-------|----------------------------------|------------|
| `/spec` | None — starting point | — |
| `/refine` | `specs/[project].yaml` + `specs/[project]-arch.md` + `specs/feature-tracker.yaml` | → "Let's define the project first" → `/spec` |
| `/build` | `specs/stories/[feature-id].yaml` + feature status=`refined` in tracker | → "This story needs refinement" → `/refine` |
| `/validate` | Feature status=`building` or `testing` in tracker | → "Nothing to validate yet" → `/build` |
| `/review` | ALL features status=`validated` in tracker | → "Some features still need validation" → list them |

## Acceptance criteria format (unified)

**ONE format everywhere** — in spec, story files, and validation reports:

```yaml
acceptance_criteria:
  - id: "AC-FUNC-AUTH-01"              # AC-[TYPE]-[FEATURE]-[NUMBER]
    type: "FUNC"                       # FUNC | SEC | BP
    description: "Given a valid email and password / When user submits login / Then session is created"
    verify: "curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:3000/api/auth/login -d '{\"email\":\"test@test.com\",\"password\":\"pass123\"}'"
    tier: 2                            # 1 (grep/bash) | 2 (curl/playwright) | 3 (runtime-only)
```

**Rules**:
- `verify: static` is **BANNED** — rewrite until you have a shell command
- AC-SEC-* MUST be Tier 1 (check code artefacts, not runtime behavior)
- No AC without `verify:` — unverifiable ACs are wishes, not criteria

## Coding standards (agnostic — all languages, all projects)

> **Full reference**: `rules/coding-standards.md` (SOLID, CQRS, DRY, YAGNI, readability gates, API design)

| Rule | Why | Example |
|------|-----|---------|
| **No magic strings** | Hardcoded strings buried in logic are invisible, fragile, and impossible to search for. Extract to named constants or config. | ❌ `if (status === 'accredited')` → ✅ `if (status === VISA_STATUS.ACCREDITED)` |
| **No magic numbers** | Same as strings. Raw numbers have no meaning without context. | ❌ `slice(0, 50)` → ✅ `slice(0, BATCH_SIZE)` |
| **Max 400 lines per file** | Files over 400 lines signal poor separation of concerns. Split into smaller, focused modules. | A 800-line service → split into core service + helpers + constants |
| **Max 40 lines per function** | Long functions signal poor decomposition. Split into focused functions. | A 100-line handler → split into validate + process + respond |
| **Max 3 levels of nesting** | Deep nesting is hard to follow and test. Use early returns, guard clauses. | ❌ `if (a) { if (b) { if (c) { ... }}}` → ✅ early returns |
| **Extract constants** | Group related constants in a dedicated file or block at the top of the module. Never scatter literals across business logic. | `const CACHE_TTL_DAYS = 30` at top, not `30` inline |
| **SOLID principles** | SRP, OCP, LSP, ISP, DIP. See `rules/coding-standards.md` for details. | Router = HTTP, Service = business logic, Repository = persistence |
| **Commits in English** | Commit messages, PR titles, and PR descriptions MUST always be in English. Code comments in English. This ensures consistency across international teams and tools. | ❌ `fix: correction du tri` → ✅ `fix: sorting order` |

## Shared rules files

| File | Content | Who must read it |
|------|---------|-----------------|
| `rules/agent-conduct.md` | Cross-agent behavior rules (single source of truth) | ALL agents, BEFORE their playbook |
| `rules/coding-standards.md` | SOLID, CQRS, DRY, YAGNI, readability gates, API design | Developer, reviewer, validator |
| `rules/test-quality.md` | Oracle computation, coverage audit, test anti-patterns, test intentions | Developer, tester, reviewer, validator |

## Git branching model (recommended)

This framework recommends a **Git Flow** branching model with two long-lived branches:

| Branch | Role | Merges into |
|--------|------|-------------|
| `main` | **Production** — only releases with changelog, version bump, and tag | — |
| `develop` | **Integration** — all feature work merges here first | `main` (at release time) |

> **Note**: If your project uses a single-branch model (trunk-based), replace `develop` with `main` in all rules below. The framework adapts to both models.

### Feature workflow
```
develop → git pull → new branch (feat/XXX) → work → PR targeting develop → merge → delete branch
```

### Release workflow (user-initiated only)
```
develop → release branch → changelog + version bump + tag → PR targeting main → merge → tag
```

### Rules — NEVER violate these
| Rule | Detail |
|------|--------|
| **All feature branches start from the integration branch** | `git checkout -b feat/XXX origin/develop` — NEVER from `main` (unless trunk-based) |
| **All PRs target the integration branch** | `gh pr create --base develop` — NEVER `--base main` (except release PRs) |
| **`main` is read-only for agents** | Only release PRs merge into `main`. Agents NEVER push directly to `main`. |
| **No cherry-picks between branches** | If something is missing, it means a release is needed — not a cherry-pick. |

### Pre-flight check (before EVERY `gh pr create`)
Before creating any PR, verify:
1. `git log --oneline origin/develop..HEAD` — your commits are ahead of the integration branch
2. `--base develop` is set (NOT `main`)
3. If you accidentally created a branch from `main`, rebase onto the integration branch first

## Git worktree rule — parallel work isolation

**When a feature branch is checked out**, all unrelated work (refinement, bug fixes, chores, other features) MUST be done in a **git worktree** to avoid mixing changes across branches.

| Situation | Action |
|-----------|--------|
| On `feat/sc-123` and user asks to refine sc-456 | Create worktree: `git worktree add .worktrees/chore-refine-456 -b chore/refine-sc-456 origin/develop` |
| On `feat/sc-123` and a bug is found unrelated to sc-123 | Create worktree: `git worktree add .worktrees/fix-sc-789 -b fix/sc-789 origin/develop` |
| Worktree work is done | Commit, push, create PR **targeting the integration branch** from the worktree. Then `git worktree remove .worktrees/[name]` |

**Rules**:
- Worktrees go in `.worktrees/` (gitignored)
- Branch from the integration branch (`origin/develop`) — NEVER from `main` or the current feature branch
- One worktree per task — don't reuse across unrelated tasks
- Clean up after merge: `git worktree remove .worktrees/[name]`
- Never mix changes from different stories/features on the same branch

## Strict rules
1. **Always read memory** at session start — `memory/[project-name].md` + `memory/LESSONS.md` + `specs/feature-tracker.yaml`
2. **Always update memory** after each phase
3. **Always update feature-tracker.yaml** after each feature state change
4. **Always follow phase order** — no shortcuts (skills enforce this via filesystem checks)
5. **Never load all agents** — use skills to load only what's needed
6. **Never over-engineer** — follow the spec, nothing more
7. **Never code before** conception phases are complete (spec + arch + tracker must exist)
8. **Never skip verify: commands** — they are the machine contract
9. **Always read `rules/agent-conduct.md`** before any agent work — it overrides playbook rules
10. **Always run enforcement scripts** before committing if the project has `test_enforcement.json`
11. **Never assert computed values without ORACLE blocks** — see `rules/test-quality.md` Rule 2
12. **Never skip test_intentions** from story files — every intention becomes a test
13. **Never mix branches** — unrelated work goes in a worktree (see worktree rule above)
14. **All PRs target the integration branch** — NEVER `main` directly (except release PRs). See Git branching model above.

## Agent role guards

| Agent | CAN do | CANNOT do |
|-------|--------|-----------|
| Product Owner | Write specs, challenge scope | Write code, make technical decisions |
| UX/UI Designer | Design UI, specify flows | Write code, choose frameworks |
| Architect | Plan architecture, create manifest | Write implementation code |
| Refinement | Break features into stories, write story files | Write code, make architecture decisions |
| Developer | Write code, create files | Self-validate, skip story scope |
| Validator | Run verify: commands, take screenshots | Modify source code, fix bugs |
| Tester | Write tests, run suites | Modify feature code |
| Reviewer | Audit quality, flag issues | Modify files directly |
| Security | Audit security, flag vulns | Modify files directly |
| DevOps | Configure CI/CD, deployment | Modify feature code |
| Test Engineer | TDD RED phase: write failing tests from spec | Write production code, modify existing tests in GREEN phase |
| Spec Generator | Merge YAML spec overlays into markdown | Modify spec YAML files, write code |
| Story Reviewer | Verify ACs against committed code, post PASS/FAIL | Modify files, execute tests |
| Builder (Service) | Build backend services: models, routers, schemas, tests | Self-validate, skip manifest |
| Builder (Frontend) | Build pages, components, hooks, API client, tests | Self-validate, skip manifest |
| Builder (Infra) | Build Docker, CI/CD, proxy, config | Modify feature code |
| Builder (Migration) | Database migrations, schema alignment tests | Modify feature code |
| Builder (Exchange) | Exchange integrations, order logic (safety-critical) | Skip safety checks |
| Build Orchestrator | Find refined stories, dispatch to builders, run gates | Skip quality gates, bypass TDD |

## `_work/` directory convention

All live agent working state lives under the `_work/` directory. This is project-specific content produced by agents during the build lifecycle.

| Path | Purpose | Who writes it |
|------|---------|---------------|
| `_work/spec/sc-0000-initial.yaml` | Baseline product spec (never modified by agents) | Dev (once, at project start) |
| `_work/spec/sc-[ID].yaml` | Per-story overlay (new/changed entries only) | Story Refiner / Refinement |
| `_work/build/sc-[ID].yaml` | Build file: domain_context, ac_verifications, anti_patterns, gate results | Build Orchestrator (creates), Builder (extends) |
| `_work/stacks/` | Project-owned stack profiles (copied from templates) | Dev (initial), customized per project |
| `_work/ux/` | UX agent working files (prototype HTML, components YAML) | UX Designer |

The build file (`_work/build/sc-[ID].yaml`) is the pipeline state for a story. The orchestrator creates it at dispatch, the builder extends it with file lists, and each quality gate updates its status. The validator reads `ac_verifications` from the build file directly.

## Enforcement scripts

Scripts live in `scripts/` (or `ai-framework/scripts/`). All read `test_enforcement.json` at the project root.

### Orchestrator gates (run at TDD boundary -- agents cannot self-certify)

| Script | Gate | Blocks when |
|--------|------|-------------|
| `check_red_phase.py` | After RED | Tests pass, trivial failures, no production imports |
| `check_test_intentions.py` | After RED | Spec intentions without matching tests |
| `check_coverage_audit.py` | After RED | Endpoints/tables/components without tests |
| `check_msw_contracts.py` | After RED | MSW handlers using frontend field names instead of backend |
| `check_test_tampering.py` | After GREEN | Deleted tests, weakened assertions |
| `check_tdd_order.py` | After GREEN | Code commits without preceding RED commit |

### Pre-commit checks (agents run before every commit)

| Script | Blocks when |
|--------|-------------|
| `check_test_quality.py` | .skip(), mock-soup, fixture-only tests |
| `check_write_coverage.py` | Tables with readers but no tested writers |
| `check_oracle_assertions.py` | Numeric assertions without ORACLE comment blocks |

## File locations
- **Agents**: `agents/*.md` (core) + `agents/*.ref.md` (templates)
- **Phase prompts**: `prompts/phases/`
- **Spec templates**: `specs/templates/`
- **Feature tracker**: `specs/feature-tracker.yaml`
- **Story files**: `specs/stories/[feature-id].yaml`
- **Stack profiles**: `stacks/`
- **Memory**: `memory/[project-name].md`
- **Lessons**: `memory/LESSONS.md`
- **Constitution**: `specs/constitution.md`
