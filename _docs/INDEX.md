# AI Spec-Driven Generator — v5

**Version 5.0** — [Changelog](../CHANGELOG.md)

> Reusable AI agent framework for spec-driven code generation. 18 agents,
> 20 enforcement scripts, adaptive gates G1–G14, 4 stack plugins built-in.

Start here:
- [README.md](../README.md) — pitch + quick start
- [PIPELINE.md](PIPELINE.md) — the whole pipeline in one doc (commands, gates, agents, scripts, state machine)
- [../rules/GUIDE.md](../rules/GUIDE.md) — full rules reference
- [../rules/CHEATSHEET.md](../rules/CHEATSHEET.md) — 1-page TL;DR

---

## Skills (13 commands)

| Skill | Description |
|---|---|
| `/spec` | Define project (constitution, scope, UX, architecture) |
| `/refine` | Break feature into stories with `verify:` + oracle values |
| `/build` | Orchestrator: auto-dispatch builder, TDD RED→GREEN + gates |
| `/validate` | Read-only rerun of gates |
| `/review` | Read-only audit — PASS/FAIL |
| `/ship` | Single exit — runs `/review` + pushes + creates PR with `sdd-validated-v5` tag |
| `/ux` | UX design (wireframes, DS tokens) |
| `/scan` | SonarQube / semgrep / eslint scan |
| `/next` | Prioritised action list |
| `/status` | Dashboard view |
| `/help` | Contextual help |
| `/resume` | Unlock escalated/tampered story |
| `/migrate` | Run migration scripts |

---

## Agents (18)

`/spec` · `product-owner`, `ux-ui`, `architect`
`/refine` · `refinement`
`/build` · builders (`builder-service`, `builder-frontend`, `builder-infra`, `builder-migration`, `builder-exchange`) + `test-author` (modes `red`/`green`) + `observability-engineer` + `performance-engineer`
`/validate` · `validator`, `security`
`/review` · `code-reviewer` (modes `story`/`code`)
`/ship` · `release-manager`
`/build` (if migration) · `data-migration-engineer`
Ops · `devops`

Full catalog with roles/models/loaders: [PIPELINE.md §4](PIPELINE.md).

---

## Enforcement scripts (20)

6 refactored AST (v5) · 4 retained · 10 new. Full list: [PIPELINE.md §5](PIPELINE.md).

---

## Documentation

| Document | What it covers |
|----------|----------------|
| [PIPELINE.md](PIPELINE.md) | Whole pipeline — commands, 18 agents, 20 scripts, G1–G14, stack plugins, state machine |
| [../rules/GUIDE.md](../rules/GUIDE.md) | Rules reference (principles, coding standards, test quality, agent conduct, commits, git flow) |
| [../rules/CHEATSHEET.md](../rules/CHEATSHEET.md) | 1-page TL;DR |
| [../stacks/CUSTOM_STACK_GUIDE.md](../stacks/CUSTOM_STACK_GUIDE.md) | Author a custom stack plugin |
| [sonarqube.md](sonarqube.md) | SonarQube setup |
| [test-methodology.md](test-methodology.md) | Two-loop test methodology |
| [token-costs.md](token-costs.md) | Token costs per agent / skill |

---

## Templates

| Template | Purpose |
|----------|---------|
| [spec-template.yaml](../specs/templates/spec-template.yaml) | YAML spec template |
| [feature-tracker.yaml](../specs/templates/feature-tracker.yaml) | Per-feature state tracking |
| [story-template.yaml](../specs/templates/story-template.yaml) | Story file (build contract) |
| [manifest-template.yaml](../specs/templates/manifest-template.yaml) | Implementation manifest |
| [build-template.yaml](../specs/templates/build-template.yaml) | Pipeline state per story |
| [stack-profile-template.md](../stacks/stack-profile-template.md) | Stack profile template |

---

## Memory Templates

| Template | Copy to |
|----------|---------|
| [LESSONS.md.template](../memory/LESSONS.md.template) | memory/LESSONS.md |
| [SYNC.md.template](../memory/SYNC.md.template) | memory/SYNC.md |
| [memory-template.md](../memory/memory-template.md) | memory/<project-name>.md |
