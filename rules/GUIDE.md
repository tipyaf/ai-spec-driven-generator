# GUIDE.md — Rules for every agent working in v5

Unified rules reference. Replaces the v4 set (`CLAUDE.md`, `coding-standards.md`,
`test-quality.md`, `agent-conduct.md`). Every agent MUST read this file (or the
1-page [`CHEATSHEET.md`](CHEATSHEET.md) for a recap) before acting.

For pipeline mechanics (commands, gates, scripts, state machine) see
[`../_docs/PIPELINE.md`](../_docs/PIPELINE.md).

---

## 1. Principles

These three principles apply to every agent, every phase, every action.

| Principle | What it means in practice |
|---|---|
| **Agnostic** | Core framework is Python + YAML. Project stack-awareness lives in `_work/stacks/`. Check `spec.type` before applying platform-specific rules (WCAG only for `web-ui`/`mobile`, OWASP patterns adapt per stack profile). Never assume "web". |
| **Autonomous** | Humans decide (product, UX, architecture, go-live). Machines verify (tests, quality, security, performance). Auto-proceed when gates pass. Escalation after 3 failed cycles is **bloquante** — only `/resume <story-id> "reason"` clears it. |
| **Accompaniment** | Guide and challenge the user. Every human-validated phase ends with clear options, trade-offs, next steps. `/help [command]`, `/status`, `/next`, messages unifiés via `scripts/ui_messages.py`. No silent execution. Respond in the user's language. |

---

## 2. Coding standards (language-agnostic)

Stack profiles in `_work/stacks/<stack>/profile.yaml` may override with
language-specific rules. In the absence of an override, the rules below apply.

### 2.1 SOLID

| Principle | Rule |
|---|---|
| **SRP** | Router = HTTP; Service = business logic; Repository = persistence; Model = data + invariants. No cross-layer leakage. |
| **OCP** | Extend via new modules. Adding a payment method must not require editing existing payment code. |
| **LSP** | No `NotImplementedError` in production. Subtypes are drop-in. |
| **ISP** | Small focused interfaces. 10-method interface where 3 are used → split. |
| **DIP** | Depend on abstractions via DI. Never instantiate deps inside the class that uses them. |

### 2.2 KISS / DRY / YAGNI

- **KISS**: 3 similar lines beat a premature abstraction. Extract at the third
  occurrence (UI components: at the second — see §2.5).
- **DRY**: shared logic in one place. Models = source of truth for shapes
  (Pydantic, Zod, TS types, Go structs). Fixtures in shared setup.
- **YAGNI**: build only what the current story requires. No speculative params,
  no "future flexibility" abstractions, no pagination/caching/rate-limiting
  unless asked.

### 2.3 Readability gates (hard — fail the review)

| Check | FAIL if |
|---|---|
| Function length | > 40 lines |
| Nesting depth | > 3 levels |
| Cyclomatic complexity | > 10 per function |
| File length | > 400 lines |
| Function parameters | > 5 (use options object) |
| Naming | `x`, `tmp`, `data`, `result` without context |
| Dead code | Commented-out blocks, unresolved TODO/FIXME/HACK |
| Duplication | Same logic 3+ times |

### 2.4 Error handling

- Never swallow errors. Empty `catch` blocks are forbidden.
- Typed errors (classes/discriminated unions), not string messages.
- Fail fast at boundaries (API entry, CLI args, config load).
- Never expose stack traces in API responses — log server-side only.

### 2.5 UI component architecture (web-ui, mobile)

Every UI component is classified **Smart** (container, state, fetching) or
**Dumb** (presentational, props in → UI out).

| Rule | FAIL if |
|---|---|
| Reuse before create | New dumb component created where an existing one could be parameterized |
| No logic in dumb components | Dumb imports a service, store, API client, router |
| No markup in smart components | Complex rendering lives in smart instead of delegating to dumb |
| Extract at the 2nd occurrence | UI duplication causes visual drift faster than logic duplication |
| Shared dumbs in shared dir | Dumb used by 2+ features lives in a feature folder |

