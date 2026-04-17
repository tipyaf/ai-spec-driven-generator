# ai-spec-driven-generator — v5

An AI framework that generates production-ready code from structured YAML
specs. **18 specialised agents, 20 enforcement scripts, adaptive gates G1–G14,
4 stack plugins built-in** (and custom stacks via plugin system). Works with
**Claude Code** and **Cursor**.

v5 ships **3 project-type implementations** (`web-ui`, `web-api`, `cli`) out of
the 7 declared (`library`, `ml-pipeline`, `mobile`, `embedded` land in v5.x).
The framework core stays Python + YAML; stack-awareness lives in the project.

## How it works

```
/spec    Human defines the product (constitution, scope, UX, architecture)
    ↓
/refine  Break each feature into stories with verify: + test_intentions
         (+ wireframes with data-testid for web-ui/mobile)
    ↓
/build   Orchestrator auto-dispatches the builder, runs TDD RED → GREEN,
         then every applicable gate (adaptive per spec.type):

            Core gates (all types)
              G1    Security (OWASP + AC-SEC + deps)
              G2    Unit tests (3 runs, 0 flakiness)
              G2.1  Mutation testing ≥ 80% on changed files
              G2.2  Regression suite (all prior stories)
              G2.3  Contract diff (API / AST / DB / CLI)
              G3    Code quality (tool mandatory)
              G4    Build final (artefact)
              G4.1  Smoke boot (app actually starts)
              G5    AC validation (Tier 1 mechanical)
              G6    Story review (AC Tier 2/3 ↔ diff)
              G7    Code review (scope, SOLID, 0 console errors)
              G8    Integration cross-stories (if touches validated module)

            Conditional gates (per spec.type)
              G9.1–G9.6  web-ui / mobile  — DS, wireframe, visual,
                                           interaction, a11y, behavioural
              G10        All (opt-in lib) — perf budget + baseline
              G11        web-api / web-ui / ml-pipeline — observability
              G12        web-api / web-ui — DAST-lite
              G13        If migration — rollback + data preserved
              G14        At /ship — release readiness

         → ALL PASS: status = validated
         → FAIL: cycle ≤ 3, then status = escalated (requires /resume)
    ↓
/ship    Single exit: runs /review on the full branch; on PASS
         push + gh pr create with tag `sdd-validated-v5`.
```

## Principles

| Principle | Rule |
|-----------|------|
| **Agnostic** | Core stays Python + YAML. Projects extend with stack plugins (`_work/stacks/`). 4 stacks built-in (`python-fastapi`, `typescript-react`, `postgres`, `nodejs-express`); community-extensible via `stacks/CUSTOM_STACK_GUIDE.md`. Honest framing: agnostic where it counts, opinionated where it must be. |
| **Autonomous** | Humans decide (product, UX, architecture, deploy). Machines verify. Escalation after 3 cycles is **blocking** — only `/resume <story-id> "reason"` unblocks. Bypass detection via AST diff between commits. |
| **Accompaniment** | `/help [command]`, `/status`, `/next`, `/resume` keep the user informed. Unified messages via `scripts/ui_messages.py`. Never leaves the user without a next step. Responds in the user's language. |

## Quick start

### 1. Create a project

```bash
git clone https://github.com/tipyaf/ai-spec-driven-generator.git
cd ai-spec-driven-generator
./scripts/init-project.sh my-project /path/to/workspace
```

Creates: git submodule, `CLAUDE.md` (from v5 template), `_work/` directories,
skills symlinks, hook config.

### 2. Open in Claude Code or Cursor

The AI reads `CLAUDE.md` and follows the workflow automatically.

### 3. Build

```
/next                        # Tape ça en arrivant le matin — le framework te dit quoi faire
/spec                        # Define your project
/refine candidate-profile    # Break a feature into stories
/build sc-0012               # TDD RED → GREEN + gates (single auto-dispatched /build)
/ship sc-0012                # Run /review on the branch; on PASS push + open PR
```

Additional skills:

```
/ux candidate-profile          # UX design (IA, flows, wireframes, DS tokens)
/validate sc-0012              # Audit-only rerun of gates (read-only)
/review [story-id|--all]       # Read-only audit — no PR, just verdict
/scan [--full] [--report]      # SonarQube / semgrep / eslint scan
/status [story-id]             # Dashboard view
/help [command]                # Contextual help
/resume sc-0012 "reason..."    # Unlock an escalated/tampered story
/migrate [--to VERSION]        # Run migration scripts (v4 → v5)
```

**Framework works without CI/CD.** For a tiers-belt: `scripts/generate-ci.sh`
emits a GitHub Actions or GitLab CI workflow that invokes `orchestrator.py`.

## Le contrat `/ship`

> **Tant que `/ship <story-id>` n'émet pas "PR CREATED" avec le tag
> `sdd-validated-v5`, le code n'a pas le droit de quitter la machine du dev.**

