# Changelog

## [5.0.8] - 2026-04-17

- fix(orchestrator): pick root spec by top-level `type:`, not alphabetical order


## [5.0.7] - 2026-04-17

### Fixes (another dog-fooding find on the 71-story monorepo)

- **Migration now generates `.claude/commands/*.md` wrappers for every
  v5 skill.** Previously, migrating a v4 project left Claude Code unable
  to discover the 7 new v5 commands (`/next`, `/ship`, `/status`,
  `/help`, `/resume`, `/scan`, `/migrate`) because the framework ships
  their `SKILL.md` under `framework/skills/*/` but Claude Code looks up
  slash-commands in `<project>/.claude/commands/*.md`. Migrated projects
  also kept stale v4 wrappers advertising "SDD framework v2.1.0" and
  describing the old agent roster.

  v5.0.7 adds **Step 8b** to `migrate-v4-to-v5.sh`:

  - For every v5 skill present under `framework/skills/`, generate a
    thin wrapper at `.claude/commands/<name>.md` carrying the
    `<!-- sdd-v5-wrapper: managed by migrate-v4-to-v5.sh -->` marker.
  - Refresh any existing wrapper whose content still references v2 /
    v3 / v4 (the whole point of the migration is to update those).
  - Leave user-customised wrappers alone: if the user removed the
    marker, they opted out of auto-refresh.
  - Project-specific commands with no matching SKILL.md (e.g.
    `dev.md`, `<project>-tooling.md`) are never touched.

- **Idempotent**: re-running the migration on an already-migrated
  project is safe — re-emits the wrappers only if their content
  drifted.

### Tests

- 3 new regression tests (`test_claude_commands_wrappers_generated`,
  `test_claude_commands_respects_user_opt_out`,
  `test_claude_commands_refreshes_v4_stale_wrappers`). Framework
  self-tests: **246/246 passing**.

### Upgrade path for projects already on v5.0.x

If you migrated to v5 BEFORE v5.0.7, your `.claude/commands/` still
misses the 7 new commands or has stale v4 content. Re-run the
migration (idempotent by design):

```bash
cd framework && git fetch --tags origin && git checkout v5.0.7 && cd ..
./framework/scripts/migrate-v4-to-v5.sh --force
git diff .claude/commands/   # review
```

Or create the wrappers directly via:

```bash
python3 framework/scripts/migrate-v4-to-v5_helpers.py \
  claude-commands --project .
```

## [5.0.6] - 2026-04-17

### Fixes (fourth dog-fooding pass)

- **Space-separated agent names renamed too.** v4 docs interleave three
  stylings for the same agent: `story-reviewer` (kebab), `Story-Reviewer`
  (Title-Kebab), AND `Story Reviewer` (Title + space). v5.0.5 handled
  the first two; v5.0.6 adds the space-separated variants:
    * `Story Reviewer` / `story reviewer` → `Code-Reviewer` / `code-reviewer`
    * `Test Engineer` / `test engineer` → `Test-Author` / `test-author`
  Previously `| Story Reviewer | Audit |` in a table row produced
  `| Story Code-Reviewer |` (the first word was left untouched).

## [5.0.5] - 2026-04-17

### Fixes (third dog-fooding pass — one more bug on the 71-story monorepo)

- **Agent renames now handle Title-Case tokens.** Mature v4 CLAUDE.md files
  use Title Case in model catalogue tables (`| Tester | Opus | ... |`,
  `| Reviewer | Audit quality |`). v5.0.4 regexes were lowercase-only
  (`\btester\b`) and missed those rows. v5.0.5 adds explicit Title-Case
  variants to both `AGENT_RENAMES` (agents subcommand) and
  `CLAUDE_MD_REPLACEMENTS` (claude-md subcommand):
    * Tester → Test-Author
    * Test-Engineer → Test-Author
    * Reviewer → Code-Reviewer (with same `(?<!Code-)(?<!Peer-)(?<!Story-)`
      lookbehind as lowercase)
    * Story-Reviewer → Code-Reviewer
    * Spec-Generator → Refinement

### Tests

- 1 new regression test for Title-Case markdown tables. Framework
  self-tests: **243/243 passing**.

## [5.0.4] - 2026-04-17

### Fixes (second dog-fooding pass — two more bugs on the 71-story monorepo)

