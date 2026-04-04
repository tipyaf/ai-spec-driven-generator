# ai-spec-driven-generator

An AI-powered framework for generating complete code projects from structured YAML specs. Works with **Cursor** and **Claude Code**.

## Overview

This framework uses specialized AI agents, a skill-based workflow with human validation, persistent memory, machine-verifiable acceptance criteria, and per-feature state tracking to generate any type of code project from a single YAML specification.

## Fundamental Principles

This framework is built on three core principles that guide every design decision:

### 1. Agnostic
The framework works with **any programming language** and **any type of project** — not just web applications.

- Web apps, REST APIs, GraphQL, gRPC
- CLI tools, desktop applications
- Mobile apps (iOS, Android, cross-platform)
- Libraries and SDKs
- Data pipelines and ETL
- Embedded systems and IoT
- Games and simulations
- Machine learning pipelines

Agents, phases, and templates adapt their recommendations based on the project type declared in the spec. Web-specific concepts (pages, CSS, WCAG, Playwright) only apply when relevant.

### 2. Autonomous
Once the product is well-defined (Phase 0), the framework generates **production-ready code** without human intervention on technical tasks.

- **Humans decide**: product scope, UX design, architecture choices, infrastructure, release go/no-go
- **Machines verify**: code quality, tests, accessibility, security, conventions, anti-patterns

The developer never self-validates. An independent validator agent executes every `verify:` command from the build contract. Tests, reviews, and security audits are fully automated with escalation to humans only after 3 failures.

### 3. Accompaniment
The framework **guides and challenges** the user to build the best possible product. The user follows instructions and answers questions — never left without clear next steps.

- The Product Owner **challenges assumptions**: "Is this feature really MVP? What happens if you ship without it?"
- The Architect **presents options**: comparison tables with trade-offs, not just a single recommendation
- Every phase **ends with clear guidance**: what was done, what's next, what the user needs to decide
- The framework **explains why** it asks questions and enforces rules

## Key Features

### Enforcement (not just documentation)
- **Filesystem-based phase gates**: a phase is "done" when its artefact file exists on disk — not a checkbox in the LLM's memory
- **Per-feature state tracking**: `feature-tracker.yaml` tracks every feature (pending → refined → building → testing → validated)
- **Machine-verifiable ACs**: every acceptance criterion has a `verify:` shell command executed by the validator
- **Persistent build contracts**: `_work/spec/sc-[feature].yaml` files survive between sessions — refinement output is never lost
- **Build file system**: `_work/build/sc-[ID].yaml` tracks pipeline gates (RED/GREEN/review/security) per story — state persists between sessions
- **TDD enforcement (machine, not honor)**: 6 scripts enforce RED→GREEN→no-tampering — agents cannot self-certify
- **Cycle counter with escalation**: max 3 validation attempts per feature, then mandatory human escalation
- **Implementation manifest**: 2-phase build contract — developer declares scope + artifacts BEFORE coding, reviewer verifies git diff matches
- **Spec contract verification**: validator checks every declared artifact (endpoint, table, component) actually exists in code
- **Manifest scope enforcement**: reviewer fails any PR with files modified outside the declared manifest scope
- **Forbidden pattern scanning**: validator greps committed files against stack profile forbidden patterns
- **Stale feature detection**: developer agent warns when features are stuck in "building" with no recent commits
- **Recurring failure auto-logging**: reviewer automatically logs patterns to `LESSONS.md` when same failure appears in 2+ stories

