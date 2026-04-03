[< Back to Index](INDEX.md)

# Development Workflow

Reusable workflow for building projects with AI agents and human oversight.
An AI reading this document can reproduce the full workflow on any new project.

---

## Concept

One user, one AI, filesystem as the source of truth.

| Concern | Tool | Responsibility |
|---------|------|----------------|
| Product spec | specs/*.yaml | What to build -- written by /spec, refined by /refine |
| Feature state | specs/feature-tracker.yaml | Progress tracking -- updated by skills automatically |
| Code + tests | Git | Implementation -- written by builder agents |
| Quality gates | scripts/*.py | Enforcement -- run by skills, exit code is truth |
| Memory | memory/ | Lessons, sync state, project decisions |

**Rule**: The filesystem is the single source of truth. Phase gates are filesystem checks (file exists or not), not LLM memory. Feature state lives in feature-tracker.yaml, not in conversation history.

---

## Build Order

Always build features in dependency order. Each feature depends on the previous.

Typical order for a full-stack project:

| # | What | Builder agent | Prerequisite |
|---|------|---------------|-------------|
| 1 | Infrastructure | builder-infra | Architecture plan exists |
| 2 | Database schema | builder-migration | Infra done |
| 3 | Auth service | builder-service | DB done |
| 4 | Core API services | builder-service | Auth done |
| 5 | External integrations | builder-exchange | Core API done |
| 6 | Frontend | builder-frontend | API services done, UX spec exists |
| 7 | CI/CD | devops | All services done |

The `/build` skill reads the feature-tracker.yaml and respects dependency chains. A feature with unmet dependencies is skipped with a warning.

---

## Stale Feature Detection

A feature is considered **stale** when it has been in `building` state with no recent commits. The developer agent checks for this condition before starting work and warns the user.

Indicators of staleness:
- Feature in `building` state for more than one session with no matching commits
- Story file exists but no code files match the declared scope
- Build contract has `building` state but git log shows no commits tagged with the feature name

**Resolution**: User decides whether to continue building, reset to `refined`, or escalate.

---

## Branch Strategy: Git Flow

```
main ─────────────────────────────────────────── (production, releases only)
  │
  └── develop ────────────────────────────────── (integration, all feature work)
        │
        ├── feature/auth ─────── (merged back to develop)
        ├── feature/dashboard ── (merged back to develop)
        └── feature/api ──────── (merged back to develop)
```

| Branch | Purpose | Merges to | Who merges |
|--------|---------|-----------|------------|
| main | Production releases only | -- | User (manual) |
| develop | Integration branch, all feature work | main (release) | User (manual) |
| feature/* | One branch per feature | develop | User after /review PASS |

### Rules
- Agents create feature branches from `develop`, never from `main`
- Feature branches are merged to `develop` after /review PASS and human approval
- `main` is only updated via release merges from `develop`
- Never force-push to `main` or `develop`
- Git worktree isolation is available for parallel work on unrelated features

---

## State Recovery Procedures

### Session interrupted mid-build
The build contract (specs/stories/[feature].yaml) and feature-tracker.yaml survive between sessions. On the next `/build`, the developer agent:
1. Reads feature-tracker.yaml to find the current state
2. Reads the story file for the implementation scope
3. Checks git log for any commits already made
4. Resumes from where it left off (does not restart from scratch)

### Validation failed 3 times
Feature is moved to `escalated` state in feature-tracker.yaml. Human must:
1. Read the validator's failure reports in the story comments
2. Decide: fix manually, reset to `refined` for re-planning, or descope the feature
3. Update feature-tracker.yaml manually to `building` or `refined` to resume

### Feature stuck in building
Run `/validate feature-name` to check current state. If code exists but tests fail:
1. Review the test failures
2. Run `/build feature-name` to resume (developer agent reads existing code)
3. If the issue is architectural, reset to `refined` and re-run `/refine`

### Corrupted feature-tracker.yaml
Reconstruct from filesystem:
- If specs/stories/[feature].yaml exists --> at least `refined`
- If git commits tagged with the feature exist --> at least `building`
- If all verify: commands pass --> `validated`

---

## _work/ Directory Structure

Projects that use this framework as a submodule use `_work/` for all live agent working state. The framework itself does not use `_work/` -- it provides the agents, skills, scripts, and templates.

```
project-root/
├── framework/                  # Git submodule → ai-spec-driven-generator
├── specs/
│   ├── constitution.md         # Non-negotiable project principles
│   ├── [project].yaml          # YAML spec (product definition)
│   ├── [project]-clarifications.md
│   ├── [project]-ux.md         # UX design (if UI project)
│   ├── [project]-arch.md       # Architecture plan
│   ├── feature-tracker.yaml    # Per-feature state (pending→validated)
│   └── stories/                # Build contracts per feature
│       ├── auth.yaml
│       └── dashboard.yaml
├── memory/
│   ├── [project].md            # Project memory (decisions, feedback)
│   ├── LESSONS.md              # Recurring failure patterns
│   └── SYNC.md                 # Framework version sync
├── stacks/                     # Stack profiles (coding contracts)
│   └── hooks/                  # Quality gate hooks
│       ├── hook-config.json
│       └── code_review.py
├── apps/                       # Application code
├── packages/                   # Shared packages
├── .claude/
│   ├── settings.json           # Hook config
│   └── skills/                 # Symlinked from framework
├── CLAUDE.md                   # Project-specific rules
└── .cursorrules                # Cursor rules (if using Cursor)
```

### Key directories

| Directory | What it holds | Committed to git? |
|-----------|--------------|-------------------|
| specs/ | Product definition, stories, feature tracker | Yes |
| specs/stories/ | Per-feature build contracts with verify: commands | Yes |
| memory/ | Lessons, sync state, project decisions | Yes |
| stacks/ | Stack profiles and quality hooks | Yes |
| stacks/hooks/ | code_review.py, hook-config.json, sonar_check.py | Yes |
| apps/ | Application source code | Yes |
| _cache/ | Tool caches (pytest, ruff, mypy) | No (.gitignore) |

---

## What an AI Needs to Start a Session

When beginning any work, Claude must:

1. Read `CLAUDE.md` -- project rules, stack choices, hard constraints
2. Read `specs/feature-tracker.yaml` -- current state of all features
3. Read `memory/LESSONS.md` -- recurring failures to avoid
4. Read the relevant agent playbook (`framework/agents/<agent>.md`)
5. Read the story file (`specs/stories/[feature].yaml`) -- if building or validating

The skill system handles this automatically. Using `/build`, `/refine`, `/validate`, or `/review` loads the correct context.

---

## Adapting to a New Project

### Automated setup

```bash
./framework/scripts/init-project.sh my-project /path/to/workspace
```

This creates:
- A git submodule pointing to the framework
- CLAUDE.md configured for the project
- Project directories (specs/, memory/, stacks/)
- Symlinked skills from the framework

### What you write from scratch (per project)

- `specs/[project].yaml` -- full product spec
- `specs/constitution.md` -- non-negotiable principles
- `CLAUDE.md` -- stack choices, constraints, IDs
- Stack profiles in `stacks/` -- coding contracts per technology
- `stacks/hooks/hook-config.json` -- anti-patterns and external checks

### What comes from the framework (unchanged)

- All 19 agent playbooks in `framework/agents/`
- All 10 skills in `framework/skills/`
- All 9 enforcement scripts in `framework/scripts/`
- Templates in `framework/specs/templates/`
- Memory templates in `framework/memory/`
