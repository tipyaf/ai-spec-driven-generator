# Agent Conduct Rules

**Every agent MUST read this file before doing ANY work. Skills load it automatically.**

**This file is the SINGLE SOURCE OF TRUTH for cross-agent rules.** Agent playbook STOP headers
are brief reminders pointing here. Playbook Hard Constraints sections contain agent-specific
rules. If a rule here conflicts with a playbook, THIS FILE WINS.

These rules exist because agents repeatedly violated them despite the rules being
documented in playbooks. This file is the enforcement mechanism -- short, impossible
to miss, loaded before the playbook.

---

## Rule 1: Never do another agent's job

| If the task is... | Use this skill | NEVER do it manually |
|-------------------|---------------|---------------------|
| Refining a feature (rewriting description, ACs, scope) | /refine | Do not rewrite story files yourself |
| Building a feature (writing code, tests) | /build | Do not write code outside the build pipeline |
| Reviewing a feature (checking ACs against code) | /review | Do not manually verify ACs without the reviewer |
| Validating a feature (running verify: commands) | /validate | Do not run verify: commands outside the validator |

**Why**: manually doing an agent's job skips quality gates (testability gate, test
intentions, stack profile injection, code review, validator, security audit). The
result looks correct but is not certified.

---

## Rule 2: Always check feature state before acting

Before ANY operation on a feature, read `specs/feature-tracker.yaml` and verify the state is valid:

| Operation | Required state | If wrong state |
|-----------|---------------|----------------|
| /refine | `pending` | If `building`/`testing`/`validated`: STOP and warn user "Feature X is already in progress -- re-refining will invalidate the build pipeline. Proceed?" Wait for explicit yes. |
| /build | `refined` | If `building`/`testing`: warn user and wait for confirmation. If `validated`: stop. |
| /validate | `building` or `testing` | If `pending`/`refined`: stop and tell user to build first. |
| /review | ALL features `validated` | If any feature not validated: stop and list which ones. |

**Why**: refining a feature that's already building or validated undoes the build,
validation, security audit, and review work. Building a feature that's already
validated without warning wastes time.

---

## Rule 3: Read the playbook FIRST, act SECOND -- prove you read it

The skill file tells you to read an agent playbook. You MUST:
1. Read the ENTIRE playbook file
2. Identify ALL steps (not just the first few)
3. **Output a numbered step list before starting** -- this proves you read the playbook and
   creates a visible checkpoint the user can verify. Format:
   ```
   Playbook steps for this task:
   1. Read story file and gather context
   2. Check dependencies
   3. ...
   ```
4. Follow steps IN ORDER -- do not skip, merge, or reorder
5. Complete EVERY mandatory step before reporting done

**Why**: agents read long playbooks and then forget later steps.
Every step exists because skipping it caused a production failure. The step list
output is the enforcement mechanism -- if you can't list the steps, you didn't read them.

---

## Rule 4: Never rubber-stamp existing work

If code is already committed for a feature:
- You MUST still diff it against the CURRENT spec and quality rules
- "Code already exists" is NEVER a reason to skip the build pipeline
- If specs or rules changed since the code was written, update the code/tests

**Why**: specs evolve, quality rules evolve. Validating stale code against new specs
without checking for gaps produces false PASS results.

---

## Rule 5: Stop and ask when uncertain

If you're unsure whether:
- A feature needs refinement or just a quick edit
- Code changes are in scope or out of scope
- A test failure is pre-existing or caused by your changes
- The user wants you to act or just investigate

**ASK. Do not guess. Do not proceed hoping you're right.**

---

## Rule 6: Run enforcement scripts before every commit

Before committing ANY code or tests, run ALL enforcement scripts:

```bash
python scripts/check_write_coverage.py --config test_enforcement.json
python scripts/check_oracle_assertions.py --backend --config test_enforcement.json
python scripts/check_test_quality.py --backend --config test_enforcement.json
```

For frontend changes, use `--frontend` instead of `--backend`.

**If ANY script exits non-zero: STOP. Fix the violation. Do not commit.**

These scripts check:
- **Write coverage**: every data store with a read endpoint must have production code that writes to it
- **Oracle assertions**: every numeric assertion on a computed value must have an `# ORACLE:` comment showing step-by-step math
- **Test quality**: no .skip(), no mock-soup in integration tests, no fixture-only tests, no existence-only assertions (Rule 2b banlist)

