# Story Reviewer Agent — Reference

> This file contains templates and examples. Load only when needed.

---

## AC Verification Template

```markdown
## AC Verification — Feature: [feature-id]

### AC-FUNC-[FEATURE]-01: [Description]
- **Verdict**: Met / Not met / Not verifiable
- **Evidence**: `path/to/file.ts:42` — [description of what satisfies the AC]
- **Notes**: [any caveats]

### AC-FUNC-[FEATURE]-02: [Description]
- **Verdict**: Met
- **Evidence**: `src/services/portfolio.service.ts:15` — implements calculateTotal() with correct formula
- **Notes**: —

### AC-SEC-[FEATURE]-01: [Description]
- **Verdict**: Met
- **Evidence**: `src/middleware/auth.ts:8` — JWT validation on all protected routes
- **Notes**: —

### AC-BP-[FEATURE]-01: [Description]
- **Verdict**: Not met
- **Evidence**: `src/controllers/portfolio.controller.ts:30` — function exceeds 40 lines (62 lines)
- **Notes**: Split into smaller functions
```

---

## PASS/FAIL Report Template

### PASS Report
```markdown
## Story Review — [feature-id]

**Verdict: PASS**

### Summary
All acceptance criteria met. Code quality adequate. Test coverage sufficient.

### AC Results
| AC ID | Description | Verdict | Evidence |
|-------|-------------|---------|----------|
| AC-FUNC-FEAT-01 | Create portfolio | Met | portfolio.service.ts:15 |
| AC-FUNC-FEAT-02 | List portfolios | Met | portfolio.controller.ts:8 |
| AC-SEC-FEAT-01 | Auth required | Met | auth.middleware.ts:12 |
| AC-BP-FEAT-01 | Error handling | Met | portfolio.service.ts:45 |

### Test Quality
- Write-path check: PASS
- Integration tests: 12 present
- Source assertions: none found
- MSW mocks: from backend schemas

### Anti-pattern Scan
- Forbidden patterns scanned: 8
- Matches found: 0

**Review: PASS — 4/4 ACs — 2026-04-04 — abc1234**
```

### FAIL Report
```markdown
## Story Review — [feature-id]

**Verdict: FAIL**

### Summary
2 of 4 acceptance criteria not met. Missing integration tests for write path.

### AC Results
| AC ID | Description | Verdict | Evidence |
|-------|-------------|---------|----------|
| AC-FUNC-FEAT-01 | Create portfolio | Not met | No POST handler found |
| AC-FUNC-FEAT-02 | List portfolios | Met | portfolio.controller.ts:8 |
| AC-SEC-FEAT-01 | Auth required | Not met | /api/v1/portfolios has no auth guard |
| AC-BP-FEAT-01 | Error handling | Met | portfolio.service.ts:45 |

### Failing ACs — Details
1. **AC-FUNC-FEAT-01**: No POST /api/v1/portfolios endpoint found in committed code.
   Expected: `portfolio.controller.ts` with POST handler.
2. **AC-SEC-FEAT-01**: GET /api/v1/portfolios endpoint missing auth middleware.
   Expected: `@UseGuards(AuthGuard)` or equivalent decorator.

### Test Quality
- Write-path check: FAIL — portfolios table has no write-path test
- Integration tests: 4 present (insufficient)

### Anti-pattern Scan
- Forbidden patterns scanned: 8
- Matches found: 1 — `console.log` in portfolio.service.ts:22

**Review: FAIL — AC-FUNC-FEAT-01, AC-SEC-FEAT-01 — _work/build/feat-portfolio.yaml**
```

---

## Test Quality Checklist (for reviewer)

### Backend Stories
- [ ] Write-path check: every table served by a read endpoint has production write code
- [ ] Integration tests present (real HTTP client + real DB)
- [ ] Every endpoint has at least one test
- [ ] response_model declared on every endpoint
- [ ] status_code declared on every endpoint
- [ ] Auth 401 test per protected endpoint
- [ ] No fixture-shape tests (no mock-soup)
- [ ] API contract alignment (Pydantic schema matches response)

### Frontend Stories
- [ ] No source assertions (no `container.innerHTML` checks)
- [ ] MSW behavior tests for API-connected components
- [ ] MSW mocks derived from backend Pydantic shapes (not frontend types)
- [ ] Error states tested (loading, error, empty)
- [ ] No `.skip()` or `.todo()` in test files

---

## Recurring Failure Log Entry Format

```markdown
[2026-04-04] [AC-SEC] [missing-auth-guard]: Protected endpoint deployed without auth middleware.
Stories: feat-portfolio, feat-dashboard. Count: 2.
Action: refinement agent should auto-add AC-SEC for auth on every new endpoint story.
```
