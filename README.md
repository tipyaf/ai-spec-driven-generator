# ai-spec-driven-generator

An AI framework that generates production-ready code from structured YAML specs. 19 specialized agents, 10 skills, 9 enforcement scripts, 7 quality gates. Works with **Claude Code** and **Cursor**.

## How it works

```
/spec       Human defines the product (constitution, scoping, UX, architecture)
     ↓
/refine     Break each feature into stories with verify: shell commands
     ↓
/build      TDD pipeline per story:
            RED (test-engineer writes failing tests)
          → GREEN (builder makes them pass)
          → 7 quality gates (all must pass to reach "validated"):
              Gate 1: Security     — OWASP + stack forbidden patterns
              Gate 2: Tests        — unit + e2e
              Gate 3: UI           — WCAG + wireframes (if UI project)
              Gate 4: AC Validation — execute every verify: command
              Gate 5: Code Review  — quality + scope conformity
              Gate 6: SonarQube    — scan + coverage (skipped if not configured)
              Gate 7: Story Review — story-reviewer verifies every AC
          → FAIL? fix + re-validate (max 3 cycles, then escalate to human)
     ↓
/review     Final cross-feature review (all features must be validated)
     ↓
Deploy + Release (human decision)

SonarQube also runs continuously via hook after each session.
```

## Principles

| Principle | Rule |
|-----------|------|
| **Agnostic** | Works with any language, any project type. Web, API, CLI, mobile, data pipeline, ML, embedded. Agents adapt based on `spec.type`. |
| **Autonomous** | Humans decide (product, UX, architecture, deploy). Machines verify (tests, review, security). Auto-proceed when gates pass, escalate after 3 failures. |
| **Accompaniment** | Guides the user at every step. Each phase ends with a clear "Next step" when manual action is required. Never leaves the user without guidance. |

## Quick start

### 1. Create a project

```bash
git clone https://github.com/tipyaf/ai-spec-driven-generator.git
cd ai-spec-driven-generator
./scripts/init-project.sh my-project /path/to/workspace
```

Creates: git submodule, `CLAUDE.md`, `_work/` directories, skills symlinks, hook config.

### 2. Open in Claude Code or Cursor

The AI reads `CLAUDE.md` and follows the framework workflow automatically.

### 3. Build

```
/spec                        # Define your project
/refine candidate-profile    # Break a feature into stories
/build candidate-profile     # TDD pipeline + 7 quality gates
/validate candidate-profile  # Re-run verify: commands independently
/review                      # Final review before PR
```

Additional skills:

```
/ux candidate-profile        # UX design (spec + YAML + HTML prototype)
/scan                        # SonarQube — local changes only
/scan-full                   # SonarQube — full repo + hotspots
/sonar                       # SonarQube — status dashboard
/migrate                     # Migrate v3.x project to v4.0
```

### 4. Configure SonarQube (optional)

```bash
cp framework/stacks/hooks/.env.example .env
```

```env
SONAR_TOKEN=squ_your_token_here
SONAR_HOST_URL=http://localhost:9000
SONAR_PROJECT_KEY=your-project-key
```

`.env` is gitignored. Each project can have its own config. Falls back to shell env vars (`~/.zshrc`).

> Full guide: [`_docs/sonarqube.md`](_docs/sonarqube.md)

### 5. Update the framework

```bash
cd my-project
git submodule update --remote framework
```

## What's enforced

### Quality gates (per story, sequential)

| Gate | What it checks | Blocks on |
|------|---------------|-----------|
| 1. Security | OWASP patterns, AC-SEC-* verify commands | Any violation |
| 2. Tests | Unit + e2e execution | Any failure |
| 3. UI | WCAG 2.1 AA, wireframe conformity | Non-conformance (UI projects only) |
| 4. AC Validation | Every `verify:` command from story file | Any command fails |
| 5. Code Review | Quality, scope (only files in story scope touched) | Issues found |
| 6. SonarQube | Scan + coverage report | New BLOCKER/CRITICAL (skipped if not configured) |
| 7. Story Review | Story-reviewer verifies every AC against code | Any AC fails |

### TDD enforcement (machine, not honor)

| Script | When | Blocks on |
|--------|------|-----------|
| `check_red_phase.py` | After RED | Tests pass, trivial failures, no production imports |
| `check_test_intentions.py` | After RED | Spec intentions without matching tests |
| `check_coverage_audit.py` | After RED | Endpoints/tables/components without tests |
| `check_msw_contracts.py` | After RED | MSW handlers using wrong field names |
| `check_tdd_order.py` | After GREEN | Code committed before tests |
| `check_test_tampering.py` | After GREEN | Deleted tests, weakened assertions |

### Pre-commit checks