### Development
- **Spec-driven**: YAML specs as the single source of truth
- **19 specialized agents**: Product Owner, UX/UI Designer, Architect, Refinement, Developer, Validator, Tester, Reviewer, Security, DevOps, Test Engineer, Spec Generator, Story Reviewer, Builder (Service, Frontend, Infra, Migration, Exchange)
- **Skills system**: `/spec`, `/refine`, `/build`, `/validate`, `/review`, `/scan`, `/scan-full`, `/sonar`, `/ux`, `/migrate` — each loads only the agents needed
- **Constitution pattern**: non-negotiable project principles defined before any code
- **Clarification phase**: ambiguities resolved before planning, not discovered during implementation
- **Unified AC format**: `AC-[TYPE]-[FEATURE]-[NUMBER]` with `verify:` command and testability tier
- **Stack profiles**: coding and security contracts per tech stack — auto-generate AC-SEC and AC-BP
- **Implementation scope control**: developers can only touch files listed in the story's scope section
- **7 sequential quality gates**: Security → Tests → UI → AC Validation → Review → SonarQube → Story Review (mandatory before `validated`)
- **SonarQube as Gate 6**: scan story files with coverage report, blocks on new BLOCKER/CRITICAL issues (skipped if not configured — optional per project)
- **SonarQube continuous quality**: hook also blocks on new violations after each session + on-demand `/scan`, `/scan-full`, `/sonar` skills

### Quality
- **3-pass code review**: KISS & readability → static analysis (automated hook) → safety & correctness
- **Independent validation**: the agent that writes code is never the agent that validates it
- **Test quality standards**: explicit "real test vs mock-soup" checklists, forbidden test patterns
- **Failure memory (LESSONS.md)**: recurring mistakes logged and read by all agents before starting
- **Language-agnostic hooks**: configurable `hook-config.json` with `{files}`, `filter`, `cwd` placeholders
- **Automated code review hook**: Python script (`code_review.py`) runs anti-patterns + external checks with JSON verdict output
- **Oracle computation blocks**: every numeric assertion on a computed value requires step-by-step math proof
- **Test intentions**: refinement agent pre-computes oracle values; developer copies, never guesses
- **Mutation testing**: tests must achieve 70%+ mutation score; surviving mutants get targeted kill-tests
- **LLM fault scenarios**: 3-5 realistic business-logic faults generated per rule (wrong field, missing accumulation, off-by-one, etc.)
- **Ensemble test assessment**: each test scored STRONG/WEAK/USELESS — USELESS tests must be rewritten
- **9 enforcement scripts** blocking commits: test quality, oracle assertions, write coverage, RED phase, test intentions, coverage audit, MSW contracts, TDD order, test tampering
- **SOLID/CQRS/DRY/YAGNI**: language-agnostic coding standards with concrete thresholds (40 lines/function, 3 levels nesting, 400 lines/file)
- **Model tier recommendations**: Opus for reasoning-heavy agents (developer, tester), Sonnet for systematic agents (validator, reviewer Pass 2)
- **UX gate**: frontend stories require UX spec before coding begins
- **ADR gate**: architecture decisions documented before implementation proceeds
- **Smart/Dumb component architecture**: classification rules, reuse-before-create, extract at 2nd occurrence (UI projects)
- **Component reuse pipeline**: architect inventories shared components → refinement audits reuse → developer checks before creating → reviewer catches duplicates
- **Interactive best practices proposal**: architect proposes stack-specific practices as checklist, user validates/customizes, stored as coding contract in stack profile
- **Best Practices Catalog**: 55+ practices across 6 project types (frontend web, mobile native, cross-platform, backend API, data pipeline, CLI/library)

### Git & Infrastructure
- **Git Flow branching model**: `main` (production, releases only) + `develop` (integration, all feature work) — enforced by agent rules
- **Git worktree isolation**: parallel work on multiple features without mixing branches — agents auto-create worktrees for unrelated tasks
- **Persistent memory**: per-project markdown files tracking decisions, feedback, phase status, and feature progress
- **Project management integration**: Shortcut.com support for ticket creation and tracking
- **Claude Code slash commands**: `/spec`, `/refine`, `/build`, `/validate`, `/review` work as native Claude Code commands via `.claude/commands/`
- **Tool-agnostic**: works with both Cursor (`.cursorrules`) and Claude Code (`CLAUDE.md`)
- **Auto-versioning**: GitHub Action bumps VERSION on every push, auto-generates CHANGELOG
- **Token-optimized agents**: core (rules) + ref (templates) split — 60% fewer tokens per session

