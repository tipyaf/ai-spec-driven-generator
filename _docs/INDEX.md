# AI Spec-Driven Generator

**Version 4.1.0** -- [Changelog](../CHANGELOG.md)

> Reusable AI agent framework for spec-driven code generation with Claude Code.
> Full agent catalog, build lifecycle, and quality gates: [agents.md](agents.md)

---

## Agents

| Invoke with | Agent |
|-------------|-------|
| /spec | [product-owner.md](../agents/product-owner.md), [ux-ui.md](../agents/ux-ui.md), [architect.md](../agents/architect.md) |
| /refine | [refinement.md](../agents/refinement.md) |
| /build | [developer.md](../agents/developer.md) |
| /validate | [validator.md](../agents/validator.md) |
| /review | [reviewer.md](../agents/reviewer.md) |
| /ux | [ux-ui.md](../agents/ux-ui.md) |
| /migrate | (inline — runs `scripts/migrate-v3-to-v4.sh`) |

**Builder agents** (dispatched by /build):
[builder-service.md](../agents/builder-service.md) --
[builder-frontend.md](../agents/builder-frontend.md) --
[builder-infra.md](../agents/builder-infra.md) --
[builder-migration.md](../agents/builder-migration.md) --
[builder-exchange.md](../agents/builder-exchange.md)

**Quality agents** (run automatically):
[tester.md](../agents/tester.md) --
[test-engineer.md](../agents/test-engineer.md) --
[reviewer.md](../agents/reviewer.md) --
[security.md](../agents/security.md) --
[story-reviewer.md](../agents/story-reviewer.md)

**Ops agents:**
[devops.md](../agents/devops.md)

---

## Skills

| Skill | Description |
|-------|-------------|
| /spec | Define project: constitution, scoping, clarify, design, architecture |
| /refine | Break a feature into stories with verify: commands |
| /build | Implement from story file (dispatches to the right builder) |
| /validate | Execute verify: commands independently |
| /review | Final quality gate |
| /scan | Scan local changes only (staged + unstaged vs integration branch) |
| /scan-full | Full codebase SonarQube analysis with hotspots and trends |
| /sonar | SonarQube status dashboard |
| /ux | Run the UX designer agent |
| /migrate | Migrate or generate spec documents |

---

## Enforcement Scripts

| Script | Gate |
|--------|------|
| check_red_phase.py | RED: tests must fail, no trivial failures, production imports required |
| check_test_tampering.py | GREEN: no deleted tests, no weakened assertions |
| check_tdd_order.py | GREEN: RED commit must precede GREEN in git history |
| check_test_intentions.py | RED: every spec intention has a matching test |
| check_coverage_audit.py | RED: every endpoint/table/component has a test |
| check_msw_contracts.py | RED: MSW handlers use backend Pydantic field names |
| check_test_quality.py | Pre-commit: no .skip, no mock-soup, no fixture-only tests |
| check_oracle_assertions.py | Pre-commit: ORACLE blocks on numeric assertions |
| check_write_coverage.py | Pre-commit: every table with reader has a writer |
| check_story_commits.py | Pre-commit: atomic commit (story + manifest + tracker + code) |

---

## Documentation

| Document | What it covers |
|----------|----------------|
| [agents.md](agents.md) | Full agent catalog (19 agents), build lifecycle diagram, 11 quality gates |
| [process.md](process.md) | Story lifecycle: idea, refine (wireframes), build (TDD + 11 gates), review, done |
| [workflow.md](workflow.md) | Board conventions, build order, branch strategy, _work/ directory structure |
| [skills.md](skills.md) | Skill system: how skills are loaded, adding new skills, phase prerequisites |
| [sonarqube.md](sonarqube.md) | SonarQube: install, configure, generate tokens, run scans, troubleshoot |
| [test-methodology.md](test-methodology.md) | Two-loop test system: spec-to-oracle + mutation feedback |
| [token-costs.md](token-costs.md) | Token analysis: per-session budgets, waste, optimization roadmap |

---

## Templates

| Template | Purpose |
|----------|---------|
| [spec-template.yaml](../specs/templates/spec-template.yaml) | YAML spec template for new projects |
| [feature-tracker.yaml](../specs/templates/feature-tracker.yaml) | Per-feature state tracking |
| [story-template.yaml](../specs/templates/story-template.yaml) | Refinement output (build contract) |
| [manifest-template.yaml](../specs/templates/manifest-template.yaml) | Implementation manifest (2-phase build contract) |
| [build-template.yaml](../specs/templates/build-template.yaml) | Pipeline state tracker with gates (per story) |
| [spec-overlay-template.yaml](../specs/templates/spec-overlay-template.yaml) | Per-story spec overlay |
| [stack-profile-template.md](../stacks/stack-profile-template.md) | Stack profile template |

---

## Memory Templates

| Template | Copy to |
|----------|---------|
| [LESSONS.md.template](../memory/LESSONS.md.template) | memory/LESSONS.md in project root |
| [SYNC.md.template](../memory/SYNC.md.template) | memory/SYNC.md in project root |
| [memory-template.md](../memory/memory-template.md) | memory/[project-name].md |
