---
name: ux
description: Design UX/UI for frontend stories. Produces a UX spec, YAML component definitions, and self-contained HTML wireframes that MUST carry data-testid, data-action, data-state, and data-role attributes on every interactive element (required by G9.x gates).
---

# /ux

## Usage
/ux [all | feature-name | story-id]

## What it does

Produces the three mandatory UX artefacts (spec, components, HTML prototype) for a UI story. In v5 the HTML wireframes become a machine-readable contract: every interactive element must expose four `data-*` attributes consumed downstream by G9.1–G9.6 gates.

## Required attributes on every interactive element

| Attribute | Used by | Example |
|---|---|---|
| `data-testid` | G9.2 wireframe conformity, E2E selectors | `data-testid="login-form-email"` |
| `data-action` | G9.4 interaction verification | `data-action="submit-login"` |
| `data-state` | G9.3 visual regression per state | `data-state="default\|loading\|error\|disabled"` |
| `data-role` | G9.5 accessibility (role + contrast) | `data-role="primary\|secondary\|destructive"` |

A wireframe missing any one of these on an interactive element is rejected — the skill loops with the UX agent until conformity. This contract is what lets the orchestrator auto-generate Playwright interaction tests.

## How it works

1. Load `agents/ux-ui.md` and the story file.
2. Build information architecture, component hierarchy, and flows.
3. Write component definitions in YAML (each component with states, props, accessibility notes).
4. Render the HTML prototype using the project's design system tokens:
   - Inline CSS with `--ds-*` custom properties referencing `specs/design-system.yaml`.
   - Include all states (empty, loading, error, success).
   - Include 3 viewports: 375px / 768px / 1440px.
   - Add the four required `data-*` attributes to every interactive element.
5. Run WCAG pre-check (axe-core if configured, manual checklist otherwise).
6. Present to the user for approval; iterate on feedback.
7. Persist to `_work/ux/wireframes/<story-id>/` and update `specs/<project>-ux.md`.

## Arguments

| Arg | Required | Description |
|---|---|---|
| `all` | No | Design every pending UI story. Default when no arg passed. |
| `feature-name` | No | Design all UI stories under the named feature. |
| `story-id` | No | Design a single story (e.g. `/ux sc-0014`). |

## Flags

None.

## Exit conditions

- **Success**: all three artefacts produced, wireframes pass the attribute contract and WCAG pre-check.
- **Failure**: missing design-system file, story has no UI scope.
- **Escalation**: user rejects wireframes after 3 iterations — user must validate manually.

## Files read / written

- Reads: `agents/ux-ui.md`, `specs/stories/<id>.yaml`, `specs/design-system.yaml`, `stacks/templates/<stack>/profile.yaml`.
- Writes: `_work/ux/wireframes/<story-id>/*.html`, `_work/ux/<story-id>-spec.md`, `_work/ux/<story-id>-components.yaml`, `specs/<project>-ux.md`.

## Related

- `/refine` — calls `/ux` automatically for UI stories.
- `/build` — consumes the wireframes for G9.2 / G9.4 test generation.