### 2.6 Anti-patterns (always wrong, every language)

Mutable global state · circular deps · callback hell · god objects (>10 methods
or >500 lines) · SQL string interpolation · catching bare `Exception` without
re-raise · magic numbers/strings in business logic · direct I/O in business logic
· sync blocking in async context · `any`/`Object`/`interface{}` without
justification.

### 2.7 API design (REST, when applicable)

Plural lowercase kebab-case nouns · correct HTTP verbs · status codes per RFC ·
typed response models · pagination with maximum · PUT/DELETE idempotent · all
endpoints versioned (`/api/v1/...`).

---

## 3. Test quality

Every agent that writes, reviews, or evaluates tests reads this section before
touching tests. Tests are verified by 4 gates: G2, G2.1 (mutation), pre-commit
scripts, and G5/G6.

### 3.1 Rule 1 — Tests call real production code

- Every test imports and invokes the real function / endpoint / component. No
  fixture-shape tests, no inline arithmetic, no assertion on mock return values.
- `.skip()` and `.todo()` are not tests. Use `xfail` with a `BUG: …` reason.
- **API mocks return what the backend sends**, not what the frontend expects.
  Read the backend router, find `response_model=X`, list every field, write the
  mock. MSW 6-step procedure is enforced by `check_msw_contracts.py`.
- Follow the plan. If the story says "test X, assert Y", you test X and assert Y.
- If 100% of bug-catching tests pass on first write, stop — at least one is
  wrong.

### 3.2 Rule 2 — Oracle computation (every numeric assertion shows its math)

Every numeric assertion on a **computed** value MUST have an `# ORACLE:` comment
block within 5 lines above it. The block shows the formula, the substitution
with concrete values, and the expected result.

```python
# ORACLE: fees_pct = total_fees / (entry_price * qty) * 100
#         = 2.20 / (100.00 * 10) * 100
#         = 0.22
assert result.fees_pct == pytest.approx(Decimal("0.22"), abs=Decimal("0.01"))
```

**Requires ORACLE**: computed fields (financial values, percentages, ratios,
totals, scores, averages, weighted values).
**Does NOT require ORACLE**: status codes, array lengths, boolean checks, string
equality, UUID comparisons, enum values.

Oracle values come from the story's `test_intentions:` section (`/refine` writes
them). If missing: the agent computes from the spec's business rules and shows
the math.

Enforced by `check_oracle_assertions.py` which **evaluates** the comment in a
sandbox: `# ORACLE: x = 42` then `assert result == 42` — if `x` doesn't actually
equal 42 under the declared formula, the commit is blocked.

### 3.3 Rule 2b — Weak assertion banlist

Banned as terminal/sole assertions on computed result fields:

| Category | Example | Why it's useless |
|---|---|---|
| **Existence-only** | `!= null`, `is not None`, `toBeDefined()` | Passes for `{}`, `0`, `""` |
| **Non-empty-only** | `len(x) > 0`, `.length > 0` | Passes with 1 item when we expected 10 |
| **Type-only** | `isinstance(x, dict)`, `toBeInstanceOf(Object)` | Passes for any instance, even empty |
| **Bare truthiness** | `assert x`, `toBeTruthy()` | `0` is falsy, `"error"` is truthy |
| **Status-code-only** | `status == 200` without body | Never checks data shape |

Legitimate as **guard** before a real value assertion, or for auth rejections
(401/403/404 without body). Never as the sole assertion on a computed field.

### 3.4 Rule 3 — Cover every layer

For each store the feature touches: verify a test calls the real **write**
function (not a fixture insert) and a test calls the real **read** endpoint and
a test verifies the **display** renders real data. Test the chain, not the link.

### 3.5 Rule 4 — Coverage audit before writing tests

Before writing a single test:
1. Enumerate data stores and identify which have production writers (grep
   INSERT/UPDATE/save/add/create).
2. Enumerate endpoints and trace their data source.
3. Enumerate pages/screens and trace their API source.
4. Produce a coverage matrix. Every gap becomes a failing test.
5. If 20+ gaps: batch 10–15 tests, run, fix, repeat.