- **Agent renames no longer clobber arbitrary prose.** v5.0.3 used word
  boundaries (`\btester\b`) for every rename, which meant the French
  verb `tester` (infinitive, "to test") in a migration doc was rewritten
  to `test-author` — e.g. `tester la connexion` → `test-author la
  connexion`. v5.0.4 only rewrites when the token is clearly a framework
  agent reference:
    * file-path references (`agents/tester.md`, `agents/tester/`)
    * YAML values of agent-ish keys (`agent:`, `agents:`, `dispatch:`,
      `loaded_by:`, `role:`, `runner:`, `invokes:`, `responsibility:`,
      `handled_by:`)
    * bare YAML list items (`  - tester` under an `agents:` key)
    * explicit noun phrases (`tester agent`)
    * Markdown emphasis (`**tester**`), inline code (`` `tester` ``)
    * whole-cell markdown table rows (`| tester | ... |`)
  Everything else — including `owner: tester` (person's name) and French
  infinitive verbs — is left alone.

- **`spec.type` auto-write targets `specs/<project-name>.yaml` specifically.**
  v5.0.3 wrote `type:` into the first root spec alphabetically, which on
  expat-hunter turned out to be `contact-sourcing-strategy.yaml` (a
  sub-epic), not the main `expat-hunter.yaml`. v5.0.4 looks for
  `specs/<directory-name>.yaml` first; if that's missing and there's
  exactly one root spec, uses that; if there are multiple ambiguous
  candidates, skips with a clear log asking the dev to add `type:`
  manually.

### Tests

- 2 new regression tests (French `tester` verb; multi-root-spec
  disambiguation). One existing test updated to reflect the new, more
  conservative rewrite semantics (an `owner: tester` story field is no
  longer auto-renamed — that's the correct behaviour).
- Framework self-tests: **242/242 passing**.

## [5.0.3] - 2026-04-17

### Fixes (found by dog-fooding the migration on a real v4.1.1 project with 71 stories)

- **`spec.type` detection no longer trusts per-story `type:` fields.** v5.0.2
  walked every YAML in `specs/` and `_work/spec/` and returned the first
  `type:` it found — which was typically a domain-specific field like
  `type: smart` on an email-template story, not the project's spec.type.
  v5.0.3 inspects only ROOT project specs (excluding stories,
  feature-tracker, design-system, arch/ux docs) and only accepts values
  that are valid v5 types (`web-ui`, `web-api`, `cli`, `library`,
  `ml-pipeline`, `mobile`, `embedded`).
- **`spec.type` is now written into the root project spec**, not into the
  first `sc-*.yaml` story overlay the script could find. v5.0.2 corrupted
  `_work/spec/sc-181.yaml` on a real migration.
- **CLAUDE.md agent renames no longer produce `code-code-reviewer`.**
  The `reviewer → code-reviewer` replacement now uses a negative lookbehind
  so it skips tokens already prefixed with `code-` / `peer-` / `story-`.
  Also adds a `test-engineer → test-author` rule that was missing.
- **`CLAUDE.md` gate-count replacement is clearer**: "11 quality gates"
  becomes "14 quality gates (G1–G14 adaptive)" instead of a flat "14
  quality gates" (which was misleading — v5 has G1, G2, G2.1, G2.2, G2.3,
  G3, G4, G4.1, G5, G6, G7, G8, plus conditional G9.x / G10–G14).
- **`_work/stacks/registry.yaml` is now auto-detected.** A new
  `migrate-v4-to-v5_helpers.py stack-detect` command inspects package.json
  (root AND nested workspaces for monorepos), pyproject.toml, docker
  compose files, and ORM config to decide which built-in stacks to enable.
  v5.0.2 enabled python-fastapi + typescript-react + postgres everywhere
  regardless of project.
- **`spec.type` inference is monorepo-aware.** Previously only the root
  `package.json` was inspected; v5.0.3 also walks `apps/*/package.json`,
  `packages/*/package.json`, `services/*/package.json` so a fullstack
  monorepo with a React frontend in `apps/frontend/` is correctly inferred
  as `web-ui`. Priority order when multiple surfaces are present:
  mobile > web-ui > web-api > cli > library.

### Tests

- 4 new regression tests in `tests/test_migration_v4_to_v5.py` — one per
  fixed bug above. Framework self-tests: **240/240 passing**.

## [5.0.2] - 2026-04-17

### Fixes

- **`migrate-v4-to-v5.sh`**: the script no longer treats a project as
  "already migrated" when the framework submodule is on v5 but the
  project's own `CLAUDE.md` is still v4. The version check now inspects
  the project state (CLAUDE.md markers) first, and only falls back to
  `framework/VERSION` when no project markers are found. This matters
  for users who update the submodule before running the migration —
  which is the most natural flow.
- Clearer diagnostic output: the script now reports both "Framework
  pinned at:" and "Project CLAUDE.md state:" so the user sees exactly
  why the script decided to proceed or skip.

### Note on 5.0.1

v5.0.1 was a CI-only version bump (no code or doc changes).

## [5.0.0] - 2026-04-17

**Major release — complete rebuild of the SDD framework.** The audit of v4.1.1
revealed a structural gap between what the README promised (agnostic, 11 gates
never skipped, machine enforcement) and what the code did (UI-hardcoded gates,
9 of 10 scripts orphaned, agents redundant, bypass trivial). v5 closes that
gap. Migration is breaking but automated via `scripts/migrate-v4-to-v5.sh`.

### Headline changes

- **Executable orchestrator**: `scripts/orchestrator.py` becomes the single
  source of truth for gate execution. `/build`, `/validate`, `/review`, `/ship`
  are thin wrappers. Every check is re-run at every gate — bypassing a hook
  with `--no-verify` is caught at the next orchestrator pass via AST diff
  between commits.
- **Adaptive gates G1–G14** driven by `spec.type`. Project-types YAML
  (`stacks/project-types/`) declare which gates run. Web-UI inherits web-api
  and adds G9.1–G9.6. CLI, library, ml-pipeline, mobile, embedded land
  progressively in v5.x.
- **`/ship` is the only door to PR.** The developer never runs `gh pr create`
  manually. `/ship` reruns `/review` on the whole branch; on pass, the
  `release-manager` agent pushes, opens the PR, attaches the evidence report,
  and tags it `sdd-validated-v5`. A manual PR has no tag → rejected in
  human review.
- **9-link pre-PR assurance chain**: unit tests · mutation testing (G2.1) ·
  build compiles · app actually boots (G4.1) · regression suite on prior
  stories · cross-story contracts · AC satisfied mechanically + semantically ·
  code clean/secure/observable/performant · PR ready.
- **6-layer anti-regression**: code (G2.2), contract (G2.3), visual (G9.3),
  behavioural (G9.6), performance (G10 vs baseline), data (G13 with seed +
  rollback).
- **/next command**: priority action list. Run it in the morning — the
  framework tells you what to do (BLOCKING / IN PROGRESS / READY / PENDING
  SHIP / SUGGESTIONS). `--json` for dashboards.
- **CI/CD optional**: framework enforces quality without CI. For a tiers
  belt, `scripts/generate-ci.sh` emits a workflow that invokes
  `orchestrator.py --gate-all`.

### Agents (19 → 18)

- **Fusions**: `tester` + `test-engineer` → `test-author` (modes: red|green);
  `reviewer` + `story-reviewer` → `code-reviewer` (scopes: story|code).
- **Removed**: `developer` (redundant with 5 builders), `spec-generator`
  (YAML is the source of truth), `orchestrator` (now `scripts/orchestrator.py`
  — a 4-line stub redirects).
- **New**: `observability-engineer`, `performance-engineer`,
  `data-migration-engineer`, `release-manager`.
- **`.ref.md` templates** moved from `agents/` to `examples/agents/[name]/`
  (consultable, no longer auto-loaded — smaller context, clearer navigation).

### Scripts (10 → 20) — all executed by the orchestrator, no more orphans

- **Refactored from regex to AST**: `check_red_phase` (catches
  `assert 1 != 2`, `pytest.fail()`, `raise AssertionError()`),
  `check_test_tampering` (AST diff between SHAs — removed assertions flagged
  even if 10 others are added), `check_coverage_audit` (dynamic routes,
  f-strings, constants), `check_oracle_assertions` (**sandbox-evaluates** the
  ORACLE comment against actual values), `check_test_intentions` (optional
  sentence-transformers similarity, regex fallback).
- **`--scan-branch` flag** added to `check_red_phase`, `check_test_tampering`,
  `check_tdd_order`, `check_story_commits`. Orchestrator runs these against
  `git log main..HEAD` — bypass via `--no-verify` is detected.
- **New**: `check_integration_coverage`, `check_performance_budget`,
  `check_observability`, `check_release_artifacts`, `check_migration_safety`,
  `check_ds_conformity`, `check_contract_diff`, `generate-interaction-tests`,
  `check_visual_regression`, `check_behavioral_regression`,
  `next_report`, `ui_messages`, `orchestrator`.

### Stack plugin system

- **Built-in stacks** restructured as directories with `profile.yaml`,
  `ac-templates.yaml`, `checks/`, `smoke-boot.yaml` (or
  `migration-strategy.yaml`), `README.md`:
  - `python-fastapi` (conserved)
  - `typescript-react` (conserved; `check_msw_contracts.py` moved here from
    `scripts/`)
  - `postgres` (conserved; `check_write_coverage.py` moved here from
    `scripts/`)
  - `nodejs-express` (new in v5)
- **Custom stacks** supported via `_work/stacks/registry.yaml` per project.
  See `stacks/CUSTOM_STACK_GUIDE.md` — end-to-end `go-gin` example included.

### UI guarantees (web-ui, mobile)

- **G9.1 Design System conformity** — tokens declared in
  `specs/design-system.yaml`. Hardcoded `#ff0000` or `padding: 13px` → fail.
- **G9.2 Wireframe structural conformity** — all `data-testid` from the
  wireframe HTML must exist in the rendered DOM with the declared hierarchy.
- **G9.3 Visual regression** — Playwright snapshot × 3 viewports
  (mobile/tablet/desktop). First baseline requires human approval.
- **G9.4 Interaction verification** — stories declare `interactions:`
  (trigger + expected DOM/URL/API/state). `generate-interaction-tests.py`
  auto-generates Playwright specs. **Answers the question
  "does clicking the button do what was asked?"**
- **G9.5 Accessibility** — axe-core AA, keyboard, contrast.
- **G9.6 Behavioural regression** — prior stories' `interactions:` are
  replayed.

### Skills (10 → 13)

- **Consolidated**: `/scan`, `/scan-full`, `/sonar` → single
  `/scan [--full] [--report]`.
- **New**: `/ship` (the only exit door to PR), `/next` (morning action
  list), `/status` (dashboard), `/help [command]`,
  `/resume <story-id> "reason..."`.
- **Simplified**: `/build` auto-dispatches the right builder from the
  manifest — no more `/build-service`, `/build-frontend`, etc.

### Documentation

- 4 old docs (`_docs/{agents,process,workflow,skills}.md`) merged into
  `_docs/PIPELINE.md` (unified, 381 L).
- 4 old rules (`CLAUDE.md`, `coding-standards.md`, `test-quality.md`,
  `agent-conduct.md`) merged into `rules/GUIDE.md` (479 L) +
  `rules/CHEATSHEET.md` (114 L TL;DR).
- README.md rewritten, honest, no overselling.
- `_docs/MIGRATION_V4_TO_V5.md` for upgraders.

### Tests of the framework itself

- **236 tests passing** across 9 suites: orchestrator scaffold, stack
  plugins, AST refactors, skills integration, docs consistency, migration,
  next_report, gate unit tests, tamper detection, e2e per spec.type.
- Obsolete v4 `tests/framework/` suite retired (concepts it tested — "11
  gates", old agent names, pre-plugin scripts — no longer exist; replaced
  by the above v5 suites).

### Migration

```bash
# From a project on v4.x:
framework/scripts/migrate-v4-to-v5.sh --dry-run        # preview
framework/scripts/migrate-v4-to-v5.sh --backup         # apply with _backup_v4/
framework/scripts/migrate-v4-to-v5.sh --rollback       # undo if needed
```

The migration:
- Renames agent references (`tester`/`test-engineer` → `test-author`;
  `reviewer`/`story-reviewer` → `code-reviewer`).
- Detects `spec.type` from project files or asks.
- Creates `_work/stacks/registry.yaml` with the right stacks.
- Adds new `_work/` directories (visual-baseline, perf-baseline, contracts,
  data-fixtures).
- Rewrites CLAUDE.md references from v4 (11 gates, 19 agents, 10 scripts) to
  v5 (G1–G14, 18 agents, 20 scripts).
- Merges `.claude/settings.json` with the new hook configuration while
  preserving project-specific keys.
- Blocked stories become `escalated` (escalation is now blocking in v5).
- Writes `MIGRATION_REPORT.md` listing manual follow-ups.

### Breaking changes summary

- Command surface: `/build-service`, `/build-frontend`, `/build-infra`,
  `/build-migration`, `/build-exchange` → unified `/build`. `/scan-full`
  and `/sonar` → `/scan --full`.
- Agent references: `tester`, `test-engineer`, `reviewer`,
  `story-reviewer`, `developer`, `orchestrator`, `spec-generator` →
  replaced or removed.
- Gate numbering: v4 "11 gates" → v5 G1–G14 adaptive.
- `rules/CLAUDE.md` (source file, divergent from template) deleted — only
  `rules/CLAUDE.md.template` remains. `init-project.sh` generates the
  project-specific CLAUDE.md from the template.
- `check_msw_contracts.py` and `check_write_coverage.py` moved from
  `scripts/` into their stack plugin.

## [4.1.1] - 2026-04-07

- feat: add Git Flow enforcement hooks — block PRs targeting main, direct pushes, and branching from main


## [4.1.0] - 2026-04-07

### Refine phase evolution
- feat: wireframe gate for UI projects — auto-create HTML wireframes with data-testid attributes
- feat: WCAG 2.1 AA validation on wireframes with loop-until-pass
- feat: generic PM integration (Shortcut, Jira, GitLab, MCP) — replaces Shortcut-only
- feat: auto-generated validation ACs (AC-BP-COMPILE, AC-BP-TU, AC-BP-CONSOLE, AC-BP-WCAG, AC-BP-WIREFRAME)
- feat: UX/UI agent now triggered from /refine for wireframe creation

### Build phase evolution
- feat: 11 quality gates (was 7) — Security, Unit Tests, Code Quality, E2E Code, WCAG+Wireframes, E2E Execution, E2E vs Wireframes, AC Validation, Story Review, Code Review, Final Compilation
- feat: RED phase with 4 steps (create TU, quality scan, review, validate)
- feat: GREEN phase with 2 steps (code, compilation)
- feat: code quality gate (Gate 3) NEVER skipped — reviewer 3-pass fallback when no tool configured
- feat: Gate 10 (Code Review) now includes console error verification (0 errors required)
- feat: compilation gate in both GREEN phase and Gate 11 (final validation)
- feat: data-testid contract — wireframe HTML defines IDs, builder reproduces them, E2E targets them

### Commit enforcement
- feat: atomic commit after ALL 11 gates pass (story + manifest + tracker + code + tests)
- feat: PR/MR auto-creation — detect gh/glab/az once, memorize in memory/
- feat: check_story_commits.py enforcement script — validates atomic commit, YAML validity, verify: fields
- feat: setup-hooks.sh updated with story commit check

### Rules and agents
- feat: agent-conduct.md — 7 new rules (Rules 11-17): explicit git add, atomic commit, real-time user feedback, user language, tool optionality, data-testid contract, specs as source of truth
- feat: developer.md — GREEN phase, compilation, E2E, console errors, data-testid constraints
- feat: validator.md — restructured for 11 gates with correction loop points
- feat: refinement.md — wireframe workflow, PM integration, validation ACs
- feat: ux-ui.md — /refine trigger, HTML wireframe generation, data-testid

### Testing
- feat: 231 framework tests (was 151) — new test files for refine and commit enforcement
- feat: test_pipeline.py updated for 11 gates
- feat: test_dataflow.py updated with wireframe flow and validation ACs
- feat: test_refine.py — wireframe gate, WCAG, PM integration, validation ACs
- feat: test_commit_enforcement.py — atomic commit, git add rules, check_story_commits.py

### Documentation
- docs: README updated — 11 gates, wireframe HTML, compilation, PM integration
- docs: CLAUDE.md updated — 11 gates in phase workflow

## [4.0.11] - 2026-04-04

- feat: 4 evolutions (TDAD, Trigger C, Rule 2b, token costs) + 151 framework self-tests

## [4.0.10] - 2026-04-04

- feat: enforce agent model dispatch from frontmatter


## [4.0.9] - 2026-04-04

- docs: rewrite README — clearer structure, half the size


## [4.0.8] - 2026-04-04

- feat: add next-step guidance to all skills — only on manual action required


## [4.0.7] - 2026-04-04

- feat: add SonarQube as Gate 6 in validation pipeline


## [4.0.6] - 2026-04-04

- docs: update README — 6 quality gates, SonarQube positioning


## [4.0.5] - 2026-04-04

- feat: make story-reviewer a mandatory blocking gate before validated


## [4.0.4] - 2026-04-04

- fix: auto-detect base branch for SonarQube diff — support all branching models


## [4.0.3] - 2026-04-04

- fix: sonar_check.py ROOT resolution — use git toplevel instead of parent traversal


## [4.0.2] - 2026-04-04

- fix: cross-platform SonarQube config — .env per project, Python 3.8+ compat


## [4.0.1] - 2026-04-04

- feat: v4.0.0 — TDD enforcement pipeline, 8 new agents, 5 new skills, migration tooling


## [4.0.0] - 2026-04-04

### Added — Machine-Enforced TDD Pipeline
- **6 new enforcement scripts** blocking the pipeline: `check_red_phase.py` (tests must fail in RED), `check_test_intentions.py` (every spec intention has a test), `check_coverage_audit.py` (every endpoint/table/component tested), `check_msw_contracts.py` (MSW mocks match Pydantic fields), `check_tdd_order.py` (RED commit before GREEN), `check_test_tampering.py` (builder cannot weaken tests)
- **Build file system**: `_work/build/sc-[ID].yaml` tracks pipeline gates per story (RED/GREEN/review/security/validation)
- **SonarQube integration**: `sonar_check.py` hook, `/scan`, `/scan-full`, `/sonar` skills

### Added — New Agents (8)
- **test-engineer**: Opus-only agent for TDD RED phase — writes failing tests before code
- **spec-generator**: YAML overlay merging to markdown documentation
- **story-reviewer**: Per-story AC verification (separated from code reviewer)
- **builder-service**: Specialized backend builder (Python/FastAPI)
- **builder-frontend**: Specialized frontend builder (React/TypeScript, MSW contracts)
- **builder-infra**: Docker/CI-CD specialist
- **builder-migration**: Database migration expert (Alembic)
- **builder-exchange**: Safety-critical exchange integration (Opus-only)

### Added — New Skills (5)
- `/scan` — SonarQube scan on local changes
- `/scan-full` — Full codebase SonarQube analysis
- `/sonar` — SonarQube status dashboard
- `/ux` — UX design with 3 mandatory artefacts (spec + YAML + HTML prototype)
- `/migrate` — Migrate v3.x projects to v4.0 structure

### Added — Documentation & Templates
- **7 documentation files** in `_docs/`: INDEX, agents catalog, process lifecycle, workflow conventions, skills guide, SonarQube guide (+ existing test-methodology)
- **Build template** (`specs/templates/build-template.yaml`): pipeline state tracker with gates
- **Spec overlay template** (`specs/templates/spec-overlay-template.yaml`)
- **Stack profile examples**: `python-fastapi.md`, `typescript-react.md`, `postgres.md`
- **Migration script** (`scripts/migrate-v3-to-v4.sh`): idempotent, dry-run, backup, macOS/Linux compatible

### Changed — Structural
- **`_work/` directory convention**: specs at `_work/spec/`, build state at `_work/build/`, UX at `_work/ux/`, stacks at `_work/stacks/`
- **Skills enriched**: `/build` now dispatches to specialized builders with TDD gates; `/refine` auto-generates AC-SEC/AC-BP from stack profiles; `/review` separates story review from code review; `/validate` enforces max 3 cycles
- **agent-conduct.md**: added 3 rules (TDD gates by orchestrator, enforcement scripts non-negotiable, read playbook first)
- **test-quality.md**: added MSW 6-step procedure for frontend API mocking
- **CLAUDE.md**: added _work/ conventions, full agent/skill/script catalog, agent model overrides section
- **init-project.sh**: creates `_work/` structure, symlinks skills, creates hook-config.json and .claude/settings.json

### Fixed
- **Git grep escaping bug**: 4 enforcement scripts had unescaped `[sc-{id}]` in `--grep` (matched all commits instead of specific story)

### Summary
- Agents: 11 → 19 (all with .ref.md companions)
- Skills: 5 → 10
- Enforcement scripts: 3 → 9
- Hooks: 1 → 2
- Documentation files: 1 → 7
- Templates: 5 → 8

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
