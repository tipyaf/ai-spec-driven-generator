# Builder — Exchange Adapter Agent — Reference

> This file contains templates and examples. Load only when needed.

---

## Adapter Interface Template (ABC)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


@dataclass
class OrderRequest:
    symbol: str
    side: OrderSide
    quantity: Decimal
    order_type: OrderType = OrderType.MARKET
    price: Decimal | None = None  # Required for limit orders


@dataclass
class OrderResult:
    order_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    fill_price: Decimal | None
    status: str  # "filled", "partial", "open", "cancelled", "failed"


@dataclass
class Position:
    symbol: str
    side: OrderSide
    quantity: Decimal
    entry_price: Decimal
    unrealized_pnl: Decimal


@dataclass
class Balance:
    currency: str
    free: Decimal
    used: Decimal
    total: Decimal


class ExchangeAdapter(ABC):
    """Abstract exchange adapter — all concrete adapters implement this."""

    @abstractmethod
    async def place_order(self, request: OrderRequest) -> OrderResult:
        """Place an order and return the result. Never returns portfolio snapshot."""
        ...

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> OrderResult:
        """Cancel an order. Idempotent — cancelling already-cancelled returns success."""
        ...

    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str) -> OrderResult:
        """Query order status. Read-only — never mutates."""
        ...

    @abstractmethod
    async def get_position(self, symbol: str) -> Position | None:
        """Get current position for symbol. Read-only — never mutates."""
        ...

    @abstractmethod
    async def get_balances(self) -> list[Balance]:
        """Get all account balances. Read-only — never mutates."""
        ...

    @abstractmethod
    async def close_position(self, symbol: str) -> OrderResult:
        """Close position by placing a counter-order. Command — mutates state."""
        ...
```

---

## Factory Template

```python
from .base import ExchangeAdapter
from .okx_adapter import OkxAdapter
from ..config import ExchangeConfig


def create_exchange_adapter(config: ExchangeConfig) -> ExchangeAdapter:
    """Build the correct adapter from config. DI entry point."""
    adapters = {
        "okx": OkxAdapter,
        # Add new exchanges here — Open/Closed principle
    }

    adapter_cls = adapters.get(config.exchange_name.lower())
    if adapter_cls is None:
        raise ValueError(f"Unsupported exchange: {config.exchange_name}")

    if config.leverage > config.max_allowed_leverage:
        raise ValueError(
            f"Leverage {config.leverage}x exceeds allowed maximum "
            f"{config.max_allowed_leverage}x"
        )

    return adapter_cls(
        api_key=config.api_key,
        api_secret=config.api_secret,
        passphrase=config.passphrase,
        is_paper=config.is_paper,
    )
```

---

## Safety Checklist

### Before every commit, verify:

- [ ] **API keys never logged**: search all files for `log.*api_key`, `log.*secret`, `log.*passphrase` — zero matches
- [ ] **API keys never in error responses**: search all exception messages and response bodies — zero key references
- [ ] **API keys never cached**: no keys stored in Redis, no keys in session, no keys in URL params
- [ ] **Paper/live mode from config only**: mode determined by config at startup, no runtime override endpoint
- [ ] **Leverage enforced in factory**: factory raises error if config.leverage > max_allowed_leverage
- [ ] **Stop-loss atomic with entry**: entry order and stop-loss placed in same transaction/method — no window without protection
- [ ] **Circuit breaker present**: exchange errors trigger circuit breaker after threshold
- [ ] **Rate limiting**: order submission rate-limited per exchange requirements
- [ ] **Idempotent cancellation**: cancel_order on already-cancelled order returns success, not error
- [ ] **All endpoints have response_model**: no raw dict returns
- [ ] **Auth on all endpoints**: no public exchange endpoints
- [ ] **Order logging**: every place_order and cancel_order logged with timestamp, symbol, side, quantity
- [ ] **No secret in logs**: order logs contain order details but never API credentials

---

## Test Templates

### Unit Test — Order Parameter Validation
```python
import pytest
from decimal import Decimal
from app.exchange.base import OrderRequest, OrderSide, OrderType


def test_order_request_requires_price_for_limit():
    """Limit orders must have a price."""
    with pytest.raises(ValueError):
        validate_order(OrderRequest(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            quantity=Decimal("0.01"),
            order_type=OrderType.LIMIT,
            price=None,  # Missing price for limit order
        ))


def test_order_request_rejects_zero_quantity():
    """Quantity must be positive."""
    with pytest.raises(ValueError):
        validate_order(OrderRequest(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            quantity=Decimal("0"),
            order_type=OrderType.MARKET,
        ))
```

### Integration Test — Order Placement Flow
```python
async def test_place_order_and_verify_db(client, auth_headers, mock_exchange):
    """Place order via API, verify DB record matches."""
    mock_exchange.place_order.return_value = OrderResult(
        order_id="ex-123",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        quantity=Decimal("0.01"),
        fill_price=Decimal("50000.00"),
        status="filled",
    )

    resp = await client.post(
        "/api/v1/exchange/orders",
        json={"symbol": "BTC/USDT", "side": "buy", "quantity": "0.01"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["order_id"] == "ex-123"
    assert data["status"] == "filled"

    # Verify DB record
    db_order = await get_order_from_db(data["order_id"])
    assert db_order is not None
    assert db_order.fill_price == Decimal("50000.00")
```

### Paper/Live Mode Test
```python
async def test_paper_mode_uses_simulated_execution(paper_client, auth_headers):
    """Paper mode adapter uses simulated fills."""
    resp = await paper_client.post(
        "/api/v1/exchange/orders",
        json={"symbol": "BTC/USDT", "side": "buy", "quantity": "0.01"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    # Paper mode still returns valid order structure
    assert "order_id" in resp.json()


async def test_mode_not_overridable_by_caller(live_client, auth_headers):
    """API caller cannot switch paper/live mode via request."""
    resp = await live_client.post(
        "/api/v1/exchange/orders",
        json={"symbol": "BTC/USDT", "side": "buy", "quantity": "0.01", "paper": True},
        headers=auth_headers,
    )
    # Extra "paper" field should be ignored or rejected
    assert resp.status_code in (201, 422)
```

---

## Error Classification Template

```python
class ExchangeError(Exception):
    """Base exchange error."""
    pass


class RetryableExchangeError(ExchangeError):
    """Transient error — safe to retry (rate limit, timeout, network)."""
    pass


class FatalExchangeError(ExchangeError):
    """Permanent error — do NOT retry (invalid params, insufficient funds)."""
    pass


def classify_exchange_error(error_code: str, message: str) -> ExchangeError:
    """Map exchange-specific error to domain exception. ONE place per adapter."""
    retryable_codes = {"rate_limit", "timeout", "service_unavailable"}
    if error_code in retryable_codes:
        return RetryableExchangeError(message)
    return FatalExchangeError(message)
```
