# Phase 6: Deploy Config

## Responsible agent
`devops`

## Objective
Prepare the project for deployment: CI/CD, containerization, documentation.

## Prerequisites
- Phase 5 (Review) validated
- Audited and corrected code

## Instructions

You are in **Phase 6 — Deployment configuration**. You must prepare everything needed to deploy the project.

### Step 1: Dockerfile (if applicable)
1. Create an optimized multi-stage Dockerfile
2. Create a `docker-compose.yml` for local dev (if DB/services)
3. Create a `.dockerignore`

### Step 2: CI/CD
1. Create the CI workflow adapted to the provider (GitHub Actions by default)
2. Jobs: lint → test → build → deploy
3. Configure required secrets (documented, not values)
4. Configure automatic deployment (staging on PR, prod on main)

### Step 3: Environment configuration
1. Document all environment variables
2. Create complete `.env.example`
3. Document values per environment (dev, staging, prod)

### Step 4: Documentation
1. Create/update README.md with:
   - Project description
   - Prerequisites
   - Installation
   - Development
   - Tests
   - Deployment
2. Document the API (if applicable) — OpenAPI/Swagger or markdown

### Step 5: Scripts
1. Verify all npm/make scripts are in place
2. Add missing scripts (db:migrate, db:seed, etc.)

### Step 6: Deployment verification

After deploying to any environment, verify:

#### For all project types:
1. **Build succeeds** — CI/CD pipeline completes without errors
2. **Health check** — application responds on expected port/URL
3. **Smoke test** — core functionality works (login, main feature, API responds)
4. **Logs clean** — no error-level logs in the first 5 minutes

#### For web projects:
5. **Pages load** — key pages return 200 status
6. **Assets served** — CSS/JS/images load correctly
7. **SSL valid** — HTTPS certificate is valid and not expiring soon

#### For API projects:
5. **Endpoints respond** — key endpoints return expected status codes
6. **Auth works** — protected routes reject unauthenticated requests
7. **Response time** — p95 latency within acceptable range

#### For CLI projects:
5. **Binary runs** — CLI tool executes with --help flag
6. **Core commands work** — main commands produce expected output

#### For containerized deployments:
5. **Containers running** — all containers are in "running" state
6. **Container health** — health checks pass
7. **Resource usage** — CPU/memory within expected bounds
8. **Rebuild reminder** — flag if containers need rebuild after code changes

### Rollback plan
Document the rollback procedure BEFORE deploying:
1. Previous working version/commit/tag
2. Rollback command (e.g., `git revert`, `kubectl rollout undo`, redeploy previous tag)
3. Database migration rollback (if applicable)
4. Time estimate for rollback

### Post-deploy monitoring
Define what to monitor in the first 24 hours:
1. Error rate
2. Response times
3. Resource usage
4. User-facing errors

## Validation criteria
- [ ] CI pipeline passes (lint, test, build)
- [ ] Dockerfile builds without errors (if applicable)
- [ ] README is complete and up to date
- [ ] All environment variables are documented
- [ ] Deployment is documented step by step
- [ ] Deployment succeeds on target environment
- [ ] Health checks pass
- [ ] Smoke tests pass
- [ ] Rollback plan documented
- [ ] No error-level logs after deployment
