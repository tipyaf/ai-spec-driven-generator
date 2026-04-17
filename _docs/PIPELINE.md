[< Back to Index](INDEX.md)

# PIPELINE.md — The v5 Framework in One Document

Unified reference for the whole pipeline: commands, gates, agents, scripts, stack
plugins, escalation and state machine. Replaces the v4 set (`agents.md`,
`process.md`, `workflow.md`, `skills.md`).

Honest framing: v5 ships **3 project-type implementations** (`web-ui`, `web-api`,
`cli`) out of the 7 declared (`library`, `ml-pipeline`, `mobile`, `embedded` to
land in v5.x). The pipeline here describes what v5.0 actually executes.

---

## 1. Overview

```
/spec  →  /refine  →  /build  →  /validate  →  /review  →  /ship  →  PR
                 (per feature loop)                       (single exit)
```

| Command | What it does | Exit |
|---|---|---|
| `/spec` | Define the project: constitution, scope, UX, architecture. | Artifacts on disk |
| `/refine <feature>` | Break a feature into stories + `verify:` + oracle values. | `refined` |
| `/build <story-id>` | Orchestrator: auto-dispatch builder, RED→GREEN, run gates. | `validated` or `escalated` |
| `/validate <story-id>` | Read-only rerun of gates on current repo. | PASS/FAIL |
| `/review [story-id\|--all]` | Read-only audit — ceinture + bretelles before ship. | PASS/FAIL |
| `/ship <story-id>` | Invokes `/review` then pushes + opens PR with `sdd-validated-v5` tag. | PR URL or FAIL |
| `/scan [--full]` | SonarQube / semgrep / eslint scan. | Report |
| `/next` | Prioritised action list (BLOCKING / IN-PROGRESS / READY / PENDING SHIP / SUGGESTIONS). | Report |
| `/status [story-id]` | Dashboard view of the project. | Report |
| `/help [command]` | Contextual help. | Text |
| `/resume <story-id> "reason"` | Unlock an escalated/tampered story. | State cleared |
| `/migrate [--to VERSION]` | Run migration scripts (v3→v4, v4→v5). | Report |

**Contract (1 phrase)**: until `/ship` emits `PR CREATED` with the `sdd-validated-v5`
tag, the code has not earned the right to leave the dev's machine.

---

## 2. Project types

Seven types are declared in `stacks/project-types/*.yaml`. Only three are
implemented in v5.0:

| Type | Status in v5.0 | Example |
|---|---|---|
| `web-ui` | ✅ implemented | React / Vue / Svelte / Angular |
| `web-api` | ✅ implemented | FastAPI, Gin, NestJS |
| `cli` | ✅ implemented | click, typer, cobra, clap |
| `library` | ⏳ v5.x | reusable packages / SDKs |
| `ml-pipeline` | ⏳ v5.x | training + inference pipelines |
| `mobile` | ⏳ v5.x | iOS / Android / React Native |
| `embedded` | ⏳ v5.x | firmware, QEMU-booted |

`spec.type` is auto-detected by `/spec` from project markers (`package.json`,
`pyproject.toml`, `Cargo.toml`, `go.mod`, `src/App.tsx`, …). Ambiguity → the user
confirms.

The orchestrator reads `stacks/project-types/<type>.yaml` and runs only the gates
declared there. Gates that do not apply are **absent from the log** (not marked
`skipped`).

---

## 3. Gates G1–G14

Core gates run for every project type. Conditional gates are activated by
`spec.type`, story content, or invocation context.