Enforced by `check_coverage_audit.py` (AST-based in v5: resolves f-strings,
dynamic routes, computed constants).

### 3.6 Rule 5 — Backend test quality gates

Integration tests present (real DB, not mocked) · every endpoint covered · every
endpoint declares response model · auth enforced (401 test per protected
endpoint) · write-path tested · no fixture-only coverage · zero test files on a
backend story = FAIL.

### 3.7 Rule 6 — Frontend test quality gates

Source-file assertions are banned · API stories require MSW-based behaviour
tests · error states and loading states tested (warning, not fail).

### 3.8 Rule 7 — Invariant guards

Business invariants ("completed order total > 0", "closed account balance = 0")
enforced as post-test hooks (`autouse=True` fixture in pytest, `afterEach` in
vitest). Fixtures that set computed values carry an ORACLE block proving the
values match production formulas.

### 3.9 Rule 8 — `test_intentions:` is the spec

When the story file contains `test_intentions:`, every intention MUST become a
test. Inputs → test setup; oracle → `# ORACLE:` block; assertions → asserts;
edge_cases → parametrized cases. Never change the oracle values — if the code
produces a different number, the code has a bug (use xfail).

For UI rendering (Trigger C), intentions cover null display, date formatting,
currency formatting, negative values, enum labels, empty collections, unicode.
No arithmetic — the oracle is the expected display string.

### 3.10 Rule 9 — Test quality tools

**Mutation testing** (G2.1): mutmut/stryker/go-mutesting/cargo-mutants/pitest.
Score ≥ 80% on changed files.
**LLM fault scenarios**: wrong field, missing accumulation, off-by-one scaling,
null propagation, stale state, wrong aggregation, boundary confusion, type
coercion.
**Ensemble assessment**: STRONG / WEAK / USELESS. USELESS rewritten before
proceeding.
**Schema fuzzing**: Schemathesis vs OpenAPI for APIs.
**Property-based**: Hypothesis / fast-check / gopter for calculations and pure
logic.

### 3.11 Hard constraints (every test-writing agent)

- NEVER `.skip()` / `.todo()`
- NEVER fixture-shape tests
- NEVER API mocks matching frontend expectations instead of backend schema
- NEVER insert fixture data without a corresponding production-writer test
- NEVER commit without running tests
- ALWAYS run coverage audit before writing tests
- ALWAYS follow the story file exactly
- ALWAYS run `check_*` scripts; all must pass before commit
- ALWAYS run mutation testing when available
- NEVER assert a computed value without ORACLE
- NEVER skip a `test_intention`
- NEVER change oracle values from `test_intentions`
- NEVER use Rule 2b banned assertions as terminal assertions on computed values

---

## 4. Agent conduct (shared across all 18 agents)

### 4.1 Never do another agent's job

| Task | Skill | NEVER do it manually |
|---|---|---|
| Refining a feature | `/refine` | Don't rewrite story files outside the skill |
| Building a feature | `/build` | Don't write code outside the build pipeline |
| Validating | `/validate` | Don't run `verify:` commands outside the validator |
| Reviewing | `/review` | Don't manually audit ACs |
| Shipping | `/ship` | Don't `gh pr create` by hand — the PR loses its tag |

Manually doing an agent's job skips gates and produces uncertified code.

### 4.2 Check state before acting

Before any operation on a feature, read `specs/feature-tracker.yaml` and verify
the state is valid for the operation (see state machine in PIPELINE.md §10).
`escalated` and `tampered` are terminal until `/resume`.

### 4.3 Read the playbook, prove you read it

Read the ENTIRE agent playbook before acting. **Output a numbered step list**
before starting — the visible checkpoint the user can verify. Follow steps in
order. Complete every mandatory step before reporting done.

### 4.4 Never rubber-stamp existing work

If code is already committed, diff it against the CURRENT spec and rules. Specs
and rules evolve; stale code against new specs produces false PASS verdicts.

### 4.5 Stop and ask when uncertain

