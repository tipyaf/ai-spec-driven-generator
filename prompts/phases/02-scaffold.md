# Phase 2: Scaffold

## Responsible agent
`developer`

## Objective
Create the project structure, install dependencies, and configure the development environment.

## Prerequisites
- Phase 1 (Plan) validated by the user
- Architecture plan available

## Instructions

You are in **Phase 2 — Scaffold**. You must create the project skeleton from the validated architecture plan.

### Step 1: Initialize the project
1. Create the project structure at the root of the project repository
2. Initialize with the correct tool (`npm init`, `cargo init`, `go mod init`, etc.)
3. Configure `package.json` / `pyproject.toml` / `go.mod` / etc.

### Step 2: Install dependencies
1. Install all production dependencies
2. Install development dependencies (test, lint, types)
3. Verify no version conflicts

### Step 3: Configure tools
1. TypeScript / compilation (`tsconfig.json`, etc.)
2. Linting (`eslint.config.js`, `biome.json`, `.ruff.toml`, etc.)
3. Formatting (prettier, etc.)
4. Testing (`vitest.config.ts`, `jest.config.js`, `pytest.ini`, etc.)
5. Git (`.gitignore`, `.gitattributes`)
6. Environment (`.env.example`)

### Step 4: Create folder structure
1. Create all folders defined in the architecture plan
2. Create `index.ts` / `__init__.py` / `mod.rs` export files
3. Create shared type/interface files

### Step 5: Entry point
1. Create the application entry point
2. Configure basic routing (if web)
3. Configure DB connection (if applicable)
4. Verify the project starts without errors

## Expected deliverable
- Project that compiles/starts without errors
- All dependencies installed
- Complete folder structure
- Tool configuration in place

## Validation criteria
- [ ] `npm run dev` / equivalent starts without errors
- [ ] `npm run build` / equivalent compiles without errors
- [ ] `npm run lint` / equivalent passes without errors
- [ ] Folder structure matches the plan
- [ ] `.env.example` is created with all documented variables
