# Phase 2: Scaffold

## Responsible agent
`developer`

## Objective
Create the project structure, install dependencies, and configure the development environment with strict code quality enforcement.

## Prerequisites
- Phase 1 (Plan) validated by the user
- Architecture plan available
- Stack profiles available (if generated in Phase 1)

## Instructions

You are in **Phase 2 — Scaffold**. You must create the project skeleton from the validated architecture plan.

### Step 1: Initialize the project
1. Create the project structure at the root of the project repository
2. Initialize with the correct tool (`npm init`, `cargo init`, `go mod init`, `poetry init`, etc.)
3. Configure `package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml` / etc.

### Step 2: Install dependencies
1. Install all production dependencies
2. Install development dependencies (test, lint, types)
3. Verify no version conflicts

### Step 3: Configure code quality tools

This step is **critical**. Every project MUST have linting, formatting, and static analysis configured with strict rules from day one.

#### 3.1 Linter & formatter — choose the best tools for the stack

**Research the current best practices** for your language/stack to select the most appropriate linter and formatter. For each tool you select, verify:
- It is actively maintained and widely adopted by the community
- It supports strict/opinionated rule sets (not just basic checks)
- It integrates with the project's editor and CI pipeline

Select **one linter** and **one formatter** (or a single tool that does both). If the language has a built-in linter or formatter (e.g., `go vet`, `rustfmt`, `dart analyze`), prefer it over third-party alternatives.

#### 3.2 Linter rules — apply strict best practices
Configure the linter with **strict rules**, not just defaults. Research the recommended rule set for your language and enable rules covering these categories:

- **Correctness**: unused imports/variables (error), unreachable code, type safety
- **Style**: consistent formatting, naming conventions, prefer immutable declarations
- **Suspicious**: no loose equality, no empty blocks, no assignments in conditions
- **Complexity**: prefer simple and readable patterns, limit nesting depth
- **Performance**: avoid known anti-patterns for the language
- **Security**: no code injection, no eval-equivalents, no hardcoded secrets

If the project has a **frontend**, also enable rules for:
- **Accessibility (a11y)**: alt text, semantic HTML, keyboard navigation
- **Framework-specific rules**: research the recommended lint plugin for your UI framework

If the project is a **monorepo**, use **overrides** to scope rules per app (e.g., no a11y rules in backend code).

#### 3.3 Formatter
- Prefer a tool that handles both linting and formatting if one exists for the language
- Otherwise configure a separate formatter
- Define explicit formatting rules: indent style, width, line length, quote style, trailing commas

#### 3.4 Editor configuration
Create a `.editorconfig` at the project root:
```ini
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true
```
Adjust `indent_size` for the language convention (4 for Python/Rust/Go, 2 for JS/TS/HTML/CSS).

#### 3.5 Pre-commit hooks (optional but recommended)
If the project uses git, set up pre-commit hooks to enforce lint + format on every commit. Research the standard pre-commit hook tool for your language/ecosystem.

#### 3.6 Static analysis / compiler strictness
Enable the **strictest compiler/analyzer settings** available for the language. Research the recommended strict mode flags for your compiler or type checker and enable them. The goal is to catch as many issues as possible at compile time rather than at runtime.

#### 3.7 Other tools
1. Testing framework (research the standard testing tool for your language)
2. Git (`.gitignore`, `.gitattributes`)
3. Environment (`.env.example` or equivalent)

### Step 4: Create folder structure
1. Create all folders defined in the architecture plan
2. Create barrel/export files as needed by the language (`index.ts`, `__init__.py`, `mod.rs`, `exports.dart`, etc.)
3. Create shared type/interface/model files

### Step 5: Internationalization (i18n)
If the project supports multiple languages (check the spec/architecture plan):
1. Install the i18n library appropriate for the stack (e.g., `next-intl`, `react-i18next`, `@adonisjs/i18n`, `go-i18n`, etc.)
2. Create the i18n configuration file
3. Create translation files for each supported language (e.g., `en.json`, `fr.json`)
4. Create a helper/hook to access translations in components (e.g., `useTranslations()`)
5. Wire the i18n provider into the app's root layout/entry point
6. Verify that a sample translation key renders correctly in each supported language

> **Why:** If i18n is deferred to a "polish" phase, all UI text gets hardcoded and must be extracted later — a costly, error-prone rewrite. Setting up i18n infrastructure during scaffold ensures every feature uses translation keys from day one.

### Step 6: Entry point
1. Create the application entry point
2. Configure basic routing (if web)
3. Configure DB connection (if applicable)
4. Verify the project starts without errors

### Step 7: Code quality gate (MANDATORY)
Before presenting results to the user, you MUST pass **all** quality checks below. Fix and re-run until every check passes.

#### 6.1 Static checks
1. Run the linter (`lint` command) — **must pass with zero errors**
2. Run the formatter — **must produce no changes** (all code already formatted)
3. Run the build/compile step — **must succeed with zero errors**

#### 6.2 Runtime checks
4. Start the dev server — **must start without errors**
5. **Smoke test every endpoint/route that exists** — send real HTTP requests (or equivalent for non-web projects) and verify you get the expected response. At minimum:
   - Health check / root route returns 200
   - If auth routes exist: test register, login, and authenticated endpoints with real HTTP requests
   - If a frontend exists: verify the main page loads and renders without errors
6. If any runtime check fails: **diagnose, fix the root cause, and re-run all checks**

> **Why runtime checks?** A project that compiles does not necessarily work. Missing middleware, missing dependencies, missing configuration files, and incorrect wiring are only caught by actually running the code and sending requests. **Never skip this step.**

#### 6.3 Dependency check
7. Verify all **peer dependencies** and **required runtime dependencies** are installed — not just that the build passes, but that every import resolves at runtime
8. For frameworks with plugins/providers: verify each registered provider has its required configuration file and dependencies

> **This is a blocking gate.** Do NOT present the scaffold as complete or request user validation until ALL checks pass — static, runtime, and dependency. This code quality gate applies to every subsequent phase as well (implement, test, review).

## Expected deliverable
- Project that compiles/starts without errors
- **All endpoints respond correctly to real requests** (not just compilation)
- All dependencies installed (including runtime-only deps like native modules)
- Complete folder structure
- **Strict linter configuration with language best practices**
- **Formatter configured and all code formatted**
- `.editorconfig` at root
- Tool configuration in place

## Validation criteria
- [ ] `lint` command passes with zero errors
- [ ] `build` / compile command succeeds
- [ ] `dev` command starts without errors
- [ ] **Smoke test passes** — all existing endpoints return expected responses
- [ ] **Every registered provider/plugin has its config file and dependencies**
- [ ] Linter rules cover: correctness, style, suspicious patterns, performance, security
- [ ] Frontend-specific rules (a11y, hooks) are enabled if applicable
- [ ] Monorepo overrides disable irrelevant rules per app (e.g., no a11y rules in backend)
- [ ] Folder structure matches the plan
- [ ] `.env.example` is created with all documented variables
- [ ] `.editorconfig` exists at root
- [ ] If multilingual: i18n infrastructure is in place and a sample key renders in each language