If unsure whether a change is in scope, whether a test failure is pre-existing,
or whether the user wants you to act or investigate — ASK. Do not guess.

### 4.6 Run enforcement scripts before every commit

The pre-commit hook installed by `scripts/setup-hooks.sh` runs them
automatically, but an agent that writes code also runs them manually:

```bash
python3 scripts/check_write_coverage.py --config test_enforcement.json
python3 scripts/check_oracle_assertions.py --backend --config test_enforcement.json
python3 scripts/check_test_quality.py --backend --config test_enforcement.json
```

Any non-zero exit → STOP. Fix the violation. Do not `--no-verify`.

### 4.7 Create and respect the implementation manifest

`specs/stories/<id>-manifest.yaml` declares the scope: files to read, modify,
create. Phase 1 is the skeleton, Phase 2 is the post-exploration plan. **Never
modify files not declared** — G7 checks `git diff` against the manifest.

### 4.8 TDD gates are run by the orchestrator, not self-certified

An agent saying "I verified" is not evidence. Only the script exit code is.
Orchestrator runs:

| Gate | Script |
|---|---|
| After RED | `check_red_phase`, `check_test_intentions`, `check_coverage_audit`, `check_msw_contracts` |
| After GREEN | `check_test_tampering`, `check_tdd_order`, `check_story_commits` |

### 4.9 Inform the user of every step in real-time

Every agent communicates each step: "Starting RED — writing unit tests…",
"Gate 1 Security — PASS ✓", "Gate 2 Unit Tests — FAIL ✗ (3 failures)", "Fixing
failures, returning to builder…". No silent execution. Messages go through
`scripts/ui_messages.py` helpers (`success`, `fail`, `next_step`, `escalation`).

### 4.10 Respond in the user's language

Framework files (agents, skills, rules, scripts, templates) are in English.
Agent outputs (status messages, questions, explanations) are in the user's
language.

### 4.11 Tools are optional — no hard dependencies

Tools are suggested, not imposed. `/spec` (architecture phase) proposes them; the
user decides. Exceptions: **G3 code quality requires a tool** — no subjective
fallback in v5. `/build` refuses to start if no tool is configured and suggests
by stack.

### 4.12 `data-testid` contract (web-ui, mobile)

Wireframe HTML defines `data-testid` on every interactive element and
significant content zone. Production code reproduces them exactly. E2E tests
target them. Any mismatch = G9.2 FAIL.

### 4.13 Specs are the absolute source of truth

With or without a PM tool, `specs/` is the authoritative product contract. The
product can be rebuilt from the specs alone. PM tools mirror, they never
replace. If specs and PM tool disagree, specs win.

---

## 5. Commits (atomic, story-linked, TDD-ordered)

### 5.1 Atomic story commits

All story artifacts (story file, manifest, implementation code, tests,
wireframes) are committed in a **single atomic commit** AFTER all gates pass.
No commits during `/refine`. No commits during `/build` until the orchestrator
has run the gates.

```
/refine   → writes files to working tree (NO commit)
/build    → writes code + tests (NO commit until gates pass)
gates     → ALL PASS
→ single git commit: story + manifest + tracker + code + tests + wireframes
```

The orchestrator creates the commit. The agent does not call `git commit`
directly.

### 5.2 Never `git add .` or `git add -A`

Name files explicitly. `git add .` risks staging `.env`, credentials, temp
files, or unrelated changes.

### 5.3 TDD order

RED commit precedes GREEN commit in git history. Enforced by
`check_tdd_order.py`. Between RED and GREEN, `check_test_tampering.py` runs an
AST diff — any assertion removed is flagged, even if two are added.

### 5.4 Commit messages in English

Commit messages, PR titles, PR descriptions MUST be in English regardless of the
user's conversational language. Conventional-commit prefixes (`feat:`, `fix:`,
`refactor:`, `chore:`, `docs:`, `test:`) are recommended.

### 5.5 Story association

Every production-code commit carries a story reference
(`[sc-0012]` tag, or `story: sc-0012` trailer). `check_story_commits.py`
blocks production code staged without a matching story file + manifest +
tracker update.

