# Phase 5: Review

## Responsible agent
`reviewer`

## Objective
Analyze the project's overall quality and identify issues to fix.

## Prerequisites
- Phase 4 (Test) validated
- Passing tests

## Instructions

You are in **Phase 5 — Review**. You must audit the project's complete code.

### Step 1: Compliance review
1. Verify each spec feature is implemented
2. Verify the data model matches the spec
3. Verify conventions are followed

### Step 2: Quality review
1. Go through each code file
2. Identify dead, duplicated, overly complex code
3. Verify typing quality
4. Verify error handling

### Step 3: Security review
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

### Step 6: Corrections
If critical or important issues are found:
1. List necessary corrections
2. Request user validation
3. Delegate corrections to the `developer`
4. Re-run tests after corrections

## Validation criteria
- [ ] Overall score >= B
- [ ] No unresolved critical issues
- [ ] No security vulnerabilities
- [ ] Tests still passing after corrections
