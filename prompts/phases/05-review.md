# Phase 5: Review

## Responsible agent
`reviewer`

## Objective
Analyze the project's overall quality and identify issues to fix. This phase is **auto-validated** — no human validation gate.

## Prerequisites
- Phase 4 (Test) validated
- Passing tests

## Validation mode
**Auto-validated.** The reviewer runs automated checks and decides pass/fail. If all checks pass, the orchestrator auto-proceeds to Phase 5.5 (Security). Human intervention is only required if the reviewer cannot resolve issues after 3 attempts.

## Instructions

You are in **Phase 5 — Review**. You must audit the project's complete code using automated checks.

### Step 1: Compliance review
1. Verify each spec feature is implemented
2. Verify the data model matches the spec
3. Verify conventions are followed

### Step 2: Quality review (automated)
1. Go through each code file
2. Identify dead, duplicated, overly complex code
3. Verify typing quality (no `any`, proper interfaces)
4. Verify error handling
5. Check for unused imports, dead code
6. Check for hardcoded strings (i18n violation)
7. Check for hardcoded colors/values (design system violation)

### Step 3: Security review (automated)
1. Look for OWASP Top 10 vulnerabilities
2. Verify secret management
3. Verify input validation
4. Audit dependencies

### Step 4: Performance review
1. Identify N+1 queries
2. Verify caching
3. Verify pagination
4. Identify potential memory leaks

### Step 5: Report
Produce the review report (see format in `agents/reviewer.md`)

### Step 6: Auto-fix or escalate
If issues are found:
1. **Auto-fixable issues** (unused imports, formatting, minor anti-patterns): fix automatically and re-verify
2. **Developer-fixable issues** (code logic, missing validation): delegate to `developer` agent, then re-run review
3. **Architecture-level issues**: escalate to human only if they require product/architecture decisions
4. Re-run tests after any corrections
5. If 3 review cycles fail, escalate to human with full reports

## Validation criteria (automated)
- [ ] Overall score >= B
- [ ] No unresolved critical issues
- [ ] No security vulnerabilities
- [ ] Tests still passing after corrections
- [ ] No anti-patterns from manifest
- [ ] No hardcoded user-facing strings (i18n)
- [ ] CSS variables used, no hardcoded colors (design system)
- [ ] No unused imports or dead code

## Auto-proceed rule
When ALL validation criteria above pass, the orchestrator **automatically proceeds** to Phase 5.5 (Security Audit) without waiting for human approval.