This applies to EVERY agent that writes code or tests (developer, tester, reviewer auto-fixes).

**Why**: agents repeatedly wrote tests that passed but caught zero bugs. These scripts
are the only reliable enforcement mechanism -- markdown rules get ignored, scripts block commits.

---

## Rule 7: Create and respect the implementation manifest

Before writing ANY code for a feature:

1. Copy `specs/templates/manifest-template.yaml` to `specs/stories/[feature-id]-manifest.yaml`
2. Fill Phase 1 (skeleton): scope, artifacts, ac_verifications, anti_patterns
3. Read the codebase, then fill Phase 2 (complete): files_to_read, files_to_modify, files_to_create
4. Set `phase: "complete"` — only then start coding
5. **NEVER modify files not declared in the manifest** — the reviewer and validator will FAIL you

After coding:
6. Update `pipeline_steps` with actual steps completed
7. Add `deployment_note` if applicable

**Why**: without a manifest, the developer can modify files outside scope, and the reviewer has
no reference for scope enforcement. The manifest is the build contract that the validator and
reviewer consume to verify completeness and scope compliance.

---

## Rule 8: TDD gates are run by the orchestrator, not self-certified

An agent saying "I verified" is NOT evidence. The script exit code IS evidence.

| Gate | Script | Who runs it |
|------|--------|-------------|
| After RED | `check_red_phase.py` | Orchestrator |
| After RED | `check_test_intentions.py` | Orchestrator |
| After RED | `check_coverage_audit.py` | Orchestrator |
| After RED | `check_msw_contracts.py` | Orchestrator |
| After GREEN | `check_test_tampering.py` | Orchestrator |
| After GREEN | `check_tdd_order.py` | Orchestrator |

TDD gates are machine-enforced. The orchestrator runs enforcement scripts at each gate
boundary. Agents cannot self-certify -- only the script exit code is trusted.

**Why**: agents will claim tests pass without running them, or claim they verified quality
without the enforcement script. Trust the exit code, not the prose.

---

## Rule 9: Enforcement scripts are non-negotiable

Every enforcement script in `scripts/` (or `ai-framework/scripts/`) is a hard gate. No agent
may skip, defer, or work around an enforcement script. If a script exits non-zero, the pipeline
stops until the violation is fixed.

This applies to ALL scripts:
- `check_red_phase.py` -- tests must fail in RED phase (no trivial failures, real production imports)
- `check_test_intentions.py` -- every spec intention must have a matching test
- `check_coverage_audit.py` -- every endpoint/table/component must be tested
- `check_msw_contracts.py` -- MSW handlers must use backend field names
- `check_test_tampering.py` -- no deleted or weakened tests after GREEN phase
- `check_tdd_order.py` -- RED commit must precede GREEN commit in git history
- `check_test_quality.py` -- no .skip(), no mock-soup, no fixture-only tests
- `check_write_coverage.py` -- tables with readers must have tested writers

**Why**: every workaround that bypasses a script creates a class of bugs that the script was
designed to prevent. The scripts exist because agents found creative ways to satisfy the letter
of the rule while violating its spirit.

---

## Rule 10: Read the playbook before acting -- no exceptions

Before performing ANY work, the agent MUST read its full playbook file. This is not optional
and not satisfied by "I already know the steps." The playbook may have been updated since the
last session. The agent must:

1. Read the ENTIRE playbook (not just the first section)
2. Identify the "Read Before Write" section and follow it completely
3. Check for any anti-patterns or lessons specific to this task
4. Only then begin executing

If the skill file says "read agent playbook X," that is a blocking instruction. Do not proceed
until the playbook has been read in full and its steps have been listed (see Rule 3).

**Why**: agents skip playbook sections they consider irrelevant and then miss critical steps.
The playbook is the contract. Reading it is not a suggestion.

---

## Rule 11: Never use `git add .` or `git add -A`

Always name files explicitly when staging for commit:
```bash
# CORRECT:
git add specs/stories/auth.yaml
git add src/auth/service.py

# FORBIDDEN:
git add .
git add -A
```

**Why**: `git add .` can stage sensitive files (.env, credentials), large binaries, temporary
files, or unrelated changes. Explicit file names ensure the commit contains exactly what was
intended and nothing more.

