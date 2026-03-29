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
- **Persistent build contracts**: `specs/stories/[feature].yaml` files survive between sessions — refinement output is never lost
- **Cycle counter with escalation**: max 3 validation attempts per feature, then mandatory human escalation
- **Implementation manifest**: 2-phase build contract — developer declares scope + artifacts BEFORE coding, reviewer verifies git diff matches
- **Spec contract verification**: validator checks every declared artifact (endpoint, table, component) actually exists in code
- **Manifest scope enforcement**: reviewer fails any PR with files modified outside the declared manifest scope
- **Forbidden pattern scanning**: validator greps committed files against stack profile forbidden patterns
- **Stale feature detection**: developer agent warns when features are stuck in "building" with no recent commits
- **Recurring failure auto-logging**: reviewer automatically logs patterns to `LESSONS.md` when same failure appears in 2+ stories

### Development
- **Spec-driven**: YAML specs as the single source of truth
- **10 specialized agents**: Product Owner, UX/UI Designer, Architect, Refinement, Developer, Validator, Tester, Reviewer, Security, DevOps
- **Skills system**: `/spec`, `/refine`, `/build`, `/validate`, `/review` — each loads only the agents needed
- **Constitution pattern**: non-negotiable project principles defined before any code
- **Clarification phase**: ambiguities resolved before planning, not discovered during implementation
- **Unified AC format**: `AC-[TYPE]-[FEATURE]-[NUMBER]` with `verify:` command and testability tier
- **Stack profiles**: coding and security contracts per tech stack — auto-generate AC-SEC and AC-BP
- **Implementation scope control**: developers can only touch files listed in the story's scope section
- **5 sequential quality gates**: Security → Tests → UI → AC Validation → Review

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
- **3 enforcement scripts** blocking commits: test quality, oracle assertions, write coverage
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
  Scoping (PO)    → specs/[project].yaml
  Clarify         → specs/[project]-clarifications.md
  Design (UX/UI)  → specs/[project]-ux.md (skip if non-UI)
  Ordering        → features ordered in arch doc
  Architecture    → specs/[project]-arch.md
  Initialize      → specs/feature-tracker.yaml

═══════════════════════════════════════════════════════════
PHASE 1 — SCAFFOLD (/build first run) — Auto
═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
PHASE 2 — CONSTRUCTION (per feature loop)
═══════════════════════════════════════════════════════════
  For each feature [pending → refined → building → testing → validated]:

  /refine   → story file written (build contract with verify: commands)
  /build    → code + tests
  /validate → 5 gates: Security → Tests → UI → ACs → Review
  → PASS: feature validated
  → FAIL: fix + re-validate (max 3 cycles, then escalate)

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
- Project-specific directories (`specs/`, `memory/`, `stacks/`)

### 2. Open in your AI IDE

Open the project in **Cursor** or **Claude Code**. The AI will automatically pick up the rules and follow the framework workflow.

### 3. Start building

In Claude Code, use the slash commands directly:

```
/spec                        # Define your project (constitution → scoping → design → architecture)
/refine candidate-profile    # Break a feature into stories with verify: commands
/build candidate-profile     # Implement the refined story
/validate candidate-profile  # Run all verify: commands independently
/review                      # Final review before PR
```

In Cursor, describe your task and the AI follows the same workflow via `.cursorrules`.

Skills enforce phase order via filesystem checks: you can't build before the story file exists, you can't review before all features are validated. Each phase ends with clear options and next steps.

### 4. Update the framework

When the framework gets improvements, update all projects at once:

```bash
cd my-project
git submodule update --remote framework
```

## Framework structure

