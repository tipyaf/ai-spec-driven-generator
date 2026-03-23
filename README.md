# ai-spec-driven-generator

An AI-powered framework for generating complete code projects from structured YAML specs. Works with **Cursor** and **Claude Code**.

## Overview

This framework uses specialized AI agents, a phased workflow with human validation at every step, and persistent memory between sessions to generate any type of code project from a single YAML specification.

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
Once the product is well-defined (Phases 0–1), the framework generates **production-ready code** without human intervention on technical tasks.

- **Humans decide**: product scope, UX design, architecture choices, infrastructure, release go/no-go
- **Machines verify**: code quality, tests, accessibility, security, conventions, anti-patterns

The developer never self-validates. An independent validator agent verifies every implementation. Tests, reviews, and security audits are fully automated with escalation to humans only after 3 failures.

### 3. Accompaniment
The framework **guides and challenges** the user to build the best possible product. The user follows instructions and answers questions — never left without clear next steps.

- The Product Owner **challenges assumptions**: "Is this feature really MVP? What happens if you ship without it?"
- The Architect **presents options**: comparison tables with trade-offs, not just a single recommendation
- Every phase **ends with clear guidance**: what was done, what's next, what the user needs to decide
- The framework **explains why** it asks questions and enforces rules

## Features

- **Spec-driven**: YAML specs as the single source of truth
- **11 specialized agents**: Product Owner, UX/UI Designer, Architect, Refinement, Developer, **Validator**, Tester, Reviewer, Security, DevOps, Orchestrator
- **Phase-based workflow**: Scoping → Design → Plan → Scaffold → [Refinement → Implement → **Validate** → Test] → Review → Security → Deploy
- **Automated validation**: Independent validator agent verifies implementations with screenshots, grep, curl — no self-assessment
- **Machine-verifiable acceptance tests**: Visual, runtime, grep, and e2e tests defined in specs
- **Context slicing**: Architect produces implementation manifests so dev agents only load relevant files
- **Quality hooks**: Pre-commit anti-pattern detection, post-edit design system compliance
- **Smart validation**: Human decides (product, architecture, infra), machines verify (tests, review, security)
- **Persistent memory**: Per-project markdown files tracking decisions, feedback, and phase status
- **Project management integration**: Shortcut.com support for ticket creation and tracking
- **Tool-agnostic**: Works with both Cursor (`.cursorrules`) and Claude Code (`CLAUDE.md`)
- **Stack profiles**: Coding and security contracts generated per tech stack
- **Failure memory (LESSONS.md)**: Recurring mistakes are logged and read by all agents before starting work — the framework learns from its errors
- **Language-agnostic hooks**: Configurable `hook-config.json` with `{files}`, `filter`, `cwd` placeholders — works with any language (TypeScript, Python, Rust, Go, Java, etc.)
- **Agent role guards**: Strict enforcement of agent boundaries — refiner never codes, reviewer never modifies files, developer never self-validates
- **Deployment verification**: Post-deploy health checks, smoke tests, rollback plan documentation
- **Skills system**: `/refine`, `/build`, `/review`, `/validate`, `/spec` — slash commands that load only the agents needed for the current task
- **Auto-versioning**: GitHub Action bumps VERSION on every push, auto-generates CHANGELOG
- **Framework sync tracking**: SYNC.md tracks which version each project uses
- **3-pass code review**: KISS & readability → static analysis → safety & correctness
- **Test quality standards**: Explicit "real test vs mock-soup" checklists, forbidden test patterns
- **Hard constraints**: NEVER/Always rules in every agent — critical rules are visually distinct
- **Token-optimized agents**: Each agent split into core (rules, workflow) + ref (templates, examples) — 60% fewer tokens per session
- **Lazy agent loading**: Skills load only the required agents per task — never all 11 at once. Principles enforced via CLAUDE.md

## Workflow

