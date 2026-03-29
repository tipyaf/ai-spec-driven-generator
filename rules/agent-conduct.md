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
- **Test quality**: no .skip(), no mock-soup in integration tests, no fixture-only tests, no weak-only assertions

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
