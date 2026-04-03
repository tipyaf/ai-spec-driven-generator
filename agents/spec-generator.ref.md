# Spec Generator Agent — Reference

> This file contains templates and examples. Load only when needed.

---

## Overlay Merge Example

### Baseline (`_work/spec/initial.yaml`)
```yaml
backend:
  services:
    - name: api-gateway
      port: 8000
      endpoints:
        - method: GET
          path: /api/v1/bots
          auth: true
          status: 200
          description: List all bots
        - method: POST
          path: /api/v1/bots
          auth: true
          status: 201
          description: Create bot

persistence:
  tables:
    - name: bots
      schema: public
      columns:
        - name: id
          type: uuid
          nullable: false
          default: gen_random_uuid()
        - name: name
          type: varchar(100)
          nullable: false
```

### Story Overlay (`_work/spec/feat-portfolio.yaml`)
```yaml
backend:
  services:
    - name: api-gateway
      endpoints:
        - method: GET
          path: /api/v1/portfolios
          auth: true
          status: 200
          description: List portfolios
        - method: GET
          path: /api/v1/portfolios/:id
          auth: true
          status: 200
          description: Get portfolio by ID

persistence:
  tables:
    - name: portfolios
      schema: public
      columns:
        - name: id
          type: uuid
          nullable: false
          default: gen_random_uuid()
        - name: user_id
          type: uuid
          nullable: false
          references: auth.users.id
```

### Merged Result
The `api-gateway` service now has 4 endpoints (2 original + 2 from overlay). The `portfolios` table is appended to the tables array. The `bots` table is unchanged.

---

## Markdown Output Template

### Endpoint Table
```markdown
## API Endpoints

### api-gateway (port 8000)

| Method | Path | Auth | Role | Status | Description |
|--------|------|------|------|--------|-------------|
| GET | /api/v1/bots | Y | -- | 200 | List all bots |
| POST | /api/v1/bots | Y | -- | 201 | Create bot |
| GET | /api/v1/portfolios | Y | -- | 200 | List portfolios |
| GET | /api/v1/portfolios/:id | Y | -- | 200 | Get portfolio by ID |
```

### Database Table
```markdown
## Database Tables

### public.bots

| Column | Type | Nullable | Default | References |
|--------|------|----------|---------|------------|
| id | uuid | No | gen_random_uuid() | -- |
| name | varchar(100) | No | -- | -- |

### public.portfolios

| Column | Type | Nullable | Default | References |
|--------|------|----------|---------|------------|
| id | uuid | No | gen_random_uuid() | -- |
| user_id | uuid | No | -- | auth.users.id |
```

### Redis Streams
```markdown
## Redis Streams

| Stream key | Producers | Consumers | Retention |
|-----------|-----------|-----------|-----------|
| stream:trades | trader | notification-service | 30 days |
```

### Docker Services
```markdown
## Docker Services

| Service | Image | Port | Depends on | Health check |
|---------|-------|------|------------|-------------|
| api | python:3.11-slim | 8000 | postgres, redis | GET /health |
```

---

## Domain-to-File Mapping

| Domain key | Output file |
|-----------|------------|
| overview | _docs/spec/overview.md |
| backend | _docs/spec/backend.md |
| persistence | _docs/spec/persistence.md |
| frontend | _docs/spec/frontend.md |
| exchanges | _docs/spec/exchanges.md |
| execution | _docs/spec/execution.md |
| infrastructure | _docs/spec/infrastructure.md |
| quality | _docs/spec/quality.md |
| mobile | _docs/spec/mobile.md |
| open_items | _docs/spec/open_items.md |

---

## Summary Report Template

```markdown
## Spec Generation Summary

- **Scope**: full / backend / feat-portfolio
- **Files regenerated**: 3
  - _docs/spec/backend.md: 66 endpoints across 2 services
  - _docs/spec/persistence.md: 12 tables
  - _docs/spec/frontend.md: 8 pages, 24 components
- **Overlays merged**: feat-portfolio, feat-dashboard
- **Errors**: none
```
