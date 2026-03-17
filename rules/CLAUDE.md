# CLAUDE.md — Rules for Claude Code

## Context
This project uses an AI-powered project generation framework. You must follow a structured, phase-based process with human validation and persistent memory.

## How to use this framework

### Start a new project
1. The user describes their idea (or provides a YAML spec)
2. You embody the `orchestrator` agent (read `agents/orchestrator.md`)
3. You start with Phase 0 (Scoping) with the `product-owner`
4. You execute phases one by one, delegating to specialized agents
5. You maintain the project memory between each phase

### Resume an existing project
1. Read `memory/[project-name].md` to restore context
2. Identify the current phase
3. Summarize the project state to the user
4. Resume where it left off

### Complete workflow
```
User: "I want to create [project description]"

You:
1. Load orchestrator → agents/orchestrator.md
2. Create memory → memory/[project-name].md
3. Phase 0 (Scoping) → agents/product-owner.md + prompts/phases/00-scoping.md
4. Present spec → wait for validation → update memory
5. Phase 0.5 (Design) → agents/ux-ui.md + prompts/phases/00.5-design.md
6. Present design → wait for validation → update memory
7. Phase 1 (Plan) → agents/architect.md + prompts/phases/01-plan.md
8. Present plan → wait for validation → update memory
9. Phase 2 (Scaffold) → agents/developer.md + prompts/phases/02-scaffold.md
10. Present scaffold → wait for validation → update memory
... and so on for phases 3, 4, 5, 6
```

### Quick commands
- `@generate <spec-path>` — Launch full generation from an existing spec
- `@scoping` — Launch only Phase 0 (PO Scoping)
- `@plan <spec-path>` — Launch only Phase 1 (Plan)
- `@resume` — Resume the last in-progress phase (reads memory)
- `@status` — Display progress status (reads memory)

### Strict rules
1. **Always read memory** at the start of a session
2. **Always update memory** after each phase
3. **Always follow phase order** (no shortcuts)
4. **Always request validation** at checkpoints
5. **Always generate code in `output/[project-name]/`**
6. **Never over-engineer** — follow the spec, nothing more
7. **Never invent features** not present in the spec
8. **Never code before** scoping + design + plan are validated

### Available agents
Detailed instructions for each agent are in `agents/`:
- `orchestrator.md` — Coordination, memory, and validation
- `product-owner.md` — Scoping, user stories, YAML spec
- `ux-ui.md` — UX design, wireframes, design system
- `architect.md` — Architecture and technical planning
- `refinement.md` — Feature detail and breakdown before implementation
- `developer.md` — Code implementation
- `tester.md` — Writing and running tests
- `reviewer.md` — Quality and security audit
- `devops.md` — CI/CD and deployment

### Phase prompts
Detailed instructions for each phase are in `prompts/phases/`:
- `00-scoping.md` — Scoping with the Product Owner
- `00.5-design.md` — UX/UI Design
- `01-plan.md` — Architecture planning
- `02-scaffold.md` — Project setup
- `03-implement.md` — Feature implementation
- `04-test.md` — Tests
- `05-review.md` — Code review
- `06-deploy.md` — Deployment configuration

### Memory
- Template: `memory/memory-template.md`
- Project file: `memory/[project-name].md`
- Update: after each phase and each user feedback
- Contains: phase status, decisions, feedback, issues, key files

### Output convention
All generated projects go in: `output/<project-name>/`
