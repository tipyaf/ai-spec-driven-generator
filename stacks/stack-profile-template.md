# Stack Profile: [Language] + [Framework]

> This template is used by the Architect agent (Phase 1) to create stack profiles for the project.
> Stack profiles belong to the **project**, not the framework.
> Copy this template to your project's `stacks/` directory and fill it in.

## Coding Best Practices

### Project structure
- [Recommended project structure patterns for this stack]

### Conventions
- [Naming conventions, formatting, linting rules]
- [Type system usage]
  - In typed languages, distinguish between ABSENT values (property not in object) and NULL values (property present, value is null). Never conflate the two.
  - Use optional (`field?: T`) only when the property can genuinely be absent (undefined) — e.g. optional input params, conditional API response fields.
  - Use nullable (`field: T | null`) when the property is always present but its value can be null — e.g. nullable DB columns.
  - Never use `field?: T | null` — this conflates both concepts.
- [Import/export patterns]

### Anti-patterns
- [Common mistakes to avoid with this stack]


## Security Rules

### Input validation (OWASP A03)
- [How to validate input in this stack]

### Authentication & Authorization (OWASP A01, A07)
- [Auth best practices specific to this framework]

### Injection prevention (OWASP A03)
- [SQL injection, XSS, command injection prevention]

### Data exposure (OWASP A01)
- [How to avoid leaking sensitive data]

### Headers & CORS
- [Security headers and CORS configuration]

### Dependencies
- [Dependency management and audit tools]

### Logging
- [Secure logging practices]

## Performance Rules
- [Stack-specific performance optimizations]
- [Caching strategies]
- [Async patterns if applicable]

## Testing Rules

### Framework and tools
- [Test framework: pytest, vitest, jest, go test, etc.]
- [Integration test approach: real DB, test client, etc.]
- [Mutation testing tool: mutmut, stryker, etc.]
- [Coverage tool and minimum threshold]
- [Property-based testing tool: Hypothesis, fast-check, etc.]

### Test patterns
- [How to write integration tests in this stack]
- [How to mock external APIs (not internal DB)]
- [How to write fixtures/factories]
- [How to set up test databases]

### Enforcement configuration
- [What to put in test_enforcement.json for this stack]
- [Where are backend_test_dirs, integration_test_dirs, etc.]
- [What write_path_keywords are relevant]

## Component Architecture (UI projects only)

> Skip this section for API-only, CLI, library, embedded, or data pipeline projects.

### Smart/Dumb mapping for this stack
- **Dumb components**: [How presentational components work in this framework — e.g., React: pure function with props, Vue: props-only SFC, Angular: @Input/@Output]
- **Smart components**: [How container components work — e.g., React: hooks + context, Vue: composables + store, Angular: services + observables]
- **Shared component directory**: [Path where reusable dumb components live — e.g., `src/components/ui/`, `src/shared/components/`]
- **Feature component directory**: [Path where feature-specific smart components live — e.g., `src/features/[name]/components/`]

### Component rules specific to this stack
- [State management pattern: Redux, Zustand, Pinia, NgRx, etc.]
- [How to pass data down: props, slots, children, content projection]
- [How to emit events up: callbacks, custom events, @Output, emit]
- [Styling approach: CSS modules, styled-components, Tailwind, scoped styles]

## SOLID Application in This Stack
- [How SRP maps to this framework (e.g., controllers/services/repos)]
- [How DIP works (dependency injection mechanism)]
- [Common SOLID violations specific to this stack]

## Auto-generated AC Templates

> These ACs are automatically added to features by the Refinement agent (Phase 2.5).
> Adapt the templates below to match the stack's specifics.

### For features with API endpoints
```
AC-SEC-[FEATURE]-INPUT:
  Given any API endpoint for [feature]
  When receiving user input
  Then all fields are validated through [stack-specific validation mechanism]

AC-SEC-[FEATURE]-AUTH:
  Given a protected endpoint for [feature]
  When a request is made without valid authentication
  Then a 401 response is returned with no data leakage

AC-SEC-[FEATURE]-AUTHZ:
  Given a protected endpoint for [feature]
  When a user tries to access another user's data
  Then a 403 response is returned

AC-SEC-[FEATURE]-ERRORS:
  Given any API endpoint for [feature]
  When an unexpected error occurs
  Then a generic error message is returned (no stack trace) and the error is logged

AC-BP-[FEATURE]-TYPING:
  Given all functions in [feature]
  When reviewing the code
  Then all functions have complete type annotations and data validation
```

### For features with database operations
```
AC-BP-[FEATURE]-QUERIES:
  Given database queries for [feature]
  When loading related data
  Then optimized queries are used to prevent N+1 problems

AC-SEC-[FEATURE]-INJECTION:
  Given database operations for [feature]
  When building queries
  Then parameterized queries or ORM are used (no raw string interpolation)
```

### For features with file uploads
```
AC-SEC-[FEATURE]-UPLOAD:
  Given a file upload endpoint for [feature]
  When a file is uploaded
  Then file type is validated (whitelist), size is limited, and file is stored outside webroot
```
