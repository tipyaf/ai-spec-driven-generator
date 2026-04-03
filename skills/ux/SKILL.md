---
name: ux
description: Design UX/UI for frontend stories. Produces a UX spec, YAML component definitions, and an HTML prototype. Use when starting UI work or when a story needs visual design before build.
---

## Phase guard — verify before proceeding

**Prerequisites** (check filesystem):
1. `specs/feature-tracker.yaml` must exist
2. At least one feature with UI scope must exist in the tracker
3. Stack profiles from `stacks/` must be readable (for design system constraints)

**If any prerequisite is missing** → Tell user: "Define the project first" → suggest `/spec`

## Setup — Read these files before starting

1. Read `agents/ux-ui.md` (core instructions)
2. Read `specs/feature-tracker.yaml` (current state)
3. Read the relevant story file from `specs/stories/[feature-id].yaml`
4. Read stack profiles from `stacks/` (design system rules, component library, CSS framework)
5. Read `memory/LESSONS.md` (known UX pitfalls)

## Invocation modes

- `/ux` or `/ux all` — run UX design for all frontend stories in pending/refined state
- `/ux [feature-name]` — run UX design for a specific feature
- `/ux [story-ID]` — run UX design for a specific story by its ID (e.g., `/ux 124`)

## Workflow

### Step 1 — Information architecture
1. Read the story ACs to understand what the user sees and does
2. Map out the page/screen structure (sitemap fragment)
3. Identify navigation flows and user journeys
4. Define component hierarchy

### Step 2 — Component design
1. Define each UI component in YAML format:
   - Component name, purpose, props/inputs
   - States (default, loading, error, empty)
   - Responsive behavior (mobile, tablet, desktop)
   - Accessibility requirements (ARIA roles, keyboard navigation)
2. Reference existing design system components where possible
3. Flag new components that need creation

### Step 3 — HTML prototype
1. Create a static HTML prototype demonstrating the layout and interactions
2. Use the project's CSS framework (from stack profile) for styling
3. Include realistic sample data (not lorem ipsum)
4. Prototype must be viewable by opening the HTML file directly in a browser

### Step 4 — User validation
1. Present the design to the user with:
   - Component hierarchy diagram
   - Key interaction flows
   - Accessibility notes
2. Wait for user approval before proceeding
3. Iterate based on feedback

## Output directory

All UX artefacts are written to `_work/ux/`:
- `_work/ux/[feature-id]-spec.md` — UX specification document
- `_work/ux/[feature-id]-components.yaml` — component definitions in YAML
- `_work/ux/[feature-id]-prototype.html` — static HTML prototype

## 3 mandatory artefacts

Every `/ux` invocation MUST produce all three:

| Artefact | Format | Purpose |
|---|---|---|
| **UX spec** | Markdown (`.md`) | Information architecture, flows, design rationale, accessibility notes |
| **Component definitions** | YAML (`.yaml`) | Structured component tree with props, states, responsive rules |
| **HTML prototype** | HTML (`.html`) | Visual, interactive prototype viewable in browser |

If any artefact cannot be produced (e.g., no UI in the story), explain why and skip with justification.

## Artefact checklist (must exist after /ux)
- [ ] `_work/ux/[feature-id]-spec.md` — UX specification
- [ ] `_work/ux/[feature-id]-components.yaml` — component definitions
- [ ] `_work/ux/[feature-id]-prototype.html` — HTML prototype
- [ ] Story file updated with UX references (if applicable)