| Gate | Name | Applies to | Blocks on |
|---|---|---|---|
| **G1** | Security | All | OWASP patterns, AC-SEC-* fail, dep vulns |
| **G2** | Unit tests (3 runs, 0 flakiness) | All | test fail, coverage < threshold |
| **G2.1** | Mutation testing (changed files) | All | mutation score < 80% |
| **G2.2** | Regression suite (prior stories) | All | prior story test fail |
| **G2.3** | Contract diff (API / public AST / DB / CLI surface) | All | breaking change undeclared |
| **G3** | Code quality (tool mandatory) | All | tool violation or no tool configured |
| **G4** | Build final (artifact) | All | build error / type error |
| **G4.1** | Smoke boot | All | app fails to start / respond |
| **G5** | AC validation (Tier 1 mechanical) | All | `verify:` command fails |
| **G6** | Story review (AC Tier 2/3 ↔ diff) | All | AC not implemented |
| **G7** | Code review (scope, SOLID, 0 console errors) | All | scope violation, SOLID, stacktrace |
| **G8** | Integration cross-stories | If touches validated module | contract break inter-module |
| **G9.1** | Design System conformity | web-ui, mobile | hardcoded token, unauthorized component |
| **G9.2** | Wireframe structural conformity (`data-testid`) | web-ui, mobile | `data-testid` missing, hierarchy mismatch |
| **G9.3** | Visual regression (3 viewports) | web-ui, mobile | pixel diff > threshold |
| **G9.4** | Interaction verification (from `interactions:`) | web-ui, mobile | expected DOM/URL/API/state ≠ actual |
| **G9.5** | Accessibility (axe + keyboard + contrast) | web-ui, mobile | axe AA violation, keyboard trap |
| **G9.6** | Behavioral regression (rejoue prior `interactions:`) | web-ui, mobile | prior interaction fails |
| **G10** | Performance (budget + baseline delta) | All (opt-in for library) | regression > 5% vs baseline |
| **G11** | Observability (logs/metrics/traces ratios) | web-api, web-ui, ml-pipeline | ratio below minimum |
| **G12** | Runtime security / DAST-lite | web-api, web-ui | DAST high severity |
| **G13** | Migration safety | If migration present | rollback fail, data loss |
| **G14** | Release readiness | At `/ship` | CHANGELOG / VERSION / tags incoherent |

**Disappeared vs v4**: v4 Gate 3 "reviewer 3-pass fallback" is gone — G3 requires
a real tool. v4 Gate 9/10 had overlapping scope — split as G6 (semantic AC↔code)
and G7 (quality/scope).

---

## 4. Agents (18)

Agent files live in `agents/<name>.md`. Each agent runs with the model declared
in its frontmatter. Skills load only what they need — never load all agents at
once.

### Orchestration & conception

| Agent | Role | Model | Loaded by |
|---|---|---|---|
| `product-owner` | Scoping, spec YAML, constitution | Opus | `/spec` |
| `ux-ui` | IA, flows, wireframes, DS tokens (web-ui/mobile) | Sonnet | `/spec`, `/ux` |
| `architect` | Tech choices, manifest, component inventory | Opus | `/spec` |

### Refinement

| Agent | Role | Model | Loaded by |
|---|---|---|---|
| `refinement` | Story breakdown, `verify:` commands, oracle pre-compute, `interactions:` | Opus | `/refine` |

### Build (5 specialist builders)

| Agent | Role | Model | Loaded by |
|---|---|---|---|
| `builder-service` | Backend services (routers, services, repos, tests) | Sonnet | `/build` |
| `builder-frontend` | Frontend (pages, components, hooks, API client) | Sonnet | `/build` |
| `builder-infra` | Docker, CI/CD, nginx, deployment config | Sonnet | `/build` |
| `builder-migration` | Schema migrations + roundtrip tests | Sonnet | `/build` |
| `builder-exchange` | Exchange/trading adapters (safety-critical) | Opus | `/build` |

### Quality & testing

| Agent | Role | Model | Loaded by |
|---|---|---|---|
| `test-author` (modes `red` / `green`) | TDD writer: fails tests in RED, no tamper in GREEN. Replaces v4 `tester` + `test-engineer`. | Opus | `/build` |
| `validator` | Independent AC runner (Tier 1 only) | Sonnet | `/validate` |
| `code-reviewer` (scopes `story` / `code`) | G6 semantic AC↔code + G7 quality/scope. Replaces v4 `reviewer` + `story-reviewer`. | Opus | `/validate`, `/review` |
| `security` | OWASP + static + dep audit; CRITICAL/HIGH blocks | Sonnet/Opus | `/build`, `/validate` |

