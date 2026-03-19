# ai-spec-driven-generator

An AI-powered framework for generating complete code projects from structured YAML specs. Works with **Cursor** and **Claude Code**.

## Overview

This framework uses specialized AI agents, a phased workflow with human validation at every step, and persistent memory between sessions to generate any type of code project from a single YAML specification.

## Features

- **Spec-driven**: YAML specs as the single source of truth
- **10 specialized agents**: Product Owner, UX/UI Designer, Architect, Refinement, Developer, Tester, Reviewer, Security, DevOps, Orchestrator
- **Phase-based workflow**: Scoping → Design → Plan → Scaffold → [Refinement → Implement → Test] → Review → Security → Deploy
- **Human validation gates**: Between every phase
- **Persistent memory**: Per-project markdown files tracking decisions, feedback, and phase status
- **Project management integration**: Shortcut.com support for ticket creation and tracking
- **Tool-agnostic**: Works with both Cursor (`.cursorrules`) and Claude Code (`CLAUDE.md`)
- **Stack profiles**: Coding and security contracts generated per tech stack

## Workflow

```
[Phase 0: Scoping]        → PO           → ✅ Human Validation
[Phase 0.5: Design]       → UX/UI        → ✅ Human Validation
[Phase 1: Plan]            → Architect    → ✅ Human Validation
[Phase 2: Scaffold]        → Developer    → ✅ Human Validation
  ┌─── For each feature: ─────────────────────────────┐
  │ [Phase 2.5: Refinement] → Refinement → ✅ Valid.  │
  │ [Phase 3: Implement]    → Developer  → ✅ Valid.   │
  │ [Phase 4: Test]         → Tester     → ✅ Valid.   │
  └────────────────────────────────────────────────────┘
[Phase 5: Review]          → Reviewer     → ✅ Human Validation
[Phase 5.5: Security]     → Security     → ✅ Human Validation
[Phase 6: Deploy Config]   → DevOps       → ✅ Human Validation
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
├── agents/                  # 10 specialized agent definitions
│   ├── orchestrator.md      # Main coordinator
│   ├── product-owner.md     # Scoping & spec writing
│   ├── ux-ui.md             # UX/UI design
│   ├── architect.md         # Architecture planning
│   ├── refinement.md        # Feature breakdown & tickets
│   ├── developer.md         # Code implementation
│   ├── tester.md            # Test writing & execution
│   ├── reviewer.md          # Quality audit
│   ├── security.md          # Security audit (OWASP, auth, data)
│   └── devops.md            # CI/CD & deployment
├── prompts/phases/          # Phase-specific instructions
│   ├── 00-scoping.md
│   ├── 00.5-design.md
│   ├── 01-plan.md
│   ├── 02-scaffold.md
│   ├── 03-implement.md
│   ├── 04-test.md
│   ├── 05-review.md
│   ├── 05.5-security.md
│   └── 06-deploy.md
├── rules/                   # IDE integration
│   ├── CLAUDE.md            # Rules for Claude Code (legacy, direct use)
│   ├── CLAUDE.md.template   # Template for project init (uses framework/ paths)
│   └── .cursorrules         # Rules for Cursor
├── specs/templates/         # YAML spec templates
│   └── spec-template.yaml
├── stacks/                  # Stack profile template
│   └── stack-profile-template.md
├── examples/                # Example specs
│   └── todo-app-spec.yaml
├── memory/                  # Memory templates
│   └── memory-template.md
├── scripts/                 # Utility scripts
│   └── init-project.sh      # Project initializer (submodule-based)
└── output/                  # Default output directory (legacy)
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