## Workflow

```
═══════════════════════════════════════════════════════════
PHASE 0 — CONCEPTION (/spec) — Human validation at each step
═══════════════════════════════════════════════════════════
  Constitution    → specs/constitution.md
  Scoping (PO)    → specs/[project].yaml → _work/spec/sc-0000-initial.yaml
  Clarify         → specs/[project]-clarifications.md
  Design (UX/UI)  → _work/ux/[project]-ux-spec.md (skip if non-UI)
  Ordering        → features ordered in arch doc
  Architecture    → specs/[project]-arch.md
  Initialize      → _work/feature-tracker.yaml

═══════════════════════════════════════════════════════════
PHASE 1 — SCAFFOLD (/build first run) — Auto
═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
PHASE 2 — CONSTRUCTION (per feature loop)
═══════════════════════════════════════════════════════════
  For each feature [pending → refined → building → testing → validated]:

  /refine   → spec overlay + story file (_work/spec/sc-[ID].yaml)
  /build    → TDD: RED (test-engineer) → GREEN (builder) → 7 quality gates
  /validate → Gate 1: Security → Gate 2: Tests → Gate 3: UI
              Gate 4: AC Validation → Gate 5: Review
              Gate 6: SonarQube (skipped if not configured)
              Gate 7: Story Review (mandatory)
  → ALL GATES PASS: feature validated
  → ANY FAIL: fix + re-validate (max 3 cycles, then escalate)

  SonarQube also runs continuously (hook after each session + /scan on demand)

═══════════════════════════════════════════════════════════
PHASE 3 — REVIEW (/review) — All features must be validated
═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
PHASE 4 — DEPLOY — ✅ Human validation
═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
PHASE 5 — RELEASE — ✅ Human validation
═══════════════════════════════════════════════════════════
```

## Quick start

### 1. Create a new project

```bash
# Clone the framework (or use it from any location)
git clone https://github.com/tipyaf/ai-spec-driven-generator.git
cd ai-spec-driven-generator

# Initialize a new project
./scripts/init-project.sh my-project /path/to/workspace
```

This creates a new project with:
- A **git submodule** pointing to this framework
- A `CLAUDE.md` configured for the project
- Project-specific directories (`specs/`, `memory/`, `_work/`)
- Skills symlinked to `.claude/skills/`
- Hook configuration (`hook-config.json`, `.claude/settings.json`)

### 2. Open in your AI IDE

Open the project in **Cursor** or **Claude Code**. The AI will automatically pick up the rules and follow the framework workflow.

### 3. Start building

In Claude Code, use the slash commands directly:

```
/spec                        # Define your project (constitution → scoping → design → architecture)
/refine candidate-profile    # Break a feature into stories with verify: commands
/build candidate-profile     # TDD pipeline: RED → GREEN → review → security
/validate candidate-profile  # Run all verify: commands independently (max 3 cycles)
/review                      # Final review before PR
/ux candidate-profile        # UX design (spec + YAML components + HTML prototype)
/scan                        # SonarQube scan on local changes
/scan-full                   # Full codebase SonarQube analysis
/sonar                       # SonarQube status dashboard
/migrate                     # Migrate v3.x project to v4.0 structure
```

In Cursor, describe your task and the AI follows the same workflow via `.cursorrules`.

Skills enforce phase order via filesystem checks: you can't build before the story file exists, you can't review before all features are validated. Each phase ends with clear options and next steps.

### 4. Configure SonarQube (optional)

Create a `.env` file at your project root with your SonarQube credentials:

```bash
cp framework/stacks/hooks/.env.example .env
```

```env
SONAR_TOKEN=squ_your_token_here
SONAR_HOST_URL=http://localhost:9000
SONAR_PROJECT_KEY=your-project-key
```

The `.env` file is gitignored — each developer and each project can have its own configuration. The hook and skills read `.env` first, then fall back to shell environment variables (`~/.zshrc`).

> Full setup guide (Docker install, token generation, coverage reporting): [`_docs/sonarqube.md`](_docs/sonarqube.md)