### Operations (new in v5)

| Agent | Role | Model | Loaded by |
|---|---|---|---|
| `observability-engineer` | Structured logs, metrics, traces, alerting contract | Sonnet | `/build` (G11) |
| `performance-engineer` | Perf budgets, baseline, N+1 detection, profiling | Sonnet | `/build` (G10) |
| `data-migration-engineer` | Data transformations distinct from schema migrations | Opus | `/build` (G13) |
| `release-manager` | Version bump, CHANGELOG, tags, release notes, `gh pr create` | Sonnet | `/ship` (G14) |

### Devops

| Agent | Role | Model | Loaded by |
|---|---|---|---|
| `devops` | CI/CD pipeline, env config | Sonnet | `/spec`, optional |

**Deleted vs v4**: `developer` (duplicate of the 5 builders), `orchestrator` (now
`scripts/orchestrator.py`), `spec-generator` (YAML is the source of truth).

---

## 5. Enforcement scripts (20)

All live in `scripts/`. The orchestrator runs each at the right gate; git hooks
are feedback-only (installed via `scripts/setup-hooks.sh`). **Every `--no-verify`
is detected at the next orchestrator pass.**

### Refactored in v5 (6 — now AST-based instead of regex)

| Script | Gate | What it detects |
|---|---|---|
| `check_red_phase.py` | RED | Trivial failures (`assert False`), no real production import |
| `check_test_tampering.py` | GREEN | AST diff — any assertion removed between RED and GREEN |
| `check_coverage_audit.py` | RED | Routes/tables/components without tests (AST, handles f-strings + dynamic routes) |
| `check_oracle_assertions.py` | G1, pre-commit | Parses `# ORACLE: expr = value` and evaluates in sandbox |
| `check_msw_contracts.py` | RED (frontend) | Pydantic heritage-chain resolved; MSW vs backend field names |
| `check_test_intentions.py` | RED | Embedding similarity (fallback regex) between `test_intentions:` and test names |

### Retained from v4 (4)

| Script | Gate | What it detects |
|---|---|---|
| `check_tdd_order.py` | GREEN | Code commit without preceding RED commit |
| `check_story_commits.py` | GREEN | Production code staged without story/manifest/tracker |
| `check_test_quality.py` | pre-commit | `.skip()`, mock-soup, fixture-only, weak assertions (Rule 2b) |
| `check_write_coverage.py` | pre-commit (legacy in stack plugins) | Tables with readers but no tested writer |

### New in v5 (10)

| Script | Gate | What it detects |
|---|---|---|
| `check_integration_coverage.py` | G8 | Story touches a validated module without a cross-story test |
| `check_performance_budget.py` | G10 | Metric > budget or > 5% vs baseline |
| `check_observability.py` | G11 | logs/metrics/traces ratio below minimum per LOC added |
| `check_release_artifacts.py` | G14 | CHANGELOG/VERSION/tags incoherent |
| `check_migration_safety.py` | G13 | Schema rollback fails, data migration not idempotent |
| `check_ds_conformity.py` | G9.1 | Hardcoded colors/spacing, component outside DS |
| `check_contract_diff.py` | G2.3 | OpenAPI / public AST / DB schema / CLI surface breaking diff |
| `generate-interaction-tests.py` | G9.2 + G9.4 | Generates Playwright tests from wireframe HTML + `interactions:` |
| `check_visual_regression.py` | G9.3 | pixelmatch diff per viewport / color scheme |
| `check_behavioral_regression.py` | G9.6 | Rejoue `interactions:` of prior validated stories |

---

## 6. Stack plugins

The framework core stays agnostic (Python scripts). **Stack-awareness lives in
the project**, not in the framework:

