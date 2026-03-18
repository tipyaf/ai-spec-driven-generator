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

## Validation criteria
- [ ] CI pipeline passes (lint, test, build)
- [ ] Dockerfile builds without errors (if applicable)
- [ ] README is complete and up to date
- [ ] All environment variables are documented
- [ ] Deployment is documented step by step
