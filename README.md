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
- **3-pass code review**: KISS & readability → static analysis → safety & correctness
- **Independent validation**: the agent that writes code is never the agent that validates it
- **Test quality standards**: explicit "real test vs mock-soup" checklists, forbidden test patterns
- **Failure memory (LESSONS.md)**: recurring mistakes logged and read by all agents before starting
- **Language-agnostic hooks**: configurable `hook-config.json` with `{files}`, `filter`, `cwd` placeholders

### Infrastructure
- **Persistent memory**: per-project markdown files tracking decisions, feedback, phase status, and feature progress
- **Project management integration**: Shortcut.com support for ticket creation and tracking
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

Describe your project idea to the AI. It will automatically guide you through:

1. **`/spec`** — Constitution, scoping (one question at a time), clarification, UX design, architecture planning
2. **`/refine`** — Break features into stories with structured ACs and `verify:` commands
3. **`/build`** — Implement each story with 5 sequential quality gates
4. **`/validate`** — Independent verification executing every `verify:` command
5. **`/review`** — Full code review + security audit before PR

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
│   ├── architect.md         # Architecture + implementation manifest
│   ├── refinement.md        # Feature breakdown, story files, verify: commands
│   ├── developer.md         # Code implementation (scoped to story files)
│   ├── validator.md         # Independent verification (executes verify: commands)
│   ├── tester.md            # Test writing & execution
│   ├── reviewer.md          # Quality audit (3-pass)
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
├── rules/                   # IDE integration
│   ├── CLAUDE.md            # Rules for Claude Code
│   ├── CLAUDE.md.template   # Template for project init
│   └── .cursorrules         # Rules for Cursor
├── specs/templates/         # YAML templates
│   ├── spec-template.yaml   # Spec with unified AC format
│   ├── feature-tracker.yaml # Per-feature state tracking
│   └── story-template.yaml  # Refinement output (build contract)
├── stacks/                  # Stack profiles & quality hooks
│   ├── hooks/               # Claude Code quality gate hooks
│   └── stack-profile-template.md
├── examples/                # Example specs
│   └── todo-app-spec.yaml   # With structured ACs and verify: commands
├── memory/                  # Memory templates
│   ├── memory-template.md   # With feature status table
│   ├── LESSONS.md.template
│   └── SYNC.md.template
├── scripts/
│   └── init-project.sh      # Project initializer
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
├── CLAUDE.md               # AI rules
└── .cursorrules            # Cursor rules
```

## Contributing

Every improvement to the framework should be a commit + PR on this repo. Projects that use the framework get updates via:

```bash
git submodule update --remote framework
```

## License

MIT