| Script | Blocks on |
|--------|-----------|
| `check_test_quality.py` | `.skip()`, mock-soup, fixture-only tests |
| `check_oracle_assertions.py` | Numeric assertions without ORACLE math proof |
| `check_write_coverage.py` | Tables with readers but no tested writers |

### Additional enforcement

| Mechanism | What it does |
|-----------|-------------|
| **Filesystem phase gates** | Phase is "done" when its artefact exists on disk |
| **feature-tracker.yaml** | Per-feature state (pending → refined → building → validated) |
| **Implementation manifest** | Developer declares scope before coding, reviewer verifies git diff matches |
| **Cycle counter** | Max 3 validation cycles per feature, then human escalation |
| **Code review hook** | `code_review.py` — anti-patterns + external checks, JSON verdict |
| **Forbidden patterns** | Validator greps committed files against stack profile rules |
| **Stale detection** | Warns on stories stuck in "building" with no recent commits |
| **LESSONS.md** | Recurring failures auto-logged, read by all agents before starting |

## Agents (19)

| Agent | Role | Model |
|-------|------|-------|
| Product Owner | Scoping, spec writing, AC format | Sonnet |
| UX/UI Designer | Wireframes, flows, design system | Sonnet |
| Architect | Architecture, manifest, component inventory | Opus |
| Refinement | Story breakdown, verify: commands, AC-SEC/AC-BP | Opus |
| Developer | Code implementation (generic builder) | Opus |
| Validator | Independent verification, spec contract | Sonnet |
| Tester | Test writing, mutation testing | Opus |
| Reviewer | 3-pass code review + manifest scope | Opus |
| Security | OWASP Top 10 audit | Sonnet/Opus |
| DevOps | CI/CD, deployment | Sonnet |
| Test Engineer | TDD RED phase — failing tests before code | Opus |
| Spec Generator | YAML overlay merging to markdown | Sonnet |
| Story Reviewer | Per-story AC verification (Gate 7) | Sonnet |
| Builder (Service) | Backend: routers, services, repositories | Sonnet |
| Builder (Frontend) | Frontend: components, hooks, MSW contracts | Sonnet |
| Builder (Infra) | Docker, CI/CD, proxy config | Sonnet |
| Builder (Migration) | Database migrations (Alembic) | Sonnet |
| Builder (Exchange) | Safety-critical exchange integrations | Opus |
| Orchestrator | Dispatch builders, run gates, manage state | Opus |

Each agent has a core file (`agents/[name].md`) and a template file (`agents/[name].ref.md`). Skills load only the agents needed — never all at once.

## Project structure (after init)

```
my-project/
├── framework/              # Git submodule → this repo
├── _work/                  # Working artifacts (per-story state)
│   ├── spec/               #   Spec overlays (sc-0000-initial.yaml + per-story)
│   ├── build/              #   Pipeline state per story (gates, files, ACs)
│   ├── ux/                 #   UX artifacts (wireframes, prototypes)
│   └── stacks/             #   Project-specific stack profiles
├── specs/
│   ├── constitution.md     #   Non-negotiable project principles
│   ├── [project].yaml      #   YAML spec (source of truth)
│   ├── [project]-arch.md   #   Architecture plan
│   ├── feature-tracker.yaml #  Per-feature state tracking
│   └── stories/            #   Story files (build contracts)
├── memory/                 #   Project memory + LESSONS.md
├── apps/                   #   Application code
├── .claude/
│   ├── skills/             #   Symlinks → framework skills
│   └── settings.json       #   Hook configuration
├── .env                    #   SonarQube config (gitignored)
├── CLAUDE.md               #   AI rules (from framework template)
└── .cursorrules            #   Cursor rules
```

> Full framework file tree: [`_docs/INDEX.md`](_docs/INDEX.md)

## Documentation

| Document | Content |
|----------|---------|
| [`_docs/INDEX.md`](_docs/INDEX.md) | Navigation hub — all agents, skills, scripts, templates |
| [`_docs/agents.md`](_docs/agents.md) | Agent catalog with sequence diagram |
| [`_docs/process.md`](_docs/process.md) | Story lifecycle (idea → done) |
| [`_docs/workflow.md`](_docs/workflow.md) | Board conventions, Git Flow, `_work/` structure |
| [`_docs/skills.md`](_docs/skills.md) | Skills system guide |
| [`_docs/sonarqube.md`](_docs/sonarqube.md) | SonarQube setup, config, troubleshooting |
| [`_docs/test-methodology.md`](_docs/test-methodology.md) | Two-loop test approach (spec→oracle + mutation) |

## Contributing

Every improvement is a commit + PR on this repo. Projects get updates via `git submodule update --remote framework`.

## License

MIT
