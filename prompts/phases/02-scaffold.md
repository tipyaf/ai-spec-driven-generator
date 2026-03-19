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

#### 3.1 Linter — choose the best tool for the stack

Pick the standard linter for your language. The table below covers common stacks — **if your language is not listed, research and use the community-standard linter for that language** and apply the same strict configuration principles described in 3.2.

| Language/Stack | Recommended linter | Formatter | Config file |
|---|---|---|---|
| TypeScript/JavaScript | Biome (preferred) or ESLint | Biome (built-in) or Prettier | `biome.json` / `eslint.config.js` |
| Python | Ruff | Ruff (built-in) or Black | `ruff.toml` / `pyproject.toml` |
| Rust | Clippy (built-in) | rustfmt (built-in) | `clippy.toml` / `rustfmt.toml` |
| Go | golangci-lint | gofmt / goimports (built-in) | `.golangci.yml` |
| Java | Checkstyle or SpotBugs | google-java-format or Spotless | `checkstyle.xml` / `build.gradle` |
| Kotlin | ktlint or detekt | ktlint (built-in) | `.editorconfig` / `detekt.yml` |
| C# / .NET | dotnet-format + Roslyn analyzers | dotnet-format (built-in) | `.editorconfig` / `Directory.Build.props` |
| F# | Fantomas | Fantomas (built-in) | `.editorconfig` / `.fantomasconfig` |
| Dart / Flutter | dart analyze (built-in) | dart format (built-in) | `analysis_options.yaml` |
| Swift | SwiftLint | SwiftFormat | `.swiftlint.yml` / `.swiftformat` |
| Ruby | RuboCop | RuboCop (built-in) | `.rubocop.yml` |
| PHP | PHPStan + PHP-CS-Fixer | PHP-CS-Fixer (built-in) | `phpstan.neon` / `.php-cs-fixer.php` |
| Elixir | Credo | mix format (built-in) | `.credo.exs` / `.formatter.exs` |
| Scala | Scalafix + WartRemover | Scalafmt | `.scalafix.conf` / `.scalafmt.conf` |
| C / C++ | clang-tidy | clang-format | `.clang-tidy` / `.clang-format` |
| Zig | zig fmt (built-in) | zig fmt (built-in) | `build.zig` |

> **Not in the table?** Use the most widely adopted linter + formatter for your language. Check the language's official documentation or community best practices. The rules in section 3.2 still apply — adapt them to your linter's terminology.

#### 3.2 Linter rules — apply strict best practices
Configure the linter with **strict rules**, not just defaults. At minimum:

- **Correctness**: unused imports (error), unused variables (error), no unreachable code
- **Style**: consistent formatting (quotes, semicolons, indentation), consistent naming conventions, prefer const/immutable, use template literals over concatenation
- **Suspicious**: no explicit `any`/equivalent (warn), no double equals, no empty blocks, no assignments in expressions
- **Complexity**: prefer flat map, optional chaining, no useless fragments
- **Performance**: no accumulating spread in loops, prefer efficient patterns
- **Security**: no dangerous HTML injection, no eval, no hardcoded secrets

If the project has a **frontend** (React, Vue, Svelte, etc.), also enable:
- **Accessibility (a11y)**: alt text, button types, valid anchors, keyboard events
- **Hooks rules**: exhaustive dependencies (warn), hooks at top level (error)
- **Security**: no `dangerouslySetInnerHTML` or equivalent

If the project is a **monorepo** with backend + frontend, use **overrides** to disable frontend-only rules (a11y, hooks, etc.) in backend code.

#### 3.3 Formatter
- Use the linter's built-in formatter if available (Biome, Ruff, rustfmt)
- Otherwise configure a separate formatter (Prettier, gofmt, etc.)
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
If the project uses git, consider setting up pre-commit hooks to enforce lint + format on every commit:
- **Node.js / TypeScript**: husky + lint-staged
- **Python**: pre-commit framework (`pre-commit`)
- **Rust**: cargo-husky
- **Go**: pre-commit or lefthook
- **.NET / C#**: husky.net or dotnet-format as a git hook
- **Dart / Flutter**: `dart_pre_commit` or custom shell hook running `dart analyze && dart format`
- **Java / Kotlin**: Spotless Gradle plugin with `check` task, or pre-commit
- **Ruby**: overcommit or lefthook
- **Multi-language / other**: lefthook (language-agnostic, single YAML config)

#### 3.6 Static analysis / compiler strictness
Enable the strictest compiler/analyzer settings available for the language:
- **TypeScript**: `strict: true` in `tsconfig.json`
- **C# / .NET**: `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>`, `<Nullable>enable</Nullable>`, enable Roslyn analyzers
- **Dart / Flutter**: `strict-casts: true`, `strict-inference: true`, `strict-raw-types: true` in `analysis_options.yaml`
- **Rust**: `#![deny(warnings)]`, `#![deny(clippy::all)]`
- **Go**: `go vet`, enable all golangci-lint checks
- **Java**: `-Xlint:all`, SpotBugs with high effort
- **Python**: `mypy --strict` or pyright strict mode
- **Other languages**: enable the equivalent strict/pedantic compiler flags

#### 3.7 Other tools
1. Testing framework (Vitest, Jest, pytest, cargo test, go test, xUnit, flutter test, etc.)
2. Git (`.gitignore`, `.gitattributes`)
3. Environment (`.env.example` or equivalent)

### Step 4: Create folder structure
1. Create all folders defined in the architecture plan
2. Create barrel/export files as needed by the language (`index.ts`, `__init__.py`, `mod.rs`, `exports.dart`, etc.)
3. Create shared type/interface/model files

### Step 5: Entry point
1. Create the application entry point
2. Configure basic routing (if web)
3. Configure DB connection (if applicable)
4. Verify the project starts without errors

### Step 6: Code quality gate (MANDATORY)
Before presenting results to the user, you MUST pass the code quality gate:

1. Run the linter (`lint` command) — **must pass with zero errors**
2. Run the formatter — **must produce no changes** (all code already formatted)
3. Run the build/compile step — **must succeed with zero errors**
4. Run the dev server — **must start without errors**
5. If any of the above fails: **fix the issues immediately and re-run until all pass**

> **This is a blocking gate.** Do NOT present the scaffold as complete or request user validation until lint, format, build, and dev all pass cleanly. This code quality gate applies to every subsequent phase as well (implement, test, review).

## Expected deliverable
- Project that compiles/starts without errors
- All dependencies installed
- Complete folder structure
- **Strict linter configuration with language best practices**
- **Formatter configured and all code formatted**
- `.editorconfig` at root
- Tool configuration in place

## Validation criteria
- [ ] `lint` command passes with zero errors
- [ ] `build` / compile command succeeds
- [ ] `dev` command starts without errors
- [ ] Linter rules cover: correctness, style, suspicious patterns, performance, security
- [ ] Frontend-specific rules (a11y, hooks) are enabled if applicable
- [ ] Monorepo overrides disable irrelevant rules per app (e.g., no a11y rules in backend)
- [ ] Folder structure matches the plan
- [ ] `.env.example` is created with all documented variables
- [ ] `.editorconfig` exists at root