### 5. Update the framework

When the framework gets improvements, update all projects at once:

```bash
cd my-project
git submodule update --remote framework
```

## Framework structure

```
ai-spec-driven-generator/
├── agents/                  # 19 specialized agent definitions (core + ref split)
│   ├── orchestrator.md      # Orchestration rules reference (enforced by skills)
│   ├── product-owner.md     # Scoping, spec writing, AC format
│   ├── ux-ui.md             # UX/UI design — WCAG 2.1 AA
│   ├── architect.md         # Architecture + implementation manifest + shared component inventory
│   ├── refinement.md        # Feature breakdown, story files, verify: commands, AC-SEC/AC-BP auto
│   ├── developer.md         # Code implementation (manifest-scoped, generic builder)
│   ├── validator.md         # Independent verification (spec contract, forbidden patterns)
│   ├── tester.md            # Test writing (mutation, kill-tests, ensemble assessment)
│   ├── reviewer.md          # Code quality audit (3-pass + manifest scope enforcement)
│   ├── security.md          # Security audit — OWASP Top 10
│   ├── devops.md            # CI/CD & deployment
│   ├── test-engineer.md     # TDD RED phase — writes failing tests before code (Opus)
│   ├── spec-generator.md    # YAML overlay merging to markdown documentation
│   ├── story-reviewer.md    # Per-story AC verification (separated from code review)
│   ├── builder-service.md   # Specialized backend builder (Python/FastAPI)
│   ├── builder-frontend.md  # Specialized frontend builder (React/TS, MSW contracts)
│   ├── builder-infra.md     # Docker/CI-CD specialist
│   ├── builder-migration.md # Database migration expert (Alembic)
│   ├── builder-exchange.md  # Safety-critical exchange integration (Opus)
│   └── *.ref.md             # Templates and examples per agent (loaded on demand)
├── skills/                  # Skill dispatchers with phase guards
│   ├── spec/SKILL.md        # /spec — constitution → scoping → clarify → design → arch
│   ├── refine/SKILL.md      # /refine — break feature into story file + AC-SEC/AC-BP
│   ├── build/SKILL.md       # /build — TDD pipeline (RED→GREEN) with specialized builders
│   ├── validate/SKILL.md    # /validate — execute verify: commands (max 3 cycles)
│   ├── review/SKILL.md      # /review — story review + code review + security audit
│   ├── scan/SKILL.md        # /scan — SonarQube scan on local changes
│   ├── scan-full/SKILL.md   # /scan-full — full codebase SonarQube analysis
│   ├── sonar/SKILL.md       # /sonar — SonarQube status dashboard
│   ├── ux/SKILL.md          # /ux — UX design (spec + YAML components + HTML prototype)
│   └── migrate/SKILL.md     # /migrate — upgrade v3.x projects to v4.0
├── prompts/phases/          # Phase-specific detailed instructions
├── rules/                   # IDE integration + shared rules
│   ├── CLAUDE.md            # Rules for Claude Code (model tiers, enforcement mechanisms)
│   ├── CLAUDE.md.template   # Template for project init
│   ├── .cursorrules         # Rules for Cursor
│   ├── agent-conduct.md     # Cross-agent behavior rules (single source of truth)
│   ├── coding-standards.md  # SOLID, CQRS, DRY, YAGNI, readability gates, API design, smart/dumb components
│   ├── test-quality.md      # Oracle computation, coverage audit, test anti-patterns
│   └── commands/            # Claude Code slash command templates
│       ├── spec.md          # /spec command
│       ├── refine.md        # /refine command
│       ├── build.md         # /build command
│       ├── validate.md      # /validate command
│       └── review.md        # /review command
├── specs/templates/         # YAML templates
│   ├── spec-template.yaml   # Spec with unified AC format
│   ├── spec-overlay-template.yaml # Per-story spec overlay for domain changes
│   ├── feature-tracker.yaml # Per-feature state tracking
│   ├── story-template.yaml  # Refinement output (build contract)
│   ├── manifest-template.yaml # Implementation manifest (2-phase build contract)
│   └── build-template.yaml  # Pipeline state tracker with gates (RED/GREEN/review/security)
├── stacks/                  # Stack profiles & quality hooks
│   ├── hooks/               # Claude Code quality gate hooks
│   │   ├── hook-config.json # Anti-patterns, external checks, skip dirs
│   │   ├── code_review.py   # Automated code review hook (Pass 2) — JSON verdict
│   │   └── sonar_check.py   # SonarQube stop hook — blocks on new violations
│   ├── templates/           # Stack profile examples
│   │   ├── python-fastapi.md    # Backend: AC-SEC, AC-BP, forbidden patterns
│   │   ├── typescript-react.md  # Frontend: MSW contracts, component architecture
│   │   └── postgres.md          # Database: migration patterns, constraints
│   └── stack-profile-template.md # Generic template for any stack
├── examples/                # Example specs
│   └── todo-app-spec.yaml   # With structured ACs and verify: commands
├── memory/                  # Memory templates
│   ├── memory-template.md   # With feature status table
│   ├── LESSONS.md.template
│   └── SYNC.md.template
├── _docs/                   # Framework documentation
│   ├── INDEX.md             # Navigation hub
│   ├── agents.md            # Agent catalog with sequence diagram
│   ├── process.md           # Story lifecycle documentation
│   ├── workflow.md          # Board conventions, build order, branches
│   ├── skills.md            # Skills system guide
│   ├── sonarqube.md         # SonarQube integration guide
│   └── test-methodology.md  # Two-loop test approach (spec→oracle + mutation feedback)
├── scripts/
│   ├── init-project.sh          # Project initializer (creates _work/, symlinks skills, hooks)
│   ├── migrate-v3-to-v4.sh     # Migration script for existing v3.x projects
│   ├── check_test_quality.py    # Pre-commit: no .skip(), no mock-soup
│   ├── check_oracle_assertions.py # Pre-commit: ORACLE blocks on numeric assertions
│   ├── check_write_coverage.py   # Pre-commit: write-path coverage verification
│   ├── check_red_phase.py       # Gate: tests must FAIL in RED phase
│   ├── check_test_intentions.py # Gate: every spec intention has a test
│   ├── check_coverage_audit.py  # Gate: every endpoint/table/component tested
│   ├── check_msw_contracts.py   # Gate: MSW mocks match Pydantic fields
│   ├── check_tdd_order.py       # Gate: RED commit before GREEN commit
│   ├── check_test_tampering.py  # Gate: builder cannot weaken tests
│   └── test_enforcement.json.example # Config template for enforcement scripts
├── VERSION
├── CHANGELOG.md
└── .github/workflows/
    └── bump-version.yml     # Auto-versioning
```

