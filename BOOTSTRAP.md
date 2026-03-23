# Bootstrap Guide

Step-by-step checklist for setting up a new project with this framework.

## Prerequisites
- [ ] Git installed
- [ ] Claude Code or Cursor installed
- [ ] Node.js (for JS/TS projects) or relevant language toolchain

## Option A: Automated setup (recommended)

```bash
./scripts/init-project.sh <project-name> <workspace-path>
```

This creates: submodule, CLAUDE.md, directories, memory files, LESSONS.md, SYNC.md.

## Option B: Manual setup

### Step 1: Create project structure
- [ ] Create project directory
- [ ] Initialize git: `git init`
- [ ] Add framework as submodule: `git submodule add https://github.com/tipyaf/ai-spec-driven-generator.git framework`

### Step 2: Copy framework files
- [ ] Copy `framework/rules/CLAUDE.md.template` to `./CLAUDE.md`
- [ ] Copy `framework/rules/.cursorrules` to `./.cursorrules` (if using Cursor)
- [ ] Create `specs/` directory
- [ ] Create `memory/` directory
- [ ] Copy `framework/memory/memory-template.md` to `memory/<project-name>.md`
- [ ] Copy `framework/memory/LESSONS.md.template` to `memory/LESSONS.md`
- [ ] Create `stacks/` directory

### Step 3: Configure CLAUDE.md
- [ ] Update project name in CLAUDE.md
- [ ] Update framework paths (replace `agents/` with `framework/agents/`)
- [ ] Add project-specific agent instructions (if any)
- [ ] Define epic priority table (if using Shortcut)

### Step 4: Write initial spec
- [ ] Copy `framework/specs/templates/spec-template.yaml` to `specs/<project-name>.yaml`
- [ ] Fill in: name, type, description, target_users, problem_statement
- [ ] Start Phase 0 (Scoping) with the PO agent

### Step 5: Configure hooks (optional)
- [ ] Copy `framework/stacks/hooks/hook-config.json` to project root
- [ ] Customize patterns for your tech stack
- [ ] Generate Claude Code settings from hook config

### Step 6: Verify setup
- [ ] Run `/spec` skill to test PO agent
- [ ] Run `/refine` skill to test refinement
- [ ] Verify CLAUDE.md is picked up by your IDE
- [ ] Verify memory file is readable

## Post-setup checklist
- [ ] First commit with project structure
- [ ] SYNC.md created with framework version
- [ ] Team members onboarded (if applicable)