```
ai-spec-driven-generator/
├── agents/                  # 10 specialized agent definitions (core + ref split)
│   ├── orchestrator.md      # Orchestration rules reference (enforced by skills)
│   ├── product-owner.md     # Scoping, spec writing, AC format
│   ├── ux-ui.md             # UX/UI design — WCAG 2.1 AA
│   ├── architect.md         # Architecture + implementation manifest + shared component inventory + interactive best practices
│   ├── refinement.md        # Feature breakdown, story files, verify: commands, UX gate, ADR gate, component reuse audit
│   ├── developer.md         # Code implementation (manifest-scoped, component reuse check, stale detection, deployment reminder)
│   ├── validator.md         # Independent verification (spec contract, forbidden patterns, manifest scope)
│   ├── tester.md            # Test writing (batch sizing, kill-tests, ensemble assessment)
│   ├── reviewer.md          # Quality audit (3-pass, manifest scope enforcement, recurring failure logging)
│   ├── security.md          # Security audit — OWASP Top 10
│   ├── devops.md            # CI/CD & deployment
│   └── *.ref.md             # Templates and examples (loaded on demand)
├── skills/                  # Skill dispatchers with phase guards
│   ├── spec/SKILL.md        # /spec — constitution → scoping → clarify → design → arch
│   ├── refine/SKILL.md      # /refine — break feature into story file
│   ├── build/SKILL.md       # /build — implement from story file
│   ├── validate/SKILL.md    # /validate — execute verify: commands
│   └── review/SKILL.md      # /review — final quality gate
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
│   ├── feature-tracker.yaml # Per-feature state tracking
│   ├── story-template.yaml  # Refinement output (build contract)
│   └── manifest-template.yaml # Implementation manifest (2-phase build contract)
├── stacks/                  # Stack profiles & quality hooks
│   ├── hooks/               # Claude Code quality gate hooks
│   │   ├── hook-config.json # Anti-patterns, external checks, skip dirs
│   │   └── code_review.py   # Automated code review hook (Pass 2) — JSON verdict
│   └── stack-profile-template.md
├── examples/                # Example specs
│   └── todo-app-spec.yaml   # With structured ACs and verify: commands
├── memory/                  # Memory templates
│   ├── memory-template.md   # With feature status table
│   ├── LESSONS.md.template
│   └── SYNC.md.template
├── _docs/
│   └── test-methodology.md  # Two-loop test approach (spec→oracle + mutation feedback)
├── scripts/
│   ├── init-project.sh      # Project initializer
│   ├── check_test_quality.py    # Enforcement: no .skip(), no mock-soup, no weak assertions
│   ├── check_oracle_assertions.py # Enforcement: ORACLE blocks on numeric assertions
│   ├── check_write_coverage.py   # Enforcement: write-path coverage verification
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
├── specs/
│   ├── constitution.md     # Non-negotiable project principles
│   ├── my-project.yaml     # YAML spec
│   ├── my-project-clarifications.md  # Resolved ambiguities
│   ├── my-project-ux.md    # UX design (if UI project)
│   ├── my-project-arch.md  # Architecture plan
│   ├── feature-tracker.yaml # Per-feature state (pending→validated)
│   └── stories/            # Build contracts per feature
│       ├── auth.yaml
│       └── todos-crud.yaml
├── memory/
│   ├── my-project.md       # Project memory (with feature status table)
│   ├── LESSONS.md          # Failure memory
│   └── SYNC.md             # Framework version sync
├── stacks/                 # Stack profiles
├── apps/                   # Application code
├── packages/               # Shared packages
├── .claude/commands/       # Claude Code slash commands (copied from framework)
│   ├── spec.md
│   ├── refine.md
│   ├── build.md
│   ├── validate.md
│   └── review.md
├── CLAUDE.md               # AI rules
└── .cursorrules            # Cursor rules
```

## Code Quality & Test Robustness

The framework generates production-ready code by enforcing quality at every pipeline stage — not just at review time.

### Two-Loop Test Generation
- **Loop 1 (Proactive)**: Refinement agent pre-computes oracle values with step-by-step math. Developer copies these into `# ORACLE:` comment blocks. Tests verify exact expected values, not vague assertions.
- **Loop 2 (Reactive)**: After tests pass, mutation testing introduces faults (flip operators, change values). If tests don't catch the mutations (score < 70%), they're weak — targeted kill-tests are written for each surviving mutant.

### Enforcement Pipeline
Three Python scripts block commits if violations are found:
- `check_test_quality.py` — no `.skip()`, no mock-soup in integration tests, no fixture-only tests
- `check_oracle_assertions.py` — every numeric assertion needs an ORACLE comment with step-by-step math
- `check_write_coverage.py` — every data store with a read endpoint must have production write code

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