```
<project>/_work/stacks/
├── registry.yaml                     # active stacks for this project
├── python-fastapi/
│   ├── profile.yaml                  # test/build/smoke commands, forbidden patterns
│   ├── ac-templates.yaml             # AC-SEC-* / AC-BP-* auto-injected by /refine
│   └── checks/                       # stack-specific Python checks
├── typescript-react/
├── postgres/
├── nodejs-express/
└── <custom-stack>/                   # community / project-specific
```

v5 ships **4 built-in stacks**: `python-fastapi`, `typescript-react`, `postgres`,
`nodejs-express` (stored in `stacks/templates/`). Projects copy what they use
into `_work/stacks/`.

Full reference: [`../stacks/CUSTOM_STACK_GUIDE.md`](../stacks/CUSTOM_STACK_GUIDE.md).

---

## 7. Pre-PR assurance chain (9 links)

Every `/ship` re-runs this chain from the current repo content — independently of
commits, hooks, or prior gate verdicts.

1. **Unit tests pass on current code** (G2, 3 consecutive runs, 0 flakiness)
2. **Tests actually test** (G2.1 — mutation score ≥ 80% on changed files)
3. **Code compiles and types** (G4)
4. **The app actually starts** (G4.1 — smoke boot per stack)
5. **Previously validated features still work** (G2.2 — full regression)
6. **Cross-module contracts hold** (G8 when applicable)
7. **ACs are satisfied** (G5 mechanical + G6 semantic)
8. **Code is clean, safe, observable, performant** (G1, G3, G7, G10, G11, G12)
9. **The PR itself is ready** — `/ship` runs `/review` internally; only on PASS
   does it push + `gh pr create` via `release-manager` with the
   `sdd-validated-v5` tag.

If any link fails, `/ship` refuses to create the PR and returns a detailed
report. The dev never runs `gh pr create` directly — a manually-created PR lacks
the `sdd-validated-v5` tag and is caught at human review.

---

## 8. Multi-layer anti-regression (R1–R6)

Regressions happen at six different levels. Each has a dedicated gate.

| Level | What regresses | Gate | Evidence |
|---|---|---|---|
| **R1** | Existing tests break | G2.2 | Test registry per story, 3 runs |
| **R2** | Public contract (API / lib / DB / CLI) | G2.3 | OpenAPI snapshot / AST diff / schema diff |
| **R3** | Visual appearance | G9.3 | Pixelmatch vs baseline, 3 viewports |
| **R4** | User-facing behaviour | G9.6 | Rejoue `interactions:` of prior stories |
| **R5** | Performance | G10 | Metric vs baseline, >5% = fail |
| **R6** | Data (migration) | G13 | Seed + rollback + re-run reads |

---

## 9. Escalation & `/resume`

**Escalation contract**: after 3 failed validation cycles, the orchestrator
writes `status: escalated` to `specs/feature-tracker.yaml` and refuses to run
`/build` or `/validate` on that story. The lock is only cleared by `/resume`:

```
/resume sc-0012 "reset to refined — architecture needs rethinking"
```

The reason is **mandatory**. Without it the skill refuses. The reason lands in
the story's history and `memory/LESSONS.md` if the same pattern repeats across
2+ stories.

**Tamper detection**: if the orchestrator detects a `--no-verify` bypass,
weakened assertion, or code commit without a story association (AST diff between
commits, not between staged/HEAD), the story is moved to `status: tampered`
which also requires `/resume`.

**Exit codes** (orchestrator):

| Code | Meaning |
|---|---|
| 0 | All gates pass |
| 1 | One or more gates failed (normal fail) |
| 2 | `status: escalated` — max cycles reached, `/resume` required |
| 3 | Config error (missing `project-type`, unknown stack, …) |
| 4 | `status: tampered` — bypass detected, `/resume` required |

---

## 10. Feature tracker state machine

`specs/feature-tracker.yaml` holds the state of every feature. The filesystem
and the state machine are the single source of truth — not conversation memory.

