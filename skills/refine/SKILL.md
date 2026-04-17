---
name: refine
description: Break a pending feature into implementable stories with structured ACs (AC-FUNC / AC-SEC / AC-BP) each carrying a verify: command. Injects stack-specific security and best-practice ACs from the active stack templates.
---

# /refine

## Usage
/refine [feature-name]

## What it does

Transforms a `pending` feature from `specs/feature-tracker.yaml` into one or more atomic stories with:
- Functional ACs (`AC-FUNC-*`) hand-written from user requirements.
- Security ACs (`AC-SEC-*`) auto-injected from `stacks/templates/<stack>/ac-templates.yaml`.
- Best-practice ACs (`AC-BP-*`) auto-injected from the same templates.
- Every AC has a `verify:` command (Tier 1 preferred, Tier 3 forbidden).
- A manifest file listing `scope.files`, `epic`, dependencies used by the `/build` auto-dispatcher.

For UI scope, the wireframe gate runs to produce HTML prototypes with `data-testid`, `data-action`, `data-state`, and `data-role` attributes required by G9.x gates.

## How it works

1. Load `agents/refinement.md` and `agents/product-owner.md`.
2. Read the feature from `specs/[project].yaml` and stack templates from `stacks/templates/<stack>/ac-templates.yaml`.
3. Decompose into atomic stories; each fits a single session.
4. Write ACs in the Given/When/Then format with testability tier classification.
5. Inject stack-specific AC-SEC-* and AC-BP-* from the templates (matched by `story.type`).
6. For UI stories: dispatch `agents/ux-ui.md` via `/ux` to produce wireframes; enforce the four required `data-*` attributes.
7. Produce `specs/stories/<id>.yaml` (contract) + `specs/stories/<id>-manifest.yaml` (scope & epic).
8. Update `specs/feature-tracker.yaml` status to `refined`.

## Arguments

| Arg | Required | Description |
|---|---|---|
| `feature-name` | No | Target feature from the tracker. Omit to pick the next `pending` one. |

## Flags

None.

## Exit conditions

- **Success**: story + manifest written; tracker updated. Next: `/build <id>`.
- **Failure**: spec ambiguous or missing. Run `/spec` first.
- **Escalation**: wireframe iteration exhausted (UI only). User must validate wireframes manually.

## Files read / written

- Reads: `specs/[project].yaml`, `specs/feature-tracker.yaml`, `stacks/templates/<stack>/ac-templates.yaml`, `memory/LESSONS.md`, `agents/refinement.md`, `agents/product-owner.md`, `agents/ux-ui.md` (UI only).
- Writes: `specs/stories/<id>.yaml`, `specs/stories/<id>-manifest.yaml`, `specs/feature-tracker.yaml`, `_work/ux/wireframes/<id>/` (UI only).

## Wireframe attributes (UI only)

Every interactive element MUST carry:
- `data-testid` — E2E selector.
- `data-action` — intent tag (e.g. `submit-login`), consumed by G9.4 interaction tests.
- `data-state` — visual state (`default`/`loading`/`error`/`disabled`), consumed by G9.3 visual regression.
- `data-role` — semantic role (`primary`/`secondary`/`destructive`), consumed by G9.5 accessibility.

## Related

- `/spec` — create or update the project spec this skill consumes.
- `/ux` — design wireframes (called automatically for UI stories, can be run standalone).
- `/build` — consume the refined story.
