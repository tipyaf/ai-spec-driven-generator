# Changelog

## [3.0.10] - 2026-03-29

- feat: add build state gates to manifest — persist gate results between sessions


## [3.0.9] - 2026-03-29

- docs: update README with component reuse pipeline and interactive best practices


## [3.0.8] - 2026-03-29

- fix: add mandatory final recap with user confirmation to best practices proposal


## [3.0.7] - 2026-03-29

- feat: interactive best practices proposal during architecture phase


## [3.0.6] - 2026-03-29

- fix: remove low-value UI Rules section from stack profile template


## [3.0.5] - 2026-03-29

- fix: make UI rules in stack profile template platform-agnostic


## [3.0.4] - 2026-03-29

- feat: add frontend rules sections to stack profile template


## [3.0.3] - 2026-03-29

- feat: add component reuse checks across the pipeline (UI projects)


## [3.0.2] - 2026-03-29

- fix: add missing test-methodology.md referenced by tester agent


## [3.0.1] - 2026-03-29

- feat: wave 2 — advanced quality pipeline, implementation manifest, agent restructuring


## [2.3.1] - 2026-03-28

- feat: add Git Flow branching model and update worktree rules


## [2.3.0] - 2026-03-28

### Added
- **Git Flow branching model**: `main` (production, releases only) + `develop` (integration, all feature work) — enforced as agent rule 10
- **Pre-flight PR check**: agents must verify `--base develop` and `git log origin/develop..HEAD` before every `gh pr create`
- **Worktree isolation updated**: worktrees now branch from `origin/develop` instead of `origin/main`, PR targets updated to integration branch

### Changed
- **Worktree rule**: `origin/main` → `origin/develop` as default base branch for worktrees
- **CLAUDE.md.template**: added Git Flow and worktree sections for new projects
- **README**: added Git & Infrastructure section documenting branching model and worktree isolation

## [2.2.1] - 2026-03-28

- Update bump-version.yml


All notable changes to the ai-spec-driven-generator framework.

## [2.2.0] - 2026-03-25

### Added
- **Claude Code slash commands**: `/spec`, `/refine`, `/build`, `/validate`, `/review` now work as native Claude Code commands via `.claude/commands/` files
- **Command templates** in `rules/commands/`: reusable templates that `init-project.sh` copies into new projects
- **init-project.sh** now creates `.claude/commands/` directory and copies all command templates automatically

### Fixed
- Skills were documented in CLAUDE.md but not registered as Claude Code commands — Claude couldn't dispatch them as slash commands

## [2.1.0] - 2026-03-24

### Added
- **Enforcement layer**: filesystem-based phase guards — a phase is "done" when its artefact exists on disk
- **Feature tracker** (`specs/feature-tracker.yaml`): per-feature state management (pending → refined → building → testing → validated)
- **Story files** (`specs/stories/[feature-id].yaml`): persistent build contracts with `verify:` commands that survive between sessions
- **Unified AC format**: `AC-[TYPE]-[FEATURE]-[NUMBER]` with mandatory `verify:` shell commands and testability tiers (1/2/3)
- **Constitution phase**: non-negotiable project principles as a versioned artefact (`specs/constitution.md`)
- **Clarify phase**: resolve spec ambiguities before architecture planning
- **5 sequential quality gates**: Security → Tests → UI → AC Validation → Review
- **Cycle counter**: max 3 validation cycles per feature before human escalation
- **Story template** (`specs/templates/story-template.yaml`)
- **Feature tracker template** (`specs/templates/feature-tracker.yaml`)

### Changed
- **CLAUDE.md**: complete rewrite with v3 workflow, enforcement mechanisms, unified AC format
- **Skills (all 5)**: rewritten with filesystem phase guards and story-based contracts
- **Orchestrator**: transformed from active agent to reference document (rules distributed into skills)
- **Product Owner**: AC format now requires `verify:` commands, `verify: static` banned
- **Refinement agent**: writes story files, updates tracker, verifies all ACs have verify: commands
- **Validator agent**: reads story file as primary source, executes verify: commands, checks scope
- **Spec template**: unified AC format replaces fragmented acceptance_criteria + acceptance_tests
- **Todo app example**: all features rewritten with structured ACs (IDs, types, verify:, tiers)
- **Memory template**: added feature status table, framework version, decisions with alternatives
- **.cursorrules**: aligned with CLAUDE.md v3 skill-based approach

### Removed
- Dead `validation:` section from spec template (no agent read it)
- Orchestrator as an active loaded agent (never loaded by any skill)

## [2.0.0] - 2026-03-23

### Added
- 3 fundamental principles: Agnostic, Autonomous, Accompaniment
- Validator agent for independent implementation verification
- Implementation manifest for context slicing
- Machine-verifiable acceptance tests (visual, runtime, grep, e2e)
- Phase 3.5 (Validate) and Phase 5.5 (Security) — auto-validated
- WCAG 2.1 AA contrast ratio acceptance criteria in UX/UI agent
- LESSONS.md persistent failure memory
- Language-agnostic hook-config.json
- Agent role guards in CLAUDE.md
- Deployment verification in Phase 6
- Claude Code skills: /refine, /build, /review, /validate, /spec
- Auto-versioning with GitHub Action
- SYNC.md for version tracking across projects
- BOOTSTRAP.md onboarding checklist

### Changed
- Phases 4 (Test), 5 (Review), 5.5 (Security) now auto-validated
- "Humans decide, machines verify" principle applied throughout
- All agents now platform-aware (conditional sections per project type)
- PO challenges assumptions before writing specs
- Architect presents stack options in comparison tables
- Tester requires e2e Playwright + unit tests + WCAG audit
- Spec template expanded with 10 project types
