# Reviewer Reference — Templates, Checklists & Report Format

## Review Verdict Format

```markdown
## Code Review — [story/PR title]

**Verdict: PASS / FAIL**

### Pass 1: KISS & Readability
| Check | Status | Evidence |
|-------|--------|----------|
| Function length | PASS | All functions < 40 lines |
| ... | ... | ... |

### Pass 2: Static Analysis
| Check | Status | Evidence |
|-------|--------|----------|
| Linting | PASS | 0 errors, 0 warnings |
| ... | ... | ... |

### Pass 3: Safety & Correctness
| Check | Status | Evidence |
|-------|--------|----------|
| Secrets | PASS | No hardcoded secrets found |
| ... | ... | ... |

### Issues to fix (if FAIL)
1. [file:line] description
2. [file:line] description
```

---

## Review Checklist

### 1. Spec compliance
- [ ] All spec features are implemented
- [ ] Acceptance criteria are met
- [ ] Data model matches the spec
- [ ] API endpoints match the spec
- [ ] Naming conventions are followed

### 2. Code quality
- [ ] No dead or commented-out code
- [ ] No unnecessary duplication
- [ ] Short functions (< 30 lines ideally)
- [ ] Reasonable file sizes (< 300 lines)
- [ ] Clear and descriptive naming
- [ ] Well-defined types/interfaces (no `any`)
- [ ] Organized imports without circular references

### 3. Security
- [ ] No hardcoded secrets (API keys, passwords)
- [ ] User inputs validated and sanitized
- [ ] Parameterized SQL queries (no concatenation)
- [ ] Security headers configured (CORS, CSP, etc.)
- [ ] Correct authentication/authorization
- [ ] No sensitive data in logs
- [ ] Dependencies without known vulnerabilities

### 4. Performance
- [ ] No N+1 queries
- [ ] Pagination for lists
- [ ] Indexes on frequently queried fields
- [ ] No heavy computations in the render path
- [ ] Optimized assets (images, bundles)
- [ ] Appropriate caching

### 5. Tests
- [ ] Sufficient test coverage (> 80%)
- [ ] Relevant tests (not just for coverage)
- [ ] Edge cases covered
- [ ] Deterministic tests

---

## Output Report Format

```markdown
## Code Review Report

### Overall score: [A/B/C/D/F]

### Summary
[2-3 sentences summarizing overall quality]

### Issues found

#### Critical (must fix)
1. **[File:line]** — [Problem description]
   - Impact: [what can go wrong]
   - Fix: [how to fix]

#### Important (strongly recommended)
1. **[File:line]** — [Description]
   - Fix: [how to fix]

#### Minor (suggestions)
1. **[File:line]** — [Description]

### Positive points
- [what is well done]

### Metrics
| Metric | Value | Threshold |
|--------|-------|-----------|
| Test coverage | XX% | > 80% |
| Max cyclomatic complexity | XX | < 10 |
| Longest file | XX lines | < 300 |
| Dependencies | XX | reasonable |
```

---

## Detailed Auto-Validation Pipeline

### 1. Anti-pattern detection
- No anti-patterns from the project manifest (`specs/*.yaml` forbidden patterns)
- No `console.log`, `debugger`, or debug artifacts in production code
- No `any` type in TypeScript (unless explicitly justified in spec)
- No TODO/FIXME/HACK comments left unresolved

### 2. Project conventions
- File naming follows project conventions (kebab-case, PascalCase components, etc.)
- File structure matches the architecture plan from Phase 1
- Import organization: no circular dependencies, no unused imports
- Export conventions followed (named exports, barrel files where specified)

### 3. Code cleanliness
- No unused imports or dead code
- No commented-out code blocks
- Functions under 30 lines (flag exceptions)
- Files under 300 lines (flag exceptions)
- No code duplication (similar blocks > 10 lines)

### 4. i18n compliance
> **Applies to**: projects with user-facing output (web, mobile, CLI, desktop)
> **Not required for**: libraries, embedded systems, data pipelines

- No hardcoded user-facing strings (all strings must use i18n keys)
- Translation files exist for all supported locales
- No missing translation keys

### 5. Design system compliance
> **For web projects**: CSS variables used for colors, spacing, typography (no hardcoded values like `#ff0000` or `16px`). Components use design system tokens. No inline styles unless explicitly justified.
> **For mobile UI projects**: Design tokens used for theming. No hardcoded colors or spacing outside the design system.
> **For CLI projects**: Terminal styling constants (colors, formatting) centralized. No scattered ANSI codes.
> **For API/library projects**: N/A — skip this check.