`/ship` est la seule porte de sortie. Le dev ne lance jamais `gh pr create`
manuellement. `/ship` invoque `/review` (toutes les gates applicables rejouées
sur la branche complète) ; si PASS, push + PR créée par l'agent
`release-manager` avec titre, description, evidence `_work/build/<id>.yaml`,
et tag `sdd-validated-v5`. Une PR créée à la main n'a pas le tag — et est
rejetée en review humaine.

La chaîne d'assurance pré-PR compte **9 maillons** (§7 de
`_docs/PIPELINE.md`) : tests passent · tests testent vraiment (mutation) ·
build compile · app démarre · régression prior-stories · contrats
inter-modules · ACs satisfaits · code propre/sûr/observable/performant · PR
prête.

## Quality gates (G1–G14)

| Gate | Name | Applies to | Blocks on |
|---|---|---|---|
| G1 | Security | All | OWASP patterns, AC-SEC fail, dep vulns |
| G2 | Unit tests | All | Fail, coverage < threshold, flakiness |
| G2.1 | Mutation testing | All | Score < 80% on changed files |
| G2.2 | Regression suite | All | Prior-story test fails |
| G2.3 | Contract diff | All (API/lib/DB/CLI) | Breaking change undeclared |
| G3 | Code quality | All | Tool violation or no tool configured |
| G4 | Build final | All | Build error, type error |
| G4.1 | Smoke boot | All | App fails to start / respond |
| G5 | AC validation | All | Tier-1 `verify:` command fails |
| G6 | Story review (AC ↔ code) | All | AC Tier 2/3 not implemented |
| G7 | Code review | All | Scope, console errors, SOLID |
| G8 | Integration cross-stories | If touches validated module | Contract break inter-module |
| G9.1 | Design System | web-ui, mobile | Hardcoded token, unauthorised component |
| G9.2 | Wireframe conformity | web-ui, mobile | `data-testid` missing, hierarchy mismatch |
| G9.3 | Visual regression | web-ui, mobile | Pixel diff > threshold on 3 viewports |
| G9.4 | Interaction verification | web-ui, mobile | `interactions:` expected ≠ actual |
| G9.5 | Accessibility (WCAG) | web-ui, mobile | axe AA violation, keyboard trap |
| G9.6 | Behavioral regression | web-ui, mobile | Prior-story `interactions:` broken |
| G10 | Performance | All (opt-in for library) | > 5% regression vs baseline |
| G11 | Observability | web-api, web-ui, ml-pipeline | Ratio logs/metrics/traces below min |
| G12 | Runtime security / DAST | web-api, web-ui | Fuzz + OWASP ZAP-lite violations |
| G13 | Migration safety | If migration | Rollback KO, data loss, seed not preserved |
| G14 | Release readiness | At `/ship` | CHANGELOG / VERSION / tags incoherent |

## TDD enforcement (machine, not honor)

The orchestrator (`scripts/orchestrator.py`) is the source of truth. Git hooks
are feedback-only. `--no-verify` or weakened assertions are caught at the next
orchestrator pass via AST diff between commits → story moves to `tampered`,
only `/resume` unblocks.

**20 scripts** in `scripts/`. 6 refactored in v5 (AST):

| Script | Gate | Blocks on |
|--------|------|-----------|
| `check_red_phase.py` | After RED | Trivial failures, no real production import |
| `check_test_intentions.py` | After RED | Spec intentions without matching tests (embedding similarity, fallback regex) |
| `check_coverage_audit.py` | After RED | Endpoints/tables/components without tests (AST, f-strings, dynamic routes) |
| `check_msw_contracts.py` | After RED | MSW vs backend field names (Pydantic heritage chain resolved) |
| `check_test_tampering.py` | After GREEN | AST diff — any assertion removed |
| `check_oracle_assertions.py` | G1, pre-commit | Parses and evaluates `# ORACLE:` expression in sandbox |

Plus `check_tdd_order.py`, `check_story_commits.py`, `check_test_quality.py`,
`check_write_coverage.py` (retained) and 10 new scripts for G8–G14 and G9.x.
Full list: `_docs/PIPELINE.md §5`.

## Agents (18)

