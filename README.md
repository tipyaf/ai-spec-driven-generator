# ai-spec-driven-generator

An AI-powered framework for generating complete code projects from structured YAML specs. Works with **Cursor** and **Claude Code**.

## Overview

This framework uses specialized AI agents, a phased workflow with human validation at every step, and persistent memory between sessions to generate any type of code project from a single YAML specification.

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

### 4. Update the framework

When the framework gets improvements, update all projects at once:

```bash
cd my-project
git submodule update --remote framework
```

## Framework structure

```
ai-spec-driven-generator/
├── agents/                  # 11 specialized agent definitions
│   ├── orchestrator.md      # Main coordinator
│   ├── product-owner.md     # Scoping & spec writing
│   ├── ux-ui.md             # UX/UI design (WCAG 2.1 AA contrast ratios)
│   ├── architect.md         # Architecture planning + implementation manifest
│   ├── refinement.md        # Feature breakdown & tickets
│   ├── developer.md         # Code implementation (manifest-driven)
│   ├── validator.md         # Independent verification (screenshots, grep, curl)
│   ├── tester.md            # Test writing & execution
│   ├── reviewer.md          # Quality audit
│   ├── security.md          # Security audit (OWASP, auth, data)
│   └── devops.md            # CI/CD & deployment
├── prompts/phases/          # Phase-specific instructions
│   ├── 00-scoping.md        # Includes acceptance_tests requirement
│   ├── 00.5-design.md       # Includes WCAG contrast validation
│   ├── 00.7-ordering.md     # Feature ordering
│   ├── 01-plan.md           # Includes implementation manifest requirement
│   ├── 02-scaffold.md
│   ├── 03-implement.md
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
│       └── settings-hooks-example.json  # Ready-to-use config
├── examples/                # Example specs
│   └── todo-app-spec.yaml
├── memory/                  # Memory templates
│   └── memory-template.md
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
│   └── my-project.md       # Project memory (updated by agents)
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
