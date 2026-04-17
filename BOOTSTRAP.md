# Bootstrap Guide (v5)

Step-by-step checklist for setting up a new project with this framework.

## Prerequisites
- [ ] Git installed
- [ ] Claude Code or Cursor installed
- [ ] Node.js (for JS/TS projects) or relevant language toolchain
- [ ] Python 3.11+ (framework orchestrator + check scripts)

## Option A: Automated setup (recommended)

```bash
./scripts/init-project.sh <project-name> <workspace-path>
```

This creates: submodule, CLAUDE.md (from `rules/CLAUDE.md.template`),
`specs/` + `memory/` + `_work/` directories, memory files, LESSONS.md,
SYNC.md, skills symlinks, hook config.

## Option B: Manual setup

### Step 1: Create project structure
- [ ] Create project directory
- [ ] Initialize git: `git init`
- [ ] Add framework as submodule: `git submodule add https://github.com/tipyaf/ai-spec-driven-generator.git framework`

### Step 2: Copy framework files
- [ ] Copy `framework/rules/CLAUDE.md.template` to `./CLAUDE.md`
- [ ] Copy `framework/rules/.cursorrules` to `./.cursorrules` (if using Cursor)
- [ ] Create `specs/`, `memory/`, `_work/stacks/`, `_work/build/`, `_work/spec/`
- [ ] Copy `framework/memory/memory-template.md` to `memory/<project-name>.md`
- [ ] Copy `framework/memory/LESSONS.md.template` to `memory/LESSONS.md`

### Step 3: Configure CLAUDE.md
- [ ] Update project name in CLAUDE.md
- [ ] Fill in `§Workflow state IDs` and `§Epic priority table` (if using a PM tool)
- [ ] Adjust `§Agent model overrides` if needed

### Step 4: Pick and activate stacks
- [ ] Decide which of the 4 built-in stacks apply: `python-fastapi`, `typescript-react`, `postgres`, `nodejs-express`
- [ ] Copy the chosen stack(s) from `framework/stacks/templates/<stack>/` to `_work/stacks/<stack>/`
- [ ] Create `_work/stacks/registry.yaml` listing active stacks
- [ ] For custom stacks, see `framework/stacks/CUSTOM_STACK_GUIDE.md`

### Step 5: Write initial spec
- [ ] Copy `framework/specs/templates/spec-template.yaml` to `specs/<project-name>.yaml`
- [ ] Fill in: name, type (`web-ui` / `web-api` / `cli`), description, target users, problem statement
- [ ] Launch `/spec` to start the scoping + architecture phases with the PO, UX, and architect agents

### Step 6: Install hooks (feedback loop)
- [ ] Run `framework/scripts/setup-hooks.sh` to install pre-commit, pre-push, and PR guard hooks
- [ ] Hooks are feedback-only — the orchestrator is the source of truth; `--no-verify` is caught at the next `/build`

### Step 7: Verify setup
- [ ] Run `/help` to list available commands
- [ ] Run `/spec` to start the PO agent
- [ ] Verify CLAUDE.md is picked up by your IDE
- [ ] Verify memory file is readable

## Post-setup checklist
- [ ] First commit with project structure (use `/ship` on the bootstrap story if there is one, otherwise a manual setup commit is fine)
- [ ] SYNC.md created with framework v5 version
- [ ] Team members onboarded

## After daily resumption

- [ ] `/next` — shows BLOCKING · IN-PROGRESS · READY · PENDING SHIP · SUGGESTIONS
- [ ] `/status` — dashboard view

## Optional: CI/CD belt

The framework runs without CI — the orchestrator re-runs everything on every
`/build` / `/ship`. If you want an independent CI witness:

```bash
framework/scripts/generate-ci.sh --github   # or --gitlab
```

This writes a workflow that invokes `orchestrator.py --gate-all` on push / PR.