---

## 6. Git flow

### 6.1 Branches

| Branch | Role | Merges into |
|---|---|---|
| `main` | Production — releases only (CHANGELOG, VERSION, tag) | — |
| `develop` | Integration — all feature work merges here first | `main` at release time |
| `feat/*` | One branch per feature | `develop` after `/ship` PASS |

If the project uses trunk-based dev, replace `develop` with `main` throughout —
the framework adapts.

### 6.2 Rules (never violate)

- All feature branches start from the integration branch: `git checkout -b feat/XXX origin/develop`
- All PRs target the integration branch: `gh pr create --base develop`
- `main` is read-only for agents; only release PRs merge into `main`
- No cherry-picks between branches — missing code = needs a release

### 6.3 Enforcement hooks (blocking)

Installed by `scripts/setup-hooks.sh`:

| Hook | Blocks | Exception |
|---|---|---|
| `pr-base-branch-guard` | `gh pr create --base main` | Current branch is `release/*` |
| `push-to-main-guard` | `git push origin main` | None |
| `branch-origin-guard` | `git checkout -b feat/X origin/main` | None — branch from `origin/develop` |

Do not bypass. Fix the command.

### 6.4 Bypass detection

`--no-verify`, weakened assertions, commits without a story → `check_story_commits`
+ `check_test_tampering` (AST diff between SHAs, not between staged/HEAD) flag
them at the next `/build`, `/validate`, or `/ship`. Story moves to `tampered`.
Only `/resume <story-id> "reason"` unblocks.

### 6.5 Worktree rule — parallel work isolation

On `feat/sc-123` and asked to work on sc-456: create a worktree.

```bash
git worktree add .worktrees/feat-sc-456 -b feat/sc-456 origin/develop
# work there
git worktree remove .worktrees/feat-sc-456
```

Worktrees live in `.worktrees/` (gitignored). Branch from `origin/develop`. One
worktree per task. Clean up after merge. Never mix changes from different
stories on the same branch.

### 6.6 The `/ship` contract

The dev never runs `gh pr create` manually. `/ship` is the single exit:

1. `/ship <story-id>` runs `/review` internally — all applicable gates replayed
   on the complete branch.
2. One gate FAIL → no PR. Detailed report returned.
3. All gates PASS → push + `gh pr create` via `release-manager`. PR title and
   description generated from story + manifest + `_work/build/<id>.yaml`
   (attached as evidence). Tag: `sdd-validated-v5`.
4. Manual `gh pr create` produces an untagged PR — caught at human review.

**Contract**: until `/ship` emits `PR CREATED` with the `sdd-validated-v5` tag,
the code has not earned the right to leave the dev's machine.

---

## 7. Strict rules (top-level, every agent)

1. Always read memory at session start (`memory/<project>.md` + `LESSONS.md` +
   `feature-tracker.yaml`).
2. Always update memory and tracker at each state transition.
3. Always follow phase order (the filesystem enforces it).
4. Never load all agents — skills load what they need.
5. Never over-engineer — the spec, nothing more.
6. Never code before conception phases (spec + arch + tracker) exist.
7. Never skip `verify:` commands.
8. Always run enforcement scripts before committing.
9. Never assert computed values without ORACLE.
10. Never skip a `test_intention`.
11. Never mix branches — unrelated work goes in a worktree.
12. All PRs target the integration branch (never `main` except releases).
13. Commit messages / PR titles in English, user-facing messages in the user's
    language.
14. `/ship` is the only way out — never `gh pr create` manually.

---

## See also

- [`CHEATSHEET.md`](CHEATSHEET.md) — 1-page TL;DR of this guide.
- [`../_docs/PIPELINE.md`](../_docs/PIPELINE.md) — commands, gates, agents,
  scripts, state machine.
- [`CLAUDE.md.template`](CLAUDE.md.template) — copied into each project by
  `scripts/init-project.sh`.
- [`commands/`](commands/) — per-skill reference cards.