| Agent | Role | Model | Changed from v4 |
|---|---|---|---|
| product-owner | Scoping, spec YAML, constitution | Opus | — |
| ux-ui | Wireframes, flows, DS tokens | Sonnet | — |
| architect | Architecture, manifest, component inventory | Opus | — |
| refinement | Story breakdown, `verify:`, `interactions:`, oracle | Opus | — |
| builder-service | Backend: routers, services, repos | Sonnet | — |
| builder-frontend | Frontend: components, hooks, MSW contracts | Sonnet | — |
| builder-infra | Docker, CI/CD, proxy | Sonnet | — |
| builder-migration | Database migrations + roundtrip | Sonnet | — |
| builder-exchange | Exchange adapters (safety-critical) | Opus | — |
| **test-author** | TDD RED (failing tests) + GREEN (no tamper). Modes `red`/`green`. | Opus | **Merged** `tester` + `test-engineer` |
| validator | Independent `verify:` runner (Tier 1) | Sonnet | — |
| **code-reviewer** | G6 semantic AC↔code (mode `story`) + G7 quality/scope (mode `code`) | Opus | **Merged** `reviewer` + `story-reviewer` |
| security | OWASP + static + dep audit | Sonnet/Opus | — |
| devops | CI/CD, deployment | Sonnet | — |
| **observability-engineer** | Structured logs, metrics, traces, alerts | Sonnet | **New** (G11) |
| **performance-engineer** | Perf budgets, baseline, N+1, profiling | Sonnet | **New** (G10) |
| **data-migration-engineer** | Data transformations (distinct from schema migrations) | Opus | **New** (G13) |
| **release-manager** | Version bump, CHANGELOG, tags, `gh pr create` | Sonnet | **New** (G14, used by `/ship`) |

**Removed in v5**: `developer` (duplicate of the 5 builders), `orchestrator`
(now `scripts/orchestrator.py`), `spec-generator` (YAML is source of truth).

## Stack plugin system

Core = Python + YAML. Projects pick stacks and can add custom ones without
touching the framework core.

```
my-project/_work/stacks/
├── registry.yaml                 # active stacks for this project
├── python-fastapi/               # built-in, copied from framework
│   ├── profile.yaml
│   ├── ac-templates.yaml
│   └── checks/
├── typescript-react/             # built-in
├── go-gin/                       # custom — 4 files: profile, ac-templates, smoke-boot, README
│   └── ...
```

Adding a custom stack = 4 files in `_work/stacks/<name>/` + one line in
`registry.yaml`. Full guide: [`stacks/CUSTOM_STACK_GUIDE.md`](stacks/CUSTOM_STACK_GUIDE.md).

## Project structure (after init)

```
my-project/
├── framework/              # Git submodule → this repo
├── _work/
│   ├── stacks/             # Active stacks (registry + profiles)
│   ├── spec/               # Per-story spec overlays
│   ├── build/              # Pipeline state per story (gates) + test-registry.yaml
│   ├── contracts/          # API/AST/DB/CLI snapshots (G2.3)
│   ├── visual-baseline/    # Pixel baselines (G9.3)
│   ├── perf-baseline/      # Perf metrics (G10)
│   ├── data-fixtures/      # Seed data for migrations (G13)
│   └── ux/wireframes/      # HTML wireframes with data-testid
├── specs/
│   ├── constitution.md
│   ├── <project>.yaml
│   ├── <project>-arch.md
│   ├── design-system.yaml  # UI projects — tokens + authorised components
│   ├── feature-tracker.yaml
│   └── stories/            # Story files + manifests
├── memory/                 # Project memory + LESSONS.md
├── apps/                   # Application code
├── .claude/
│   ├── skills/             # Symlinks → framework/skills
│   └── settings.json       # Hooks: 20 scripts wired via settings
├── .env                    # SonarQube config (gitignored)
├── CLAUDE.md               # From rules/CLAUDE.md.template
└── .cursorrules            # Cursor rules
```

## Documentation

| Document | Content |
|---|---|
| [`_docs/PIPELINE.md`](_docs/PIPELINE.md) | The whole pipeline (commands, gates G1–G14, 18 agents, 20 scripts, stack plugins, assurance chain, state machine) |
| [`rules/GUIDE.md`](rules/GUIDE.md) | Full rules reference (principles, coding standards, test quality, agent conduct, commits, git flow) |
| [`rules/CHEATSHEET.md`](rules/CHEATSHEET.md) | 1-page TL;DR for any agent |
| [`stacks/CUSTOM_STACK_GUIDE.md`](stacks/CUSTOM_STACK_GUIDE.md) | Author a custom stack plugin in 4 files |
| [`_docs/sonarqube.md`](_docs/sonarqube.md) | SonarQube setup, config, troubleshooting |
| [`_docs/test-methodology.md`](_docs/test-methodology.md) | Two-loop test approach (spec→oracle + mutation) |
| [`_docs/token-costs.md`](_docs/token-costs.md) | Token cost per agent and per skill session |
| [`_docs/INDEX.md`](_docs/INDEX.md) | Navigation hub |

## Migration

| From | To | Command |
|---|---|---|
| v3.x | v4.0 | `framework/scripts/migrate-v3-to-v4.sh` |
| v4.0.x | v4.1.0 | `framework/scripts/migrate-v4.0-to-v4.1.sh` |
| v4.1.x | v5.0 | `framework/scripts/migrate-v4-to-v5.sh --dry-run` then `--backup` |

v5 is a breaking change. The migration script produces a dry-run report, backs
up to `_backup_v4/`, and supports `--rollback`.

## Contributing

Every improvement is a commit + PR. Projects get updates via
`git submodule update --remote framework`.

## License

MIT
