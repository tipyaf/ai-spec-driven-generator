# Test Engineer Agent — Reference

> This file contains templates and examples. Load only when needed.

---

## Test File Templates

### Backend Test (Python/pytest)
```python
import pytest
from httpx import AsyncClient

# ORACLE: expected fill_price = entry_price from test data (1234.56)
async def test_entry_order_fill_price(client: AsyncClient, realistic_data):
    resp = await client.get("/api/v1/data/orders", headers=auth_headers(user))
    assert resp.status_code == 200
    order = find_by_id(resp.json()["orders"], order_id)
    # ORACLE: fill_price must equal entry_price = 1234.56
    assert order["fill_price"] == pytest.approx(1234.56)
```

### Frontend Test (TypeScript/Vitest + MSW)
```typescript
import { http, HttpResponse } from "msw";
import { render, screen } from "@testing-library/react";
import { server } from "../mocks/server";

// MSW returns EXACT backend Pydantic shape — never frontend expectations
server.use(
  http.get("*/api/v1/exchange/balances", () =>
    HttpResponse.json({
      balances: [
        { currency: "USDT", free: 900.0, used: 100.0, total: 1000.0 },
      ],
    })
  )
);

test("displays balance from API", async () => {
  render(<BalancePage />);
  expect(await screen.findByText("$1,000.00")).toBeInTheDocument();
});
```

### Contract Test (response shape validation)
```python
async def test_orders_response_matches_schema(client: AsyncClient):
    resp = await client.get("/api/v1/data/orders", headers=auth_headers(user))
    assert resp.status_code == 200
    data = resp.json()
    assert "orders" in data
    order = data["orders"][0]
    # Contract: field names match Pydantic OrderResponse
    assert set(order.keys()) >= {"id", "symbol", "side", "fill_price", "quantity", "status"}
```

---

## RED Phase Checklist

Before handing off to the builder, verify:

- [ ] Coverage audit completed — gap matrix produced
- [ ] All test_intentions from spec have corresponding test functions
- [ ] All API contract mismatches have corresponding tests
- [ ] ORACLE blocks present on every computed value assertion
- [ ] Tests written in batches of 10-15 (not all at once)
- [ ] Each batch runs through linter
- [ ] ALL tests FAIL (except auth 401 which may pre-exist)
- [ ] No `.skip()` or `.todo()` in any test file
- [ ] No fixture-shape tests (tests call production code)
- [ ] No MSW mocks derived from frontend code (backend routers are source of truth)
- [ ] Enforcement scripts pass (`scripts/check_test_quality.py`, `scripts/check_oracle_assertions.py`)
- [ ] Committed with message: `test: RED — failing tests for [feature-id]`

---

## Coverage Audit Example

```markdown
## Coverage Audit — Feature: user-portfolio

### Data Stores
| Store | Table/Collection | Touched by feature | Test exists |
|-------|-----------------|-------------------|-------------|
| PostgreSQL | portfolios | Yes | No — GAP |
| PostgreSQL | portfolio_snapshots | Yes | No — GAP |
| Redis | portfolio:{id}:cache | Yes | No — GAP |

### Endpoints
| Method | Path | Test exists |
|--------|------|-------------|
| GET | /api/v1/portfolios | No — GAP |
| GET | /api/v1/portfolios/:id | No — GAP |
| POST | /api/v1/portfolios | No — GAP |
| PUT | /api/v1/portfolios/:id | No — GAP |
| DELETE | /api/v1/portfolios/:id | No — GAP |

### Pages (frontend)
| Route | Test exists |
|-------|-------------|
| /portfolios | No — GAP |
| /portfolios/:id | No — GAP |

### Gap Summary
- 3 data store gaps → 3 write-path tests needed
- 5 endpoint gaps → 5 integration tests needed
- 2 page gaps → 2 MSW behavior tests needed
- **Total: 10 tests to write before starting**
```

---

## Forbidden Test Patterns

| Pattern | Why it fails | Fix |
|---------|-------------|-----|
| `mock.assert_called_with(...)` as primary assertion | Mock-soup — tests function signature not behavior | Call real code, assert on response |
| `expect(container.innerHTML).toContain(...)` | Source assertion — tests DOM structure not behavior | Use `screen.getByText()` or `getByRole()` |
| `expect(true).toBe(true)` | Empty test — asserts nothing | Write a real assertion against production code |
| Snapshot-only without behavioral assertion | Snapshot drift — no correctness guarantee | Add `expect(screen.getByText(...))` alongside |
| Hardcoded database IDs | Breaks on different seed data | Use factories or query by attribute |
