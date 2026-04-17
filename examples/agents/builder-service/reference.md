# Builder — Service Agent — Reference

> This file contains templates and examples. Load only when needed.

---

## Service Structure Template

```
services/
└── [service-name]/
    ├── main.py                 # App factory and startup
    ├── config.py               # Settings from env vars
    ├── dependencies.py         # DI container / shared deps
    ├── routers/
    │   ├── __init__.py
    │   └── [resource].py       # One router per resource
    ├── services/
    │   ├── __init__.py
    │   └── [resource].py       # Business logic
    ├── repositories/
    │   ├── __init__.py
    │   └── [resource].py       # Data access
    ├── models/
    │   ├── __init__.py
    │   └── [resource].py       # ORM models
    ├── schemas/
    │   ├── __init__.py
    │   └── [resource].py       # Pydantic request/response
    └── tests/
        ├── conftest.py         # Shared fixtures
        ├── test_[resource].py  # Integration tests
        └── test_health.py      # Health endpoint test
```

---

## Endpoint Template

### Router (FastAPI example)
```python
from fastapi import APIRouter, Depends, status
from ..schemas.portfolio import PortfolioCreate, PortfolioResponse, PortfolioListResponse
from ..services.portfolio import PortfolioService
from ..dependencies import get_portfolio_service, get_current_user

router = APIRouter(prefix="/api/v1/portfolios", tags=["portfolios"])


@router.get(
    "",
    response_model=PortfolioListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_portfolios(
    service: PortfolioService = Depends(get_portfolio_service),
    user=Depends(get_current_user),
):
    """List all portfolios for the authenticated user."""
    portfolios = await service.list_by_user(user.id)
    return PortfolioListResponse(portfolios=portfolios)


@router.post(
    "",
    response_model=PortfolioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_portfolio(
    data: PortfolioCreate,
    service: PortfolioService = Depends(get_portfolio_service),
    user=Depends(get_current_user),
):
    """Create a new portfolio."""
    portfolio = await service.create(user.id, data)
    return portfolio


@router.get(
    "/{portfolio_id}",
    response_model=PortfolioResponse,
    status_code=status.HTTP_200_OK,
)
async def get_portfolio(
    portfolio_id: str,
    service: PortfolioService = Depends(get_portfolio_service),
    user=Depends(get_current_user),
):
    """Get a portfolio by ID."""
    return await service.get_by_id(user.id, portfolio_id)
```

### Service Layer
```python
from ..repositories.portfolio import PortfolioRepository
from ..schemas.portfolio import PortfolioCreate


class PortfolioService:
    def __init__(self, repo: PortfolioRepository):
        self._repo = repo

    async def list_by_user(self, user_id: str):
        return await self._repo.find_by_user(user_id)

    async def create(self, user_id: str, data: PortfolioCreate):
        return await self._repo.create(user_id=user_id, **data.model_dump())

    async def get_by_id(self, user_id: str, portfolio_id: str):
        portfolio = await self._repo.find_by_id(portfolio_id)
        if not portfolio or portfolio.user_id != user_id:
            raise NotFoundException("Portfolio not found")
        return portfolio
```

### Pydantic Schemas
```python
from pydantic import BaseModel
from datetime import datetime


class PortfolioCreate(BaseModel):
    name: str
    description: str | None = None


class PortfolioResponse(BaseModel):
    id: str
    name: str
    description: str | None
    user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PortfolioListResponse(BaseModel):
    portfolios: list[PortfolioResponse]
```

---

## Integration Test Template

```python
import pytest
from httpx import AsyncClient


@pytest.fixture
def auth_headers(test_user_token):
    return {"Authorization": f"Bearer {test_user_token}"}


async def test_create_portfolio(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/portfolios",
        json={"name": "My Portfolio", "description": "Test"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Portfolio"
    assert "id" in data


async def test_list_portfolios(client: AsyncClient, auth_headers):
    # Write first
    await client.post(
        "/api/v1/portfolios",
        json={"name": "Portfolio A"},
        headers=auth_headers,
    )
    # Then read
    resp = await client.get("/api/v1/portfolios", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["portfolios"]) >= 1


async def test_get_portfolio_401_without_token(client: AsyncClient):
    resp = await client.get("/api/v1/portfolios")
    assert resp.status_code == 401


async def test_create_portfolio_422_invalid_input(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/portfolios",
        json={},  # missing required "name"
        headers=auth_headers,
    )
    assert resp.status_code == 422
```

---

## Status Code Reference

| Action | Method | Success | Client error | Auth error |
|--------|--------|---------|-------------|------------|
| List | GET | 200 | 400 (bad query) | 401 / 403 |
| Get by ID | GET | 200 | 404 (not found) | 401 / 403 |
| Create | POST | 201 | 422 (validation) | 401 / 403 |
| Update | PUT/PATCH | 200 | 404 / 422 | 401 / 403 |
| Delete | DELETE | 204 | 404 | 401 / 403 |
| Conflict | POST/PUT | — | 409 | — |
