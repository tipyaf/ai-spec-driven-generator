# Validator Reference — Report Templates & Anti-Patterns

## Validation Report Template

```markdown
# Validation Report

## Summary
- **Status**: PASS / FAIL
- **Spec**: [spec name]
- **Branch**: [branch name]
- **Date**: [date]

## Visual Checks
| Page | Check | Status | Evidence |
|------|-------|--------|----------|
| /parametres | Design system colors | PASS | Screenshot attached, no hardcoded colors |
| /parametres | Card readability | FAIL | Blue text on grey bg, contrast ratio 2.1:1 |

## Code Checks
| File | Check | Status | Evidence |
|------|-------|--------|----------|
| page.tsx | No hardcoded colors | FAIL | Line 112: `text-blue-800` found |
| page.tsx | i18n keys used | PASS | All strings use t() |

## Runtime Checks
| Endpoint | Check | Status | Evidence |
|----------|-------|--------|----------|
| GET /api/chat | Returns data | PASS | 200 OK, valid JSON |

## Acceptance Tests
| Test | Status | Evidence |
|------|--------|----------|
| "No blue- classes in email page" | FAIL | grep found 4 occurrences |

## Verdict
FAIL — 3 issues must be fixed before PR.

### Issues to fix
1. [file:line] description of issue
2. [file:line] description of issue
```

## Status Output Format

```
Phase 3.5 — Validator
Status: PASS / FAIL
- TypeScript compilation: PASS/FAIL
- Existing tests: PASS/FAIL
- Visual checks: PASS/FAIL
- Code checks: PASS/FAIL
- Runtime checks: PASS/FAIL
- Acceptance tests: PASS/FAIL
- Manifest check: PASS/FAIL
- Clean code check: PASS/FAIL
Next: Proceeding to Phase 4 / Returning to developer with N issues
```

## Default Anti-Patterns

### All project types
- Debug artifacts: `console.log`, `console.debug`, `debugger`
- Incomplete code: `TODO`, `FIXME`, `HACK`, `XXX`
- Unused imports
- Empty catch blocks

### Web projects only
- Hardcoded colors in UI components: `blue-`, `red-`, `green-`, `yellow-`, `gray-` (Tailwind color classes)
- Hardcoded CSS values instead of design system variables

### Projects with user-facing output (web, mobile, CLI, desktop)
- Hardcoded strings in UI (should use i18n)

## Lesson Format Template

```markdown
### [Category] Short title
**Problem**: [concrete description with file names]
**Root cause**: [why it happened]
**Rule**: [what to do instead]
```

Categories: UI, API, Testing, Validation, Security, Performance, i18n, Architecture, Deployment
