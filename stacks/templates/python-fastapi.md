# Stack Profile: Python + FastAPI

## Language & Framework

- Python 3.11+
- FastAPI with async handlers
- SQLAlchemy 2.x ORM (async)
- Pydantic v2 for schemas
- Alembic for migrations
- pytest + httpx AsyncClient for tests

---

## Security ACs (auto-added to every backend story by Story Refiner)

These AC-SEC items are added automatically to every story that touches a FastAPI endpoint.
Edit only if the project requires a specific override -- never re-invent what is already here.

- [ ] AC-SEC-01: Every protected endpoint returns 401 when no Authorization header/cookie is present | verify: grep -r "401" tests/test_<module>.py
- [ ] AC-SEC-02: Endpoint response does not include password hashes, raw secrets, or internal IDs that are not needed by the client | verify: static -- read response_model schema, check excluded fields
- [ ] AC-SEC-03: Input validated by Pydantic schema -- no raw dict unpacking into DB queries | verify: grep -r "\.dict()" app/routers/<router>.py (must not be used as direct DB insert)
- [ ] AC-SEC-04: SQL queries use ORM or parameterized statements -- no string interpolation | verify: grep -rn "f\"SELECT\|f'SELECT\|% (" app/services/<service>.py (must return no matches)
- [ ] AC-SEC-05: No secrets or API keys hardcoded in source files | verify: grep -rn "password\s*=\s*['\"].\|api_key\s*=\s*['\"]." app/ (must return no matches)

---

## Best Practice ACs (auto-added by Story Refiner)

These AC-BP items are added automatically to every story that touches a FastAPI endpoint.
Edit only if the project has an explicit override documented in CLAUDE.md.

- [ ] AC-BP-01: Every endpoint declares `response_model=` and `status_code=` | verify: grep -n "response_model=" app/routers/<router>.py
- [ ] AC-BP-02: Every endpoint is async (`async def`) | verify: grep -n "^async def\|^    async def" app/routers/<router>.py
- [ ] AC-BP-03: DB session injected via `Depends()` -- never instantiated directly in handler | verify: grep -n "SessionLocal()\|get_db()" app/routers/<router>.py (SessionLocal() must not appear in handlers)
- [ ] AC-BP-04: Errors return structured JSON (not plain strings) | verify: static -- read exception handler in app/main.py, confirm RFC 7807 or similar structured format
- [ ] AC-BP-05: Test uses real `AsyncClient` with `ASGITransport` -- no mock DB sessions | verify: grep -n "ASGITransport\|AsyncClient" tests/test_<module>.py

---

## Forbidden Patterns

These patterns are never acceptable. The validator will fail any AC that permits them.

| Pattern | Why forbidden |
|---------|--------------|
| `session = SessionLocal()` in request handlers | Bypasses dependency injection, leaks connections |
| `response.json()["detail"]` assertions in tests | Couples tests to error message strings; use status code assertions |
| `any` type on Pydantic fields without a comment | Disables type safety silently |
| Synchronous DB calls inside async handlers | Blocks the event loop, degrades throughput |
| `SELECT *` queries | Returns extra columns, breaks if schema changes, exposes sensitive fields |
| `from app.db import session` (module-level) | Creates a global session, not safe for concurrent requests |
| String interpolation in SQL (`f"SELECT {var}"`) | SQL injection vector |
| Catching `Exception` broadly without re-raising | Hides errors, makes debugging impossible |

---

## Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| Files | `snake_case.py` | `exchange_service.py` |
| Classes | `PascalCase` | `ExchangeConfig` |
| Routes | `/kebab-case/{id}` | `/exchange-configs/{config_id}` |
| DB tables | `snake_case` in a named schema | `trading.exchange_configs` |
| Test files | `test_<module>.py` | `test_exchange_router.py` |
| Pydantic schemas | `<Resource>In` / `<Resource>Out` | `ExchangeConfigIn`, `ExchangeConfigOut` |
| Service functions | `verb_noun()` | `get_exchange_config()`, `create_bot()` |

---

## Test Patterns

### AsyncClient setup (canonical)

```python
from httpx import AsyncClient, ASGITransport

@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c
```

### Auth in integration tests

```python
# Use the project's token factory -- never hardcode a token string
token = create_access_token({"sub": str(user_id)})
headers = {"Authorization": f"Bearer {token}"}
# OR via cookie (check the project's auth mechanism)
client.cookies.set("access_token", token)
```

### Mock at use site, not source

```python
# WRONG: patches source module; router already imported the function
with patch("app.services.exchange_service.fetch_balances", ...):

# RIGHT: patches the local reference in the router
with patch("app.routers.exchange.fetch_balances", ...):
```

---

## Story Refiner Instructions

When refining a `backend` story, the Story Refiner MUST:

1. Read this file before writing any ACs
2. Copy all AC-SEC-* items into the story's `### Security (AC-SEC-*)` section
3. Copy all AC-BP-* items into the story's `### Best Practice (AC-BP-*)` section
4. Substitute `<module>`, `<router>`, `<service>` placeholders with the actual file names for this story
5. Add project-specific overrides AFTER the standard items -- never replace them
6. Add story-specific AC-FUNC-* items in the `### Functional (AC-FUNC-*)` section

The Validator will execute each `verify:` command literally. Ensure the grep patterns
and file paths are correct for the story's actual implementation.