```
[Phase 0: Scoping]         → PO           → ✅ Human (product decision)
[Phase 0.5: Design]        → UX/UI        → ✅ Human (UX decision)
[Phase 0.7: Ordering]      → PO           → ✅ Human (priority decision)
[Phase 1: Plan]            → Architect    → ✅ Human (architecture decision)
[Phase 2: Scaffold]        → Developer    → 🤖 Auto
  ┌─── For each feature: ───────────────────────────────────────┐
  │ [Phase 2.5: Refinement]  → Refinement  → ✅ Human (scope)  │
  │ [Phase 3: Implement]     → Developer   →                    │
  │ [Phase 3.5: Validate]    → Validator   → 🤖 Auto (max 3x)  │
  │ [Phase 4: Test]          → Tester      → 🤖 Auto (e2e+TU)  │
  └──────────────────────────────────────────────────────────────┘
[Phase 5: Review]           → Reviewer     → 🤖 Auto
[Phase 5.5: Security]      → Security     → 🤖 Auto
[Phase 6: Deploy Config]    → DevOps       → ✅ Human (infra decision)
[Phase 7: Release]          → Orchestrator → ✅ Human (go/no-go)
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

Describe your project idea to the AI, or provide a YAML spec. The AI will guide you through each phase with human validation at every step.

Use `/spec` to start defining your project, `/refine` to break features into stories, `/build` to implement, `/review` to review code, `/validate` to verify.

### 4. Update the framework

When the framework gets improvements, update all projects at once:

```bash
cd my-project
git submodule update --remote framework
```

## Framework structure

```
ai-spec-driven-generator/
├── agents/                  # 11 specialized agent definitions (core + ref split)
│   ├── orchestrator.md      # Main coordinator (core)
│   ├── orchestrator.ref.md  # Templates, escalation procedures, model config
│   ├── product-owner.md     # Scoping & spec writing (core)
│   ├── product-owner.ref.md # AC examples, persona/story templates
│   ├── ux-ui.md             # UX/UI design — WCAG 2.1 AA (core)
│   ├── ux-ui.ref.md         # Design system templates, wireframes, components
│   ├── architect.md         # Architecture + implementation manifest (core)
│   ├── architect.ref.md     # Stack comparison, ADR, file structure templates
│   ├── refinement.md        # Feature breakdown & tickets (core)
│   ├── refinement.ref.md    # Ticket templates, Shortcut integration
│   ├── developer.md         # Code implementation (core)
│   ├── developer.ref.md     # File conventions, output format
│   ├── validator.md         # Independent verification (core)
│   ├── validator.ref.md     # Report templates, anti-pattern lists
│   ├── tester.md            # Test writing & execution (core)
│   ├── tester.ref.md        # Code examples, report templates
│   ├── reviewer.md          # Quality audit (core)
│   ├── reviewer.ref.md      # Review checklists, report format
│   ├── security.md          # Security audit — OWASP (core)
│   ├── security.ref.md      # Detailed checklists, threat model template
│   ├── devops.md            # CI/CD & deployment (core)
│   └── devops.ref.md        # Docker, CI/CD, deployment templates
├── skills/                  # Slash command skill dispatchers
│   ├── refine.md            # /refine — break features into stories
│   ├── build.md             # /build — implement a feature
│   ├── review.md            # /review — 3-pass code review
│   ├── validate.md          # /validate — verify implementation
│   └── spec.md              # /spec — define project from scratch
├── prompts/phases/          # Phase-specific instructions
│   ├── 00-scoping.md        # Includes acceptance_tests requirement
│   ├── 00.5-design.md       # Includes WCAG contrast validation
│   ├── 00.7-ordering.md     # Feature ordering
│   ├── 01-plan.md           # Includes implementation manifest requirement
│   ├── 02-scaffold.md
│   ├── 03-implement.md
│   ├── 03.5-validate.md
│   ├── 04-test.md
│   ├── 05-review.md
│   ├── 05.5-security.md
│   ├── 06-deploy.md
│   └── 07-release.md
├── rules/                   # IDE integration
│   ├── CLAUDE.md            # Rules for Claude Code (legacy, direct use)
│   ├── CLAUDE.md.template   # Template for project init (uses framework/ paths)
│   └── .cursorrules         # Rules for Cursor
├── specs/templates/         # YAML spec templates
│   └── spec-template.yaml   # Includes acceptance_tests section
├── stacks/                  # Stack profiles & quality hooks
│   ├── stack-profile-template.md
│   └── hooks/               # Claude Code quality gate hooks
│       ├── README.md        # Hook documentation
│       ├── settings-hooks-example.json  # Ready-to-use config
│       ├── hook-config.json # Language-agnostic hook configuration
│       └── code_review.py   # 3-pass code review hook
├── examples/                # Example specs
│   └── todo-app-spec.yaml
├── memory/                  # Memory templates
│   ├── memory-template.md
│   ├── LESSONS.md.template
│   └── SYNC.md.template     # Framework version sync tracker
├── VERSION                  # Current framework version
├── CHANGELOG.md             # Auto-generated changelog
├── BOOTSTRAP.md             # Bootstrap guide for new projects
├── .github/workflows/
│   └── bump-version.yml     # Auto-versioning on push
└── scripts/                 # Utility scripts
    └── init-project.sh      # Project initializer (submodule-based)
```

## Project structure (after init)

```
my-project/
├── framework/              # Git submodule → ai-spec-driven-generator
│   ├── agents/
│   ├── prompts/
│   ├── rules/
│   ├── stacks/
│   └── ...
├── specs/                  # Project-specific specs
│   ├── my-project.yaml     # YAML spec (Phase 0)
│   ├── my-project-ux.md    # UX design (Phase 0.5)
│   └── my-project-architecture.md  # Architecture plan (Phase 1)
├── memory/
│   ├── my-project.md       # Project memory (updated by agents)
│   ├── LESSONS.md          # Failure memory (logged mistakes, read by all agents)
│   └── SYNC.md             # Framework version sync tracker (from template)
├── stacks/                 # Stack profiles (Phase 1)
│   ├── typescript-nestjs.md
│   └── typescript-react.md
├── apps/                   # Application code (Phase 2+)
│   ├── api/
│   └── web/
├── packages/               # Shared packages (Phase 2+)
│   └── shared/
├── CLAUDE.md               # AI rules (generated from template)
├── .cursorrules            # Cursor rules (generated from template)
└── .gitignore
```

## Contributing

Every improvement to the framework should be a commit + PR on this repo. Projects that use the framework get updates via:

```bash
git submodule update --remote framework
```

## License

MIT
