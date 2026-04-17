---
name: spec
description: Create or update a project specification. Auto-detects spec.type from project files (package.json, pyproject.toml, Cargo.toml, go.mod, Gemfile); asks for confirmation when ambiguous.
---

# /spec

## Usage
/spec [domain | sc-<id>]

## What it does

Guides the user through scoping, clarification, UX design, feature ordering, and architecture planning, then produces the canonical `specs/` artefacts. The key v5 change: `spec.type` is **inferred from project files** instead of being asked cold.

## Auto-detection of spec.type

Before starting scoping, the skill scans the project root for signals:

| File / pattern found | Candidate spec.type |
|---|---|
| `package.json` with `next`/`react`/`vue`/`svelte` deps | `web-ui` |
| `package.json` with `express`/`fastify`/`koa`/`nestjs` | `web-api` |
| `package.json` with `commander`/`yargs`/`oclif`, bin entry | `cli` |
| `package.json` as library (no bin, has `main`/`exports`) | `library` |
| `pyproject.toml` with `fastapi`/`flask`/`django`/`starlette` | `web-api` |
| `pyproject.toml` with `torch`/`tensorflow`/`scikit-learn` | `ml-pipeline` |
| `pyproject.toml` console_scripts only | `cli` |
| `Cargo.toml` with `[[bin]]` | `cli` |
| `Cargo.toml` as lib crate | `library` |
| `go.mod` with `net/http`, `gin`, `echo` | `web-api` |
| `go.mod` with `cobra`, `urfave/cli` | `cli` |
| `Gemfile` with `rails`, `sinatra` | `web-api` |
| `ios/`, `android/`, `App.tsx` with `react-native` | `mobile` |
| `platformio.ini`, `Kconfig`, `.cargo/config.toml` with embedded target | `embedded` |

Rules:
- **Single clear match** → propose `spec.type: <value>` and ask "confirm? (y/n)".
- **Multiple matches** (e.g. Next.js + Express API in monorepo) → list candidates, ask user to pick.
- **No match** → ask the user to pick from the 7 project types.

The detected type is persisted in `specs/<project>.yaml` as `spec.type`.

## How it works

1. Run auto-detection; confirm `spec.type` with the user.
2. Load appropriate project-type YAML from `stacks/project-types/<type>.yaml` (to know which gates will apply).
3. Walk through phases:
   1. Constitution — non-negotiable principles → `specs/constitution.md`.
   2. Scoping (PO) — requirements gathering → `specs/<project>.yaml`.
   3. Clarify — resolve ambiguities → `specs/<project>-clarifications.md`.
   4. UX (if `type in {web-ui, mobile}`) — design system → `specs/<project>-ux.md`.
   5. Feature ordering — PO + Architect → `specs/<project>-arch.md`.
   6. Architecture plan → `specs/<project>-arch.md` (continued).
   7. Initialize `specs/feature-tracker.yaml`.
4. Present each phase artefact to the user before moving on.

## Arguments

| Arg | Required | Description |
|---|---|---|
| `domain` | No | Regenerate only that domain's markdown (e.g. `/spec backend`). |
| `sc-<id>` | No | Regenerate domains touched by a specific story overlay in `_work/spec/`. |

## Flags

None.

## Exit conditions

- **Success**: all required spec artefacts written and confirmed.
- **Failure**: user aborts during validation; no partial state.

## Files read / written

- Reads: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Gemfile` (auto-detection); `stacks/project-types/*.yaml`; `_work/spec/*.yaml` (overlays).
- Writes: `specs/constitution.md`, `specs/<project>.yaml`, `specs/<project>-clarifications.md`, `specs/<project>-ux.md` (if UI), `specs/<project>-arch.md`, `specs/feature-tracker.yaml`.

## Related

- `/refine` — consumes the spec.
- `/ux` — design wireframes for UI project types.
