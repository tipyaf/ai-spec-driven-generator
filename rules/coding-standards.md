# Coding Standards

**Shared rules for every agent that writes, reviews, or evaluates code.**
Referenced by: `developer.md`, `reviewer.md`, `tester.md`, `validator.md`.

These standards are **language-agnostic**. Stack profiles (`stacks/`) add language-specific
rules on top of these. When a stack profile contradicts a rule here, the stack profile wins
for that specific language -- but these defaults apply everywhere else.

---

## 1. SOLID Principles

### Single Responsibility (SRP)
One module = one reason to change. Separate concerns by layer:

| Layer | Responsibility | FAIL if |
|-------|---------------|---------|
| Router / Controller | HTTP handling, request parsing, response formatting | Contains business logic or DB queries |
| Service / Use Case | Business logic, validation, orchestration | Contains HTTP-specific code or direct DB calls |
| Repository / Data Access | Persistence, queries, transactions | Contains business logic |
| Model / Entity | Data structure, invariants | Contains I/O or side effects |

### Open/Closed (OCP)
Extend behavior via new classes/modules, not by modifying existing code. Use dependency injection
to swap implementations. Adding a new payment method should not require editing the existing
payment service -- it should add a new one that implements the same interface.

### Liskov Substitution (LSP)
Subtypes must be drop-in replacements for their base type. No empty stub methods, no
`NotImplementedError` in production code (test doubles are fine), no narrowing of input
types or broadening of exceptions.

### Interface Segregation (ISP)
Small, focused interfaces. Don't force implementors to stub methods they don't need.
If an interface has 10 methods and most implementations only use 3, split it.

### Dependency Inversion (DIP)
Depend on abstractions, not concrete implementations. Inject dependencies via constructor,
function parameters, or framework DI (FastAPI `Depends()`, NestJS `@Inject()`, etc.).
Never instantiate dependencies inside the class that uses them.

---

## 2. CQRS — Command Query Responsibility Segregation

> Applies to projects with distinct read/write paths (APIs, databases). Skip for simple
> scripts, CLIs, or libraries.

- **Commands** (write operations: create, update, delete) return only the created/updated ID
  or a status. They do NOT return the full queried result.
- **Queries** (read operations: get, list, search) are separate services/functions. They may
  use joins, aggregations, materialized views.
- This prevents coupling between read and write paths. A query optimization should not
  require touching write logic, and vice versa.

---

## 3. DRY — Don't Repeat Yourself

- Shared logic in ONE place. Validation, transformation, and business rules centralized.
- Data models are the source of truth for data shapes (Pydantic, Zod, TypeScript interfaces,
  Go structs, etc.).
- Config defined once, never scattered across files.
- Exception/error classes shared, not redefined per module.
- Test fixtures in shared setup (conftest.py, beforeAll, factories), never copy-pasted.

**But**: DRY must not sacrifice readability. Three similar lines of code are better than a
premature abstraction. If the "shared" logic is only used twice and the duplication is obvious,
leave it -- extract only when a third use appears or the logic is non-trivial.

---

## 4. YAGNI — You Aren't Gonna Need It

- Build ONLY what the current story requires. No speculative endpoints, unused parameters,
  premature abstractions, or feature toggles.
- No pagination, caching, or rate limiting unless the story asks for it.
- No abstractions for "future flexibility" -- the right amount of complexity is the minimum
  needed for the current task.

---

## 5. Code Readability Gates

These thresholds are **hard limits**. Code review MUST fail if any is exceeded.

| Check | FAIL if | Why |
|-------|---------|-----|
| Function length | > 40 lines | Long functions signal poor decomposition |
| Nesting depth | > 3 levels | Deep nesting is hard to follow and test |
| Cyclomatic complexity | > 10 per function | Complex functions need splitting |
| File length | > 400 lines | Large files signal poor separation of concerns |
| Function parameters | > 5 | Use an options object/struct instead |
| Naming clarity | Variables named `x`, `tmp`, `data`, `result` without context | Names are documentation |
| Dead code | Commented-out code blocks, unresolved TODO/FIXME/HACK | Clean code only |
| Duplication | Same logic repeated > 2 times | Extract to shared function |

