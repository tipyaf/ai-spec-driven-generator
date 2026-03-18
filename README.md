# ai-spec-driven-generator

An AI-powered framework for generating complete code projects from structured YAML specs. Works with **Cursor** and **Claude Code**.

## Overview

This framework uses specialized AI agents, a phased workflow with human validation at every step, and persistent memory between sessions to generate any type of code project from a single YAML specification.

## Features

- **Spec-driven**: YAML specs as the single source of truth
- **9 specialized agents**: Product Owner, UX/UI Designer, Architect, Refinement, Developer, Tester, Reviewer, DevOps, Orchestrator
- **Phase-based workflow**: Scoping → Design → Plan → Scaffold → [Refinement → Implement → Test] → Review → Deploy
- **Human validation gates**: Between every phase
- **Persistent memory**: Per-project markdown files tracking decisions, feedback, and phase status
- **Project management integration**: Shortcut.com support for ticket creation and tracking
- **Tool-agnostic**: Works with both Cursor (`.cursorrules`) and Claude Code (`CLAUDE.md`)

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
[Phase 6: Deploy Config]   → DevOps       → ✅ Human Validation
```

## Quick start

### 1. Clone the framework

```bash
git clone https://github.com/your-org/ai-spec-driven-generator.git
```

### 2. Create a new project

```bash
cd ai-spec-driven-generator
./scripts/init-project.sh my-project /path/to/workspace
```

This creates a new project directory with symlinks to the framework and copies of the rules files.

### 3. Open in your AI IDE

Open the project in **Cursor** or **Claude Code**. The AI will automatically pick up the rules and follow the framework workflow.

### 4. Start building

Describe your project idea to the AI, or provide a YAML spec. The AI will guide you through each phase with human validation at every step.

## Framework structure

```
ai-spec-driven-generator/
├── agents/                  # 9 specialized agent definitions
│   ├── orchestrator.md      # Main coordinator
│   ├── product-owner.md     # Scoping & spec writing
│   ├── ux-ui.md             # UX/UI design
│   ├── architect.md         # Architecture planning
│   ├── refinement.md        # Feature breakdown & tickets
│   ├── developer.md         # Code implementation
│   ├── tester.md            # Test writing & execution
│   ├── reviewer.md          # Quality & security audit
│   └── devops.md            # CI/CD & deployment
├── prompts/phases/          # Phase-specific instructions
│   ├── 00-scoping.md
│   ├── 00.5-design.md
│   ├── 01-plan.md
│   ├── 02-scaffold.md
│   ├── 03-implement.md
│   ├── 04-test.md
│   ├── 05-review.md
│   └── 06-deploy.md
├── rules/                   # IDE integration rules
│   ├── CLAUDE.md            # Rules for Claude Code
│   └── .cursorrules         # Rules for Cursor
├── specs/templates/         # YAML spec templates
│   └── spec-template.yaml
├── examples/                # Example specs
│   └── todo-app-spec.yaml
├── memory/                  # Memory templates
│   └── memory-template.md
├── scripts/                 # Utility scripts
│   └── init-project.sh      # Project initializer
├── stacks/                  # Tech stack definitions (extensible)
└── output/                  # Default output directory
```

## Project structure (after init)

```
my-project/
├── agents/          → (symlink to framework)
├── prompts/         → (symlink to framework)
├── specs/
│   ├── templates/   → (symlink to framework)
│   └── my-project.yaml  # Your project spec
├── examples/        → (symlink to framework)
├── memory/
│   └── my-project.md    # Your project memory
├── output/               # Generated code goes here
├── CLAUDE.md             # (copied from framework)
├── .cursorrules          # (copied from framework)
└── .gitignore
```

## Commands

Once in an AI IDE session:

| Command | Description |
|---------|-------------|
| `@generate <spec>` | Full generation from an existing spec |
| `@scoping` | Start Phase 0 (PO scoping) |
| `@plan <spec>` | Start Phase 1 (architecture planning) |
| `@resume` | Resume the last in-progress phase |
| `@status` | Display current progress |

## Contributing

Every improvement to the framework should be a commit + PR on this repo. Projects that use the framework get updates automatically via symlinks (or by pulling the latest version if using git submodules).

## License

MIT
