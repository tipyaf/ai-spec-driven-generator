---
name: architect-reference
description: Reference material for the Architect agent — stack comparison table, architecture overview templates, file structure example, data model format, implementation plan format, ADR template, and anti-patterns.
---

# Architect — Reference Material

## Stack Comparison Table Template

```markdown
## Stack Recommendation

| Criterion | Option A: [name] | Option B: [name] | Option C: [name] |
|-----------|-------------------|-------------------|-------------------|
| Feature fit | [score/10] | [score/10] | [score/10] |
| Performance | [score/10] | [score/10] | [score/10] |
| Ecosystem | [score/10] | [score/10] | [score/10] |
| Learning curve | [Easy/Medium/Hard] | ... | ... |
| Community support | [Active/Moderate/Low] | ... | ... |
| **Recommendation** | | **Recommended** | |

**Why Option B?** [2-3 sentence justification]

**Trade-offs**: [what you lose vs Option A or C]

**Confirm Option B or tell me which option you prefer?**
```

## Architecture Overview Template

```markdown
## Architecture Overview
- Pattern: [e.g., Clean Architecture]
- Layers: [e.g., Presentation → Application → Domain → Infrastructure]
- Communication: [e.g., REST API, WebSocket, CLI stdin/stdout, IPC]
```

## File Structure Example

```
project-name/
├── src/
│   ├── ...
├── tests/
│   ├── ...
├── config/
│   ├── ...
└── ...
```

## Data Model Format

For each entity:
- Complete schema with types
- Relations
- Indexes
- Validation constraints

## Implementation Plan Format

Ordered task list with dependencies:
```markdown
1. [Setup] Initialize project and install dependencies
2. [Data] Create database schema
3. [Core] Implement business logic for [feature 1]
4. [API] Create endpoints for [feature 1]
5. [UI] Create components for [feature 1]
...
```

## ADR Template

```markdown
### ADR-001: [Title]
- **Context**: Why this decision is necessary
- **Decision**: What was chosen
- **Alternatives**: What was considered
- **Consequences**: Impact on the project
```

## Stack Profile Example

For a Python/FastAPI + React/TypeScript project, create:
- `stacks/python-fastapi.md`
- `stacks/typescript-react.md`

## Implementation Manifest — Interface Examples by Project Type

```yaml
# Web:
- route: "/parametres/connexion-email"
  checks: ["design system colors", "card readability", "responsive"]

# CLI:
- command: "mycli init --template react"
  checks: ["exit code 0", "creates config file", "stdout contains success message"]

# Mobile:
- screen: "SettingsScreen"
  checks: ["theme colors", "layout on small devices"]

# API:
- endpoint: "GET /api/users"
  checks: ["returns 200", "response shape matches spec", "pagination works"]
```

## Anti-patterns to Avoid
- Architecture astronaut (too many abstractions)
- God classes / god modules
- Circular dependencies
- Unnecessary layers for a small project
- Copying an architecture without understanding why

## Best Practices Catalog

> Used by Step 1b (Best Practices Proposal). Select practices matching the project type and stack.
> Each practice must be actionable and verifiable — not vague advice.

### Frontend UI (web)

| # | Practice | Rationale |
|---|----------|-----------|
| 1 | Use semantic HTML elements (`<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<footer>`) over generic `<div>` | Improves accessibility, SEO, and code readability |
| 2 | Enforce heading hierarchy (h1 → h2 → h3, no skipped levels) | Screen readers use headings for navigation |
| 3 | Every `<img>` has `alt` attribute; decorative images use `alt=""` | Accessibility requirement (WCAG 1.1.1) |
| 4 | Every form input has a visible `<label>` or `aria-label` | Accessibility and UX — unlabeled inputs are unusable |
| 5 | Adopt a CSS methodology and enforce it (BEM, CSS Modules, Tailwind, etc.) | Prevents specificity wars and inconsistent naming |
| 6 | Ban `!important` except in documented justified cases | Signals broken cascade — fix the root cause instead |
| 7 | Use design tokens (CSS variables / theme) for colors, spacing, typography — no hardcoded values | Enables theming, consistency, and easy design updates |
| 8 | Use modern layout (Flexbox / Grid) over floats and positioning hacks | Cleaner, more maintainable, better responsive behavior |
| 9 | Use relative units (`rem`, `%`, `vw/vh`) for sizing; `px` only for borders and fine details | Enables responsive scaling and respects user font settings |
| 10 | `const` by default, `let` when reassignment needed, `var` banned | Reduces mutation bugs and improves code clarity |
| 11 | Use modern syntax: destructuring, template literals, async/await, optional chaining (`?.`), nullish coalescing (`??`) | Cleaner, more readable code with fewer edge-case bugs |
| 12 | Never manipulate the DOM directly when using a framework — let the framework handle rendering | Direct DOM manipulation breaks framework reactivity and causes subtle bugs |
| 13 | Lazy-load images, routes, and non-critical components | Reduces initial load time and bandwidth |
| 14 | Code-split by route or feature — avoid monolithic bundles | Faster page loads, better caching |
| 15 | Inline critical CSS in `<head>`, defer non-essential JS with `defer`/`async` | Faster first paint |
| 16 | Use modern image formats (WebP/AVIF) with fallbacks | 30-50% smaller files than JPEG/PNG |
| 17 | Leverage browser caching (Cache-Control, ETag) | Reduces repeat-visit load times |
| 18 | Mobile-first approach with responsive breakpoints | Easier to scale up than to scale down |
| 19 | Test on real devices, not only browser DevTools | DevTools doesn't catch touch, performance, and rendering differences |