---

## 6. API Design (REST)

> Applies to projects with HTTP APIs. Skip for CLI, library, embedded, data pipeline.

| Rule | Standard |
|------|----------|
| Resource naming | Plural nouns, lowercase, hyphen-separated: `/api/v1/users`, `/api/v1/order-items` |
| HTTP methods | GET=read, POST=create, PUT=full replace, PATCH=partial update, DELETE=remove |
| Status codes | 200 (success + body), 201 (created), 204 (no body), 400 (bad request), 401 (unauthorized), 403 (forbidden), 404 (not found), 409 (conflict), 422 (validation) |
| Error format | Consistent structure (RFC 7807 or project-defined). Never unstructured strings. |
| Response typing | Every endpoint has explicit response model/type. No untyped returns. |
| Pagination | List endpoints use limit/offset or cursor with enforced maximum. |
| Idempotency | PUT and DELETE are idempotent. POST is not (use idempotency keys if needed). |
| Versioning | All endpoints under `/api/v1/` (or project convention). |

---

## 7. Error Handling

| Rule | Detail |
|------|--------|
| Never swallow errors | Empty catch blocks are forbidden. Log + rethrow or handle explicitly. |
| Clear error messages | Errors must include what went wrong and ideally how to fix it. |
| Fail fast | Validate inputs at the boundary (API entry, CLI args, config load). Don't propagate invalid data through layers. |
| Typed errors | Use error classes/types, not string messages. Callers should be able to pattern-match on error type. |
| No stack traces in responses | API responses never expose internal stack traces. Log them server-side. |

---

## 8. Anti-Patterns (language-agnostic)

These are ALWAYS wrong, regardless of language or project type:

| Anti-pattern | Fix |
|-------------|-----|
| Mutable global state | Dependency injection |
| Circular imports/dependencies | Review architecture, split modules |
| Nested callbacks (callback hell) | Async/await or promise chains |
| God objects/classes (> 10 methods, > 500 lines) | Split into focused modules |
| String interpolation in SQL/queries | Parameterized queries / ORM |
| Catching generic Exception without re-raising | Catch specific errors, re-raise unknowns |
| Magic numbers/strings in business logic | Named constants or config |
| Direct I/O in business logic | Abstract behind interfaces/repositories |
| Synchronous blocking in async context | Use async equivalents |
| `any` type / `Object` / `interface{}` without justification | Use proper types |

---

## 9. Naming Conventions (defaults)

These are defaults. Stack profiles can override with language-specific conventions.

| Element | Convention | Example |
|---------|-----------|---------|
| Files | `snake_case` or `kebab-case` (per language convention) | `user_service.py`, `user-service.ts` |
| Classes / Types | `PascalCase` | `UserService`, `OrderItem` |
| Functions / Methods | `camelCase` or `snake_case` (per language) | `getUserById`, `get_user_by_id` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| Routes / URLs | `kebab-case`, plural nouns | `/api/v1/order-items` |
| Database tables | `snake_case` | `order_items` |
| Event handlers | `handle<Action>` or `on_<action>` | `handleSubmit`, `on_message_received` |

---

## Hard Constraints

- **NEVER commit code that violates readability gates** (function > 40 lines, nesting > 3, file > 400 lines)
- **NEVER leave TODO/FIXME/HACK in committed code** -- resolve before commit
- **NEVER use magic numbers/strings in business logic** -- extract to constants
- **NEVER catch generic exceptions without re-raising** -- be specific
- **NEVER return untyped data from APIs** -- always declare response model
- **ALWAYS follow the project's stack profile conventions** -- they override these defaults
- **ALWAYS read existing code before writing new code** -- understand patterns first
