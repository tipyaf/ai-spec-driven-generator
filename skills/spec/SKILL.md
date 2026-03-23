---
name: spec
description: Create or update a project specification. Guides the user through scoping with the Product Owner, then designs UX, then plans architecture. Use when starting a new project or defining a new feature.
---

## Setup — Read the agent needed for the current step

- **Phase 0 (Scoping)**: Read `agents/product-owner.md`
- **Phase 0.5 (Design)**: Read `agents/ux-ui.md`
- **Phase 1 (Plan)**: Read `agents/architect.md`

Read ONE agent at a time — load the next only when the current phase is validated.
Only read `.ref.md` files when you need a specific template.

## Workflow

1. **PO phase**: Gather requirements (one question at a time), challenge assumptions, write YAML spec
   → Present to user → wait for validation
2. **UX/UI phase** (if UI project): Design information architecture, flows, design system, components
   → Present to user → wait for validation
3. **Architect phase**: Select stack (present options), plan architecture, create implementation manifest
   → Present to user → wait for validation
4. Complete spec saved to `specs/[project-name].yaml`
