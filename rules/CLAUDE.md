# CLAUDE.md — Rules for Claude Code

## Context
This project uses an AI-powered project generation framework. You must follow a structured, phase-based process with human validation and persistent memory.

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
| `/review` | Review code quality before PR | reviewer, security, tester |
| `/validate` | Verify implementation against spec | validator |

**Default workflow**: `/spec` → `/refine` → `/build` → `/validate` → `/review`

## Loading agents (IMPORTANT)

When you need an agent, read ONLY its core file:
- `agents/[name].md` — core instructions (always read this)
- `agents/[name].ref.md` — templates and examples (read only when you need a specific template)

**NEVER read all agent files at once.** Load the minimum needed for the current task.

## On session start

### New project (no memory file exists)
When a user describes a project idea or asks to build something:
1. Tell the user: "We'll define your project together before writing any code. I'll guide you through 4 phases: Scoping → Design → Architecture → then we build."
2. Launch `/spec` — this guides through Phase 0, 0.5, and 1 with human validation at each step
3. After `/spec` is complete: launch `/refine` to break features into stories
4. Only then: `/build` for each refined story

**NEVER jump to code.** Always start with `/spec`.

### Existing project (memory file exists)
1. Read `memory/[project-name].md` to restore context
2. Read `memory/LESSONS.md` for known pitfalls
3. Identify the current phase
4. Summarize the project state to the user: what's done, what's next, what decisions are needed
5. Resume where it left off — use the appropriate skill

## Phase workflow
```
Phase 0: Scoping        → /spec    → product-owner.md   → ✅ Human
Phase 0.5: Design       → /spec    → ux-ui.md           → ✅ Human
Phase 0.7: Ordering     → /spec    → product-owner.md   → ✅ Human
Phase 1: Plan            → /spec    → architect.md       → ✅ Human
Phase 2: Scaffold        → /build   → developer.md       → 🤖 Auto
  ┌─── Per feature: ─────────────────────────────────────────────┐
  │ Phase 2.5: Refinement → /refine  → refinement.md  → ✅ Human │
  │ Phase 3: Implement    → /build   → developer.md   → 🤖 Auto  │
  │ Phase 3.5: Validate   → /validate → validator.md  → 🤖 Auto  │
  │ Phase 4: Test         → /build   → tester.md      → 🤖 Auto  │
  └───────────────────────────────────────────────────────────────┘
Phase 5: Review          → /review  → reviewer.md       → 🤖 Auto
Phase 5.5: Security      → /review  → security.md       → 🤖 Auto
Phase 6: Deploy Config   →           devops.md          → ✅ Human
Phase 7: Release         →           orchestrator.md    → ✅ Human
```

## Strict rules
1. **Always read memory** at session start
2. **Always update memory** after each phase
3. **Always follow phase order** — no shortcuts
4. **Never load all agents** — use skills to load only what's needed
5. **Never over-engineer** — follow the spec, nothing more
6. **Never code before** scoping + design + plan are validated

## Phase guards

Before executing a skill, verify its prerequisites are met:

| Skill | Prerequisites | If missing |
|-------|--------------|------------|
| `/spec` | None — this is the starting point | — |
| `/refine` | Spec validated (Phase 0 + 0.5 + 1 done) | → Tell user: "Let's define the project first" → launch `/spec` |
| `/build` | Story refined with ACs (Phase 2.5 done) | → Tell user: "This story needs refinement first" → launch `/refine` |
| `/validate` | Implementation exists (Phase 3 done) | → Tell user: "Nothing to validate yet" → launch `/build` |
| `/review` | Validation passed (Phase 3.5 done) | → Tell user: "Let's validate first" → launch `/validate` |

## Agent role guards

| Agent | CAN do | CANNOT do |
|-------|--------|-----------|
| Product Owner | Write specs, challenge scope | Write code, make technical decisions |
| UX/UI Designer | Design UI, specify flows | Write code, choose frameworks |
| Architect | Plan architecture, create manifest | Write implementation code |
| Refinement | Break features into stories | Write code, make architecture decisions |
| Developer | Write code, create files | Self-validate, skip manifest |
| Validator | Run checks, take screenshots | Modify source code, fix bugs |
| Tester | Write tests, run suites | Modify feature code |
| Reviewer | Audit quality, flag issues | Modify files directly |
| Security | Audit security, flag vulns | Modify files directly |
| DevOps | Configure CI/CD, deployment | Modify feature code |
| Orchestrator | Coordinate phases, enforce gates | Skip phases, bypass validation |

## File locations
- **Agents**: `agents/*.md` (core) + `agents/*.ref.md` (templates)
- **Phase prompts**: `prompts/phases/`
- **Spec templates**: `specs/templates/`
- **Stack profiles**: `stacks/`
- **Memory**: `memory/[project-name].md`
- **Lessons**: `memory/LESSONS.md`