```
pending ── /refine ──▶ refined ── /build ──▶ building ── /validate pass ──▶ validated ── /ship ──▶ shipped
                                      │                        │
                                      └── /validate fail ──────┘
                                                 (cycles++, max 3)
                                                    │
                                                    ▼
                                              escalated  ◀── tampered
                                                    │
                                                  /resume
                                                    │
                                                    ▼
                                              (back to refined/building)
```

| State | Meaning | Set by |
|---|---|---|
| `pending` | Declared in spec, not refined | `/spec` |
| `refined` | Story file + manifest + oracle values written | `/refine` |
| `building` | `/build` running or cycling | `/build` |
| `validated` | All applicable gates passed | `/build` on PASS |
| `shipped` | PR created with `sdd-validated-v5` tag | `/ship` |
| `escalated` | Max cycles, requires `/resume` | `/build` (terminal until resume) |
| `tampered` | Bypass detected, requires `/resume` | Any gate running tamper detection |

`escalated` and `tampered` are **terminal states** until explicit `/resume`.
Nothing the agent can do unblocks them without user intervention.

---

## 11. Artefacts on disk (the filesystem IS the contract)

| Path | Owner | Purpose |
|---|---|---|
| `specs/constitution.md` | `/spec` | Non-negotiable principles |
| `specs/<project>.yaml` | `/spec` | Product YAML spec |
| `specs/<project>-arch.md` | `/spec` | Architecture plan |
| `specs/design-system.yaml` | `/spec` (UI) | DS tokens & authorized components |
| `specs/feature-tracker.yaml` | all | Per-feature state machine |
| `specs/stories/<id>.yaml` | `/refine` | Build contract with ACs + `interactions:` + `test_intentions:` |
| `specs/stories/<id>-manifest.yaml` | `/refine` + `/build` | Scope: files to create/modify |
| `_work/build/<id>.yaml` | orchestrator | Per-story gate state |
| `_work/build/test-registry.yaml` | orchestrator | Tests per story (G2.2) |
| `_work/contracts/<id>/` | orchestrator | API/AST/DB/CLI snapshots (G2.3) |
| `_work/visual-baseline/<id>/` | G9.3 | Pixel baselines per viewport |
| `_work/perf-baseline/<id>.json` | G10 | Perf metrics baseline |
| `_work/data-fixtures/<id>/` | G13 | Seed data for migrations |
| `_work/ux/wireframes/` | `/ux` | HTML wireframes with `data-testid` |
| `_work/stacks/` | project | Active stacks (registry + profiles) |
| `memory/LESSONS.md` | all | Recurring failures, auto-appended |

---

## 12. Which skill loads which agents

| Skill | Primary agents | Auto gates |
|---|---|---|
| `/spec` | `product-owner`, `ux-ui`, `architect` | — |
| `/ux` | `ux-ui` | — |
| `/refine` | `refinement` | — |
| `/build` | `test-author` (RED), one of 5 builders (GREEN), `observability-engineer`, `performance-engineer` | G1–G14 applicable |
| `/validate` | `validator`, `code-reviewer` (story), `security` | G1, G5, G6 |
| `/review` | `code-reviewer` (code + story) | All applicable gates |
| `/ship` | `release-manager` + internal `/review` | G14 + applicable |
| `/scan`, `/next`, `/status`, `/help`, `/resume`, `/migrate` | — (scripts) | — |

---

## See also

- [`../rules/GUIDE.md`](../rules/GUIDE.md) — rules reference (principles, coding standards, test quality, agent conduct, commits, git flow)
- [`../rules/CHEATSHEET.md`](../rules/CHEATSHEET.md) — 1-page TL;DR
- [`sonarqube.md`](sonarqube.md) — SonarQube setup
- [`test-methodology.md`](test-methodology.md) — two-loop test approach
- [`token-costs.md`](token-costs.md) — token cost per agent and per skill
- [`../stacks/CUSTOM_STACK_GUIDE.md`](../stacks/CUSTOM_STACK_GUIDE.md) — add a custom stack plugin