## Project structure (after init)

```
my-project/
├── framework/              # Git submodule → ai-spec-driven-generator
├── _work/                  # Working artifacts (per-story state)
│   ├── spec/               # Spec overlays
│   │   ├── sc-0000-initial.yaml  # Baseline spec (from project YAML)
│   │   ├── sc-auth.yaml          # Per-story overlay (domain changes + ACs)
│   │   └── sc-todos-crud.yaml
│   ├── build/              # Pipeline state per story
│   │   ├── sc-auth.yaml          # Gates: RED/GREEN/review/security
│   │   └── sc-todos-crud.yaml
│   ├── ux/                 # UX design artifacts
│   │   ├── auth-ux-spec.md       # Wireframes + flows
│   │   ├── auth-components.yaml  # Component definitions
│   │   └── auth-prototype.html   # Interactive prototype
│   └── stacks/             # Project-specific stack profiles
│       ├── python-fastapi.md     # Backend coding + security contract
│       └── typescript-react.md   # Frontend coding + MSW rules
├── specs/
│   ├── constitution.md     # Non-negotiable project principles
│   ├── my-project.yaml     # YAML spec (source of truth)
│   ├── my-project-arch.md  # Architecture plan
│   └── feature-tracker.yaml # Per-feature state (pending→validated)
├── memory/
│   ├── my-project.md       # Project memory (decisions, phase status)
│   ├── LESSONS.md          # Recurring failure patterns
│   └── SYNC.md             # Framework version sync
├── apps/                   # Application code
├── packages/               # Shared packages
├── .claude/
│   ├── skills/             # Symlinks → framework skills
│   └── settings.json       # Hook configuration (code_review + sonar)
├── hook-config.json        # Language-agnostic lint/test checks
├── CLAUDE.md               # AI rules (generated from framework template)
└── .cursorrules            # Cursor rules
```

