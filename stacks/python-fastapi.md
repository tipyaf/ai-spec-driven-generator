# Stack Profile: Python + FastAPI

## Coding Best Practices

### Project structure
- Use the **repository pattern** for data access
- Use **dependency injection** via FastAPI's `Depends()`
- Separate **routers** (endpoints) from **services** (business logic)
- Use **Pydantic models** for all request/response schemas — never use raw dicts
- Use **async/await** consistently — do not mix sync and async

### Conventions
- Follow **PEP 8** and use a formatter (black/ruff)
- Type hints on ALL function signatures — no untyped functions
- Use `Annotated` types for dependency injection
- Docstrings on public functions (Google format)
- Use `Enum` for fixed value sets, not magic strings
- Environment variables via `pydantic-settings` with `.env` files

### Anti-patterns
- Never use `*` imports
- Never use mutable default arguments
- Never catch bare `except:` — always specify the exception type
- Never store secrets in code — use environment variables
- Never use `requests` in async code — use `httpx`
- Never return raw SQLAlchemy models from endpoints — use Pydantic schemas

## Security Rules

### Input validation (OWASP A03)
- ALL user input validated through Pydantic models with strict constraints
- Use `Field(max_length=...)`, `Field(ge=0)`, `Field(regex=...)` for constraints
- File uploads: validate MIME type, file size, and extension (whitelist, not blacklist)
- Path parameters: validate format (e.g., UUID) to prevent path traversal

### Authentication & Authorization (OWASP A01, A07)
- Use OAuth2 with JWT tokens — never roll your own auth
- Passwords hashed with **bcrypt** (min 12 rounds) via `passlib`
- JWT tokens: short-lived access (15min), long-lived refresh (7d)
- Use FastAPI `Security` dependencies for role-based access
- Rate limiting on auth endpoints (login, register, password reset)

### SQL Injection (OWASP A03)
- Use SQLAlchemy ORM or parameterized queries — NEVER raw SQL with f-strings
- Use `text()` with bind parameters for raw queries when needed

### Data exposure (OWASP A01)
- Never return passwords, tokens, or internal IDs in responses
- Use separate Pydantic models for create/read/update (not the same schema)
- Paginate all list endpoints — never return unbounded results

### Headers & CORS
- Configure CORS explicitly — never use `allow_origins=["*"]` in production
- Set security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`

### Dependencies
- Pin all dependency versions in `requirements.txt` or `pyproject.toml`
- Run `pip-audit` or `safety check` regularly
- No dependencies with known CVEs

### Logging
- Never log sensitive data (passwords, tokens, PII)
- Use structured logging (JSON format)
- Log all authentication events (success/failure)

## Performance Rules
- Use async database driver (`asyncpg` for PostgreSQL)
- Connection pooling via SQLAlchemy `create_async_engine`
- Use `select` with `.options(joinedload(...))` to avoid N+1 queries
- Cache expensive operations with Redis or in-memory cache
- Background tasks via FastAPI `BackgroundTasks` or Celery for heavy work
- Use streaming responses for large data exports

## Testing Rules
- Framework: **pytest** with **pytest-asyncio**
- Use `httpx.AsyncClient` with `ASGITransport` for API testing
- Factory pattern with **factory_boy** for test data
- Separate test database — never test against production
- Use `@pytest.fixture` with proper scope (function/session)
- Coverage target: 80%+ on business logic

## Auto-generated AC Templates

These ACs are automatically added to EVERY feature that has API endpoints:

```
AC-SEC-[FEATURE]-INPUT:
  Given any API endpoint for [feature]
  When receiving user input
  Then all fields are validated through Pydantic models with appropriate constraints

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

AC-BP-[FEATURE]-ASYNC:
  Given the service layer for [feature]
  When performing I/O operations (DB, HTTP, file)
  Then async/await is used consistently with no blocking calls

AC-BP-[FEATURE]-TYPING:
  Given all functions in [feature]
  When reviewing the code
  Then all functions have complete type hints and Pydantic models for data validation
```

These ACs are automatically added to features with file uploads:

```
AC-SEC-[FEATURE]-UPLOAD:
  Given a file upload endpoint for [feature]
  When a file is uploaded
  Then file type is validated (whitelist), size is limited, and file is stored outside webroot
```

These ACs are automatically added to features with database operations:

```
AC-BP-[FEATURE]-QUERIES:
  Given database queries for [feature]
  When loading related data
  Then eager loading or explicit joins are used to prevent N+1 queries

AC-SEC-[FEATURE]-SQL:
  Given database operations for [feature]
  When building queries
  Then SQLAlchemy ORM or parameterized queries are used (no raw SQL with string interpolation)
```
