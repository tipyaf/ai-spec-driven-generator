# DevOps Reference — Templates

## Docker Template

```dockerfile
# Optimized multi-stage Dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS production
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

## CI/CD Pipeline Template

```yaml
# GitHub Actions workflow
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test

  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build

  deploy:
    needs: [build]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # Deploy to staging first, then production
      - run: echo "Deploy steps here"
```

## Environment Variables Table Template

```markdown
## Environment Variables

### Required
| Variable | Description | Example |
|----------|------------|---------|
| DATABASE_URL | DB connection URL | postgres://user:pass@host:5432/db |
| API_KEY | External API key | sk-... |

### Optional
| Variable | Description | Default |
|----------|------------|---------|
| LOG_LEVEL | Log verbosity | info |
| PORT | Server port | 3000 |
```

## Utility Scripts Template

```json
{
  "scripts": {
    "dev": "...",
    "build": "...",
    "start": "...",
    "test": "...",
    "lint": "...",
    "db:migrate": "...",
    "db:seed": "..."
  }
}
```

## Deployment Guide Template

```markdown
## Deployment Guide

### Prerequisites
- [list of required tools/access]

### First deployment
1. [initial setup steps]
2. [configuration steps]
3. [deploy command]
4. [verification steps]

### Subsequent deployments
1. [deploy command]
2. [verification steps]

### Rollback
1. [identify the issue]
2. [rollback command/steps]
3. [verify rollback succeeded]

### Post-deploy checklist
- [ ] Health endpoint returns 200
- [ ] Smoke test critical paths
- [ ] Check error rate in logs
- [ ] Verify env vars are set correctly
- [ ] Monitor for 15 minutes post-deploy
```