### Frontend UI (mobile native — iOS/Android)

| # | Practice | Rationale |
|---|----------|-----------|
| 1 | Use platform-native view hierarchy (UIStackView/Auto Layout on iOS, ConstraintLayout on Android) | Better performance and platform consistency than absolute positioning |
| 2 | Set `contentDescription` (Android) / `accessibilityLabel` (iOS) on all interactive and informational elements | Screen reader accessibility |
| 3 | Use platform theme system (Material Theme / UIAppearance / SwiftUI modifiers) for colors, typography, spacing | Enables dark mode, dynamic type, and consistent theming |
| 4 | Never hardcode colors or dimensions — use theme tokens or resource files | Allows theming, dark mode, and accessibility scaling |
| 5 | Lazy-load images with platform tools (Coil/Glide on Android, SDWebImage/Kingfisher on iOS) | Prevents OOM on image-heavy screens |
| 6 | Use adaptive layouts and size classes instead of fixed breakpoints | Handles tablets, foldables, split-screen without custom logic |
| 7 | Minimize app binary size (ProGuard/R8 on Android, asset catalogs on iOS, tree shaking) | Reduces download time and storage impact |
| 8 | Handle all lifecycle states (background, foreground, low memory, screen rotation) | Prevents crashes and data loss on state transitions |
| 9 | Test on real devices across screen sizes, not only emulators | Emulators miss touch latency, GPU rendering, and memory constraints |

### Frontend UI (cross-platform — Flutter, React Native, etc.)

| # | Practice | Rationale |
|---|----------|-----------|
| 1 | Use framework widgets/components for layout (Row/Column/Stack in Flutter, View/ScrollView in RN) | Framework handles platform differences |
| 2 | Set accessibility labels on all interactive elements (`Semantics` in Flutter, `accessibilityLabel` in RN) | Cross-platform accessibility |
| 3 | Use framework theming system (ThemeData in Flutter, StyleSheet in RN) — no inline styles | Centralized, consistent, themeable |
| 4 | Never bypass the framework to call native APIs directly unless strictly necessary | Breaks cross-platform promise, creates maintenance burden |
| 5 | Lazy-load routes and heavy components | Reduces startup time on both platforms |
| 6 | Test on both platforms (iOS + Android) with real devices | Rendering differences exist despite cross-platform promise |

### Backend API

| # | Practice | Rationale |
|---|----------|-----------|
| 1 | Validate all inputs at the API boundary with typed schemas (Zod, Pydantic, Joi, etc.) | Prevents invalid data from reaching business logic |
| 2 | Use parameterized queries or ORM — never string concatenation for SQL | SQL injection prevention (OWASP A03) |
| 3 | Return consistent error format (RFC 7807 or project-defined) with no stack traces | Prevents information disclosure, improves client DX |
| 4 | Explicit response types on every endpoint — no untyped returns | API contract clarity, documentation generation |
| 5 | Separate read (query) and write (command) paths when complexity warrants it | CQRS — prevents coupling read optimizations with write logic |
| 6 | Log structured data (JSON), never sensitive fields (passwords, tokens, PII) | Enables log aggregation, prevents data leaks |
| 7 | Enforce rate limiting on public endpoints | Prevents abuse and DoS |
| 8 | Use health check endpoint (`/health` or `/readiness`) | Enables load balancer and deployment verification |
| 9 | Handle async errors explicitly — no unhandled promise rejections or swallowed exceptions | Silent failures are the worst failures |

### Data Pipeline

| # | Practice | Rationale |
|---|----------|-----------|
| 1 | Make every stage idempotent — re-running produces the same result | Enables safe retries after failures |
| 2 | Validate data shape at ingestion (schema validation, null checks) | Garbage in = garbage out — catch early |
| 3 | Log row counts and checksums at each stage boundary | Enables data reconciliation and debugging |
| 4 | Separate extraction, transformation, and loading into distinct modules | SRP — easier to test, debug, and replace each stage |
| 5 | Handle partial failures — one bad record should not kill the pipeline | Use dead-letter queues or error tables for reprocessing |
| 6 | Test with realistic data volumes, not just 10-row samples | Performance and memory issues only appear at scale |

### CLI / Library

| # | Practice | Rationale |
|---|----------|-----------|
| 1 | Validate all user inputs (args, flags, stdin) at entry point | Fail fast with clear error messages |
| 2 | Use exit codes consistently (0 = success, 1 = user error, 2 = system error) | Enables scripting and CI/CD integration |
| 3 | Provide `--help` with examples, not just flag descriptions | Users learn by example |
| 4 | Separate public API from internal implementation (library) | Consumers depend on public API — internal changes should not break them |
| 5 | Write comprehensive README with install, quickstart, and common use cases | First-contact documentation — if it's missing, adoption drops |
| 6 | Version public API with semver — breaking changes bump major | Consumer trust depends on predictable versioning |