## Code Quality & Test Robustness

The framework generates production-ready code by enforcing quality at every pipeline stage — not just at review time.

### Two-Loop Test Generation
- **Loop 1 (Proactive)**: Refinement agent pre-computes oracle values with step-by-step math. Developer copies these into `# ORACLE:` comment blocks. Tests verify exact expected values, not vague assertions.
- **Loop 2 (Reactive)**: After tests pass, mutation testing introduces faults (flip operators, change values). If tests don't catch the mutations (score < 70%), they're weak — targeted kill-tests are written for each surviving mutant.

### Enforcement Pipeline
Nine Python scripts block commits and pipeline stages if violations are found:

**Pre-commit (general quality):**
- `check_test_quality.py` — no `.skip()`, no mock-soup in integration tests, no fixture-only tests
- `check_oracle_assertions.py` — every numeric assertion needs an ORACLE comment with step-by-step math
- `check_write_coverage.py` — every data store with a read endpoint must have production write code

**Orchestrator gates (TDD pipeline per story):**
- `check_red_phase.py` — tests must FAIL before code is written (no trivial failures, must import production code)
- `check_test_intentions.py` — every `test_intention` from spec has a matching test
- `check_coverage_audit.py` — every endpoint, table, and component has at least one test
- `check_msw_contracts.py` — MSW mocks return exact Pydantic field names (catches frontend/backend mismatches)
- `check_tdd_order.py` — RED commit must precede GREEN commit in git history
- `check_test_tampering.py` — builder cannot delete, weaken, or bypass tests written by test engineer

### Automated Code Review Hook
`stacks/hooks/code_review.py` runs anti-pattern detection + external command checks (lint, format, typecheck) on changed files. Returns a JSON verdict (`pass`/`block`) for Claude's stop hook mechanism. Language-agnostic — configured via `hook-config.json`.

### Implementation Manifest
Before writing code, the developer creates a manifest declaring scope (artifacts, files to modify/create, anti-patterns to avoid). The validator verifies declared artifacts exist in code. The reviewer verifies the git diff matches the declared scope. Undeclared modifications = automatic FAIL.

### Coding Standards
Language-agnostic SOLID/CQRS/DRY/YAGNI with concrete thresholds: max 40 lines/function, max 3 levels nesting, max 400 lines/file, max 10 cyclomatic complexity, max 5 function parameters. See `rules/coding-standards.md`.

### Smart/Dumb Component Architecture (UI projects)
Every UI component is classified as **Dumb** (presentational — receives data via props, zero service imports, high reusability) or **Smart** (container — orchestrates logic, fetches data, manages state). Enforced across the pipeline: architect inventories shared components, refinement audits reuse before requesting new ones, developer checks the shared directory before creating, reviewer catches duplicates. Extract to shared dumb component at 2nd occurrence — stricter than logic DRY. See `rules/coding-standards.md` §10.

### Interactive Best Practices
During architecture phase, the framework proposes best practices tailored to the project type and stack as a numbered checklist. The user reviews, removes, adds, or modifies practices. A final recap requires explicit confirmation. Validated practices are stored in the stack profile as the project's coding contract. The catalog (`agents/architect.ref.md`) covers 6 project types with 55+ practices.

## Contributing

Every improvement to the framework should be a commit + PR on this repo. Projects that use the framework get updates via:

```bash
git submodule update --remote framework
```

## License

MIT