---

## Rule 12: Commit atomically after build validation

All story artifacts (story file, manifest, implementation code, tests, wireframes) are committed
in a **single atomic commit** AFTER all validation gates pass. No commits during the refine phase.
No commits during the build phase.

```
/refine → writes files to working tree (NO commit)
/build  → writes code + tests (NO commit)
validation gates → ALL PASS
→ single git commit: story + manifest + tracker + code + tests + wireframes
→ PR/MR created automatically
```

The story file and implementation code MUST be committed together. Committing them separately
risks losing the build contract if a session crashes between commits.

**Why**: specs ARE the product contract. If we lose the specs, we lose the product. Atomic
commits ensure the story file and its implementation are always in sync.

---

## Rule 13: Inform the user of every step in real-time

Every agent MUST communicate each step as it happens:
- **Phase transitions**: "Starting RED phase — writing unit tests..."
- **Gate results**: "Gate 1 Security — PASS ✓" / "Gate 2 Unit Tests — FAIL ✗ (3 failures)"
- **Corrections**: "Fixing 3 test failures, returning to builder..."
- **Skips**: "Gate 4 E2E Code — SKIPPED (non-UI project)"

No silent execution. The user sees progression in real-time.

**Why**: autonomy does not mean opacity. The user must be able to follow the pipeline and
intervene if something goes wrong. Silent execution erodes trust.

---

## Rule 14: Respond in the user's language

All framework files (agents, skills, rules, templates, scripts) are written in **English**.
But all agent outputs (status messages, questions, explanations, reports) MUST be in the
**user's language** (detected from their messages). If the user writes in French, respond
in French. If in English, respond in English.

**Why**: accompaniment means meeting the user where they are. Language barriers reduce trust
and comprehension.

---

## Rule 15: Tools are optional — never impose dependencies

The framework MUST NOT require specific tools. Tools are SUGGESTED, not imposed:

| Tool category | Framework behavior | If not configured |
|---------------|-------------------|-------------------|
| Code quality (SonarQube, etc.) | Use if configured | Reviewer 3-pass takes over (NEVER skip) |
| WCAG audit (Pa11y, axe-core, etc.) | Use if configured | UX agent manual checklist |
| E2E framework (Playwright, Cypress, etc.) | Use from stack profile | — |
| Test runner (Jest, Vitest, Pytest, etc.) | Use from stack profile | — |
| Compiler (tsc, mypy, go build, etc.) | Use from stack profile | — |
| PM tool (Shortcut, Jira, GitLab, etc.) | Use if configured | Specs = source of truth |
| PR/MR tool (gh, glab, az) | Detect on machine, memorize | Warn user, no auto-PR |

Tool suggestions happen during `/spec` (architecture phase). The user always decides.

**Why**: agnosticism is a core principle. Tools come and go. The framework must not create
hard dependencies on tools the user doesn't want or that may become obsolete.

---

## Rule 16: Use `data-testid` from wireframes in production code (UI projects)

For UI projects, wireframe HTML files define `data-testid` attributes on every interactive
element and significant content zone. This creates a contract:

```
Wireframe HTML → data-testid="login-form-email"
Production code → data-testid="login-form-email"  (MUST match exactly)
E2E tests → [data-testid="login-form-email"]       (selector)
```

The builder MUST reproduce the exact same `data-testid` values in production code.
The E2E tests target these identifiers. Any mismatch = Gate 7 FAIL (wireframe validation).

**Why**: this is the only reliable way to guarantee zero drift between design (wireframes),
implementation (code), and verification (E2E). Without this contract, each layer can diverge
silently.

---

## Rule 17: Specs are the absolute source of truth

With or without a PM tool, the specs (`specs/stories/`, `specs/[project].yaml`, `specs/[project]-ux.md`)
are the **absolute source of truth** for the product. The product can be rebuilt entirely from
the specs alone.

If a PM tool is configured, it is a **mirror** of the specs — never a replacement. The PM tool
provides convenience (boards, notifications, attachments) but does not hold authoritative data.

If the PM tool and specs disagree, **the specs win**.

**Why**: PM tools are external services that can change, be discontinued, or lose data.
The specs are version-controlled in the repository and travel with the code.
