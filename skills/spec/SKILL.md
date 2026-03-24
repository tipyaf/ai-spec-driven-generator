---
name: spec
description: Create or update a project specification. Guides the user through scoping with the Product Owner, then clarifies ambiguities, designs UX, then plans architecture. Use when starting a new project or defining a new feature.
---

## Phase guard

No prerequisites — `/spec` is the starting point.

## Setup — Read the agent needed for the current step

- **Phase 0 (Constitution)**: Define non-negotiable project principles
- **Phase 0.1 (Scoping)**: Read `agents/product-owner.md`
- **Phase 0.2 (Clarify)**: Resolve ambiguities in the spec before planning
- **Phase 0.3 (Design)**: Read `agents/ux-ui.md`
- **Phase 0.5 (Ordering)**: Read `agents/product-owner.md` + `agents/architect.md`
- **Phase 1 (Plan)**: Read `agents/architect.md`

Read ONE agent at a time — load the next only when the current phase is validated.
Only read `.ref.md` files when you need a specific template.

## Workflow

### Step 1 — Constitution
Define non-negotiable project principles (quality standards, testing requirements, architectural constraints).
→ Write to `specs/constitution.md`
→ Present to user → wait for validation

### Step 2 — Scoping (PO)
Gather requirements (one question at a time), challenge assumptions, write YAML spec.
→ Write to `specs/[project-name].yaml`
→ Present to user → wait for validation

### Step 3 — Clarify ambiguities
Review the spec for ambiguities, contradictions, or missing information.
Ask the user targeted questions to resolve each one. Document resolutions.
→ Write to `specs/[project-name]-clarifications.md` (even if empty = "no ambiguities found")
→ Present to user → wait for validation

### Step 4 — Design (if UI project)
Check `spec.type` — skip this step for: api, cli, library, embedded, data-pipeline.
Design information architecture, flows, design system, components.
→ Write to `specs/[project-name]-ux.md`
→ Present to user → wait for validation

### Step 5 — Feature ordering
Collaborate between PO (business value) and Architect (technical dependencies) to order features into epics.
Each epic must deliver testable user value.
→ Order features in the spec YAML or in `specs/[project-name]-arch.md`
→ Present to user → wait for validation

### Step 6 — Architecture plan
Select stack (present options with trade-offs), plan architecture, create implementation manifest.
→ Write to `specs/[project-name]-arch.md`
→ Present to user → wait for validation

### Step 7 — Initialize tracking
Create the feature tracker from `specs/templates/feature-tracker.yaml`.
Populate with all features from the spec (status: pending).
→ Write to `specs/feature-tracker.yaml`

### Artefact checklist (all must exist before /spec is "done")
- [ ] `specs/constitution.md`
- [ ] `specs/[project-name].yaml`
- [ ] `specs/[project-name]-clarifications.md`
- [ ] `specs/[project-name]-ux.md` (or skipped for non-UI)
- [ ] `specs/[project-name]-arch.md`
- [ ] `specs/feature-tracker.yaml`
