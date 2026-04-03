# Builder — Frontend Agent — Reference

> This file contains templates and examples. Load only when needed.

---

## Component Template

### Page Component
```typescript
// pages/PortfolioListPage.tsx
import { usePortfolios } from "../hooks/usePortfolios";
import { PortfolioCard } from "../components/PortfolioCard";
import { LoadingSpinner } from "../components/shared/LoadingSpinner";
import { ErrorMessage } from "../components/shared/ErrorMessage";
import { EmptyState } from "../components/shared/EmptyState";

export function PortfolioListPage() {
  const { data, isLoading, error } = usePortfolios();

  if (isLoading) return <LoadingSpinner label="Loading portfolios..." />;
  if (error) return <ErrorMessage error={error} />;
  if (!data?.portfolios.length) return <EmptyState message="No portfolios yet" />;

  return (
    <main aria-label="Portfolio list">
      <h1>Portfolios</h1>
      <ul role="list">
        {data.portfolios.map((p) => (
          <li key={p.id}>
            <PortfolioCard portfolio={p} />
          </li>
        ))}
      </ul>
    </main>
  );
}
```

### Hook
```typescript
// hooks/usePortfolios.ts
import { useQuery } from "@tanstack/react-query";
import { portfolioApi } from "../api/portfolio";

export function usePortfolios() {
  return useQuery({
    queryKey: ["portfolios"],
    queryFn: portfolioApi.list,
  });
}
```

### API Client
```typescript
// api/portfolio.ts
import { httpClient } from "./client";
import type { PortfolioListResponse, PortfolioResponse } from "../types/portfolio";

export const portfolioApi = {
  list: async (): Promise<PortfolioListResponse> => {
    const { data } = await httpClient.get("/api/v1/portfolios");
    return data;
  },
  getById: async (id: string): Promise<PortfolioResponse> => {
    const { data } = await httpClient.get(`/api/v1/portfolios/${id}`);
    return data;
  },
};
```

### Dumb Component
```typescript
// components/PortfolioCard.tsx
import type { Portfolio } from "../types/portfolio";

interface PortfolioCardProps {
  portfolio: Portfolio;
}

export function PortfolioCard({ portfolio }: PortfolioCardProps) {
  return (
    <article aria-label={portfolio.name}>
      <h2>{portfolio.name}</h2>
      {portfolio.description && <p>{portfolio.description}</p>}
      <time dateTime={portfolio.created_at}>
        Created: {new Date(portfolio.created_at).toLocaleDateString()}
      </time>
    </article>
  );
}
```

---

## MSW Handler Template

### Basic Handler (from backend Pydantic schema)
```typescript
// mocks/handlers/portfolio.ts
import { http, HttpResponse } from "msw";

// Response shape MUST match backend Pydantic PortfolioListResponse
// Source of truth: backend/routers/portfolio.py + schemas/portfolio.py
export const portfolioHandlers = [
  http.get("*/api/v1/portfolios", () =>
    HttpResponse.json({
      portfolios: [
        {
          id: "uuid-1",
          name: "Growth Portfolio",
          description: "Long-term growth",
          user_id: "user-uuid",
          created_at: "2026-01-15T10:00:00Z",
        },
      ],
    })
  ),

  http.get("*/api/v1/portfolios/:id", ({ params }) =>
    HttpResponse.json({
      id: params.id,
      name: "Growth Portfolio",
      description: "Long-term growth",
      user_id: "user-uuid",
      created_at: "2026-01-15T10:00:00Z",
    })
  ),

  http.post("*/api/v1/portfolios", async ({ request }) => {
    const body = (await request.json()) as { name: string; description?: string };
    return HttpResponse.json(
      {
        id: "new-uuid",
        name: body.name,
        description: body.description ?? null,
        user_id: "user-uuid",
        created_at: "2026-04-04T12:00:00Z",
      },
      { status: 201 }
    );
  }),
];
```

### Error State Handlers
```typescript
// mocks/handlers/portfolio-errors.ts
import { http, HttpResponse } from "msw";

export const portfolioErrorHandlers = {
  serverError: http.get("*/api/v1/portfolios", () =>
    HttpResponse.json({ detail: "Internal server error" }, { status: 500 })
  ),

  unauthorized: http.get("*/api/v1/portfolios", () =>
    HttpResponse.json({ detail: "Not authenticated" }, { status: 401 })
  ),

  empty: http.get("*/api/v1/portfolios", () =>
    HttpResponse.json({ portfolios: [] })
  ),
};
```

---

## Behavior Test Template

```typescript
// __tests__/PortfolioListPage.test.tsx
import { render, screen } from "@testing-library/react";
import { server } from "../mocks/server";
import { portfolioHandlers } from "../mocks/handlers/portfolio";
import { portfolioErrorHandlers } from "../mocks/handlers/portfolio-errors";
import { PortfolioListPage } from "../pages/PortfolioListPage";
import { TestProviders } from "../test-utils/providers";

beforeEach(() => server.use(...portfolioHandlers));

test("displays portfolio list from API", async () => {
  render(<PortfolioListPage />, { wrapper: TestProviders });
  expect(await screen.findByText("Growth Portfolio")).toBeInTheDocument();
});

test("shows loading spinner initially", () => {
  render(<PortfolioListPage />, { wrapper: TestProviders });
  expect(screen.getByText("Loading portfolios...")).toBeInTheDocument();
});

test("shows error message on server error", async () => {
  server.use(portfolioErrorHandlers.serverError);
  render(<PortfolioListPage />, { wrapper: TestProviders });
  expect(await screen.findByRole("alert")).toBeInTheDocument();
});

test("shows empty state when no portfolios", async () => {
  server.use(portfolioErrorHandlers.empty);
  render(<PortfolioListPage />, { wrapper: TestProviders });
  expect(await screen.findByText("No portfolios yet")).toBeInTheDocument();
});
```

---

## File Structure Template

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts             # Shared HTTP client with base URL
│   │   └── portfolio.ts          # Portfolio API functions
│   ├── components/
│   │   ├── shared/               # Reusable dumb components
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorMessage.tsx
│   │   │   └── EmptyState.tsx
│   │   └── PortfolioCard.tsx
│   ├── hooks/
│   │   └── usePortfolios.ts
│   ├── pages/
│   │   └── PortfolioListPage.tsx
│   ├── types/
│   │   └── portfolio.ts          # Mirrors backend Pydantic schemas
│   ├── mocks/
│   │   ├── server.ts             # MSW server setup
│   │   └── handlers/
│   │       └── portfolio.ts      # MSW handlers from backend schemas
│   └── __tests__/
│       └── PortfolioListPage.test.tsx
```
