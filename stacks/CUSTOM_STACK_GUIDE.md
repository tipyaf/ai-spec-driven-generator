# Adding a Custom Stack Plugin (v5)

Framework v5 ships with four built-in stacks: `python-fastapi`, `typescript-react`,
`postgres`, `nodejs-express`. Any other language or framework (Go, Rust, Elixir,
Kotlin, Swift, …) is supported by authoring a **custom stack plugin** — no core
framework edits required.

Custom stacks live under your project's `_work/stacks/<name>/` and are activated
by declaring them in `_work/stacks/registry.yaml`.

---

## Table of contents

1. Minimal structure
2. The two mandatory files
3. Optional files
4. Declaring the stack in `registry.yaml`
5. Testing your stack locally
6. End-to-end example: `go-gin`

---

## 1. Minimal structure

```
_work/stacks/<your-stack>/
├── profile.yaml         # REQUIRED — commands, forbidden patterns, tools
├── ac-templates.yaml    # REQUIRED — AC-SEC / AC-BP auto-injected by refinement
├── smoke-boot.yaml      # OPTIONAL — G4.1 strategy (omit for library stacks)
├── checks/              # OPTIONAL — stack-specific Python check scripts
│   └── check_<rule>.py
└── README.md            # OPTIONAL but strongly recommended
```

Only `profile.yaml` and `ac-templates.yaml` are strictly required. Everything
else is opt-in.

---

## 2. The two mandatory files

### `profile.yaml` — required fields

| Field | Type | Description |
|---|---|---|
| `name` | string | Machine-readable id, lowercase, must match the directory name |
| `version` | string | Semver of this profile — bump when you change forbidden patterns |
| `languages` | `list[str]` | Primary languages (e.g. `[go]`, `[rust]`, `[kotlin, java]`) |
| `test_command` | string | One-shot test command the orchestrator runs for G2 |
| `build_command` | string | Build artefact command the orchestrator runs for G4 |
| `smoke_boot` | mapping | See `smoke-boot.yaml` below — can be inline here if short |

Strongly recommended (optional but used by several gates):

- `type_check_command`, `lint_command`, `test_coverage_command`
- `coverage: {line_min, branch_min, mutation_min}`
- `forbidden_patterns: [{regex, reason, severity, exclude?}]`
- `tools: {required, recommended, optional}`

### `ac-templates.yaml` — required sections

Two top-level sections — each is a list of AC objects:

```yaml
ac_sec:   # Security ACs (OWASP-style, framework-specific)
  - id: AC-SEC-<RULE>
    applies_to: [endpoint, service, …]   # story component types
    text: "One-sentence intent the dev must satisfy."
    verify: "command the validator runs, or 'static -- <manual check>'"

ac_bp:    # Best Practice ACs (idioms, patterns, hygiene)
  - id: AC-BP-<RULE>
    applies_to: [endpoint, handler, …]
    text: "..."
    verify: "..."
```

The refinement agent injects each AC whose `applies_to:` matches the story's
component list. `verify:` is executed literally by the validator during G5.

---

## 3. Optional files

- **`smoke-boot.yaml`** — G4.1 strategy. Required unless `spec.type` is `library`.
  Fields: `strategy`, `start_command`, `healthcheck.url`, `healthcheck.expect_status`,
  `teardown.signal`, `timeout_s`.
- **`checks/*.py`** — stack-specific enforcement scripts. Must be executable
  Python 3 (no shebang needed, orchestrator runs them via `python3 <path>`).
  Declared in `profile.yaml: checks:` so the orchestrator knows when to run them.
- **`migration-strategy.yaml`** — only for data stacks (like `postgres`).

---

## 4. Declaring the stack in `registry.yaml`

Edit `_work/stacks/registry.yaml` and add an entry under `stacks:`:

```yaml
stacks:
  - name: go-gin
    source: _work/stacks/go-gin           # relative to project root
    profile: _work/stacks/go-gin/profile.yaml
    ac_templates: _work/stacks/go-gin/ac-templates.yaml
    smoke_boot: _work/stacks/go-gin/smoke-boot.yaml
    enabled: true
```

The orchestrator loads the stack on its next `/build` — no restart, no install.

---

## 5. Testing your stack locally

Run the stack-plugin conformance test against your new stack:

```bash
cd framework
.venv-sdd-dev/bin/pytest tests/test_stack_plugins.py::test_custom_stack \
    --custom-stack-path=/path/to/project/_work/stacks/go-gin -v
```

Smoke-check end-to-end by running a dry `/build` on a small story:

```bash
python3 framework/scripts/orchestrator.py --mode build --story sc-xxxx
```

Inspect the orchestrator log — every loaded stack is echoed at startup.

---

## 6. End-to-end example: `go-gin`

Below is a minimal but realistic custom stack for Go + Gin.

### `_work/stacks/go-gin/profile.yaml`

```yaml
name: go-gin
version: 1.0
languages: [go]
min_version: "1.21"

test_command: "go test ./..."
test_coverage_command: "go test -coverprofile=coverage.out ./..."
build_command: "go build -o bin/server ./cmd/server"
type_check_command: "go vet ./..."
lint_command: "golangci-lint run"

coverage:
  line_min: 80
  branch_min: 0        # Go coverage is line-only
  mutation_min: 70     # via go-mutesting

forbidden_patterns:
  - regex: "fmt\\.Sprintf\\(`SELECT"
    reason: "SQL injection: use database/sql parameter binding or sqlx"
    severity: error
  - regex: "panic\\("
    reason: "panics should never escape a handler — return an error instead"
    severity: error
    exclude: ["_test.go", "main.go"]
  - regex: "c\\.String\\(\\s*\\d+\\s*,\\s*req\\.URL\\.Query\\(\\)"
    reason: "echoing query params unsanitized enables XSS — use c.JSON or template-escape"
    severity: error

smoke_boot:
  strategy: go_healthcheck
  start_command: "./bin/server"
  healthcheck_url: "http://localhost:8080/health"
  timeout_s: 30

tools:
  required: [go, golangci-lint]
  recommended: [govulncheck, go-mutesting]

checks: []
```

### `_work/stacks/go-gin/ac-templates.yaml`

```yaml
ac_sec:
  - id: AC-SEC-GIN-INPUT-BIND
    applies_to: [handler, endpoint]
    text: "Request bodies bound via c.ShouldBindJSON with struct validation tags."
    verify: "grep -rnE 'c\\.ShouldBindJSON' internal/handlers/"
  - id: AC-SEC-GIN-CSRF
    applies_to: [middleware, server]
    text: "CSRF middleware configured on state-changing routes."
    verify: "grep -rn 'csrf' internal/middleware/"
  - id: AC-SEC-GIN-SQL-PARAMS
    applies_to: [repository]
    text: "All queries use parameter placeholders ($1, $2…) — never fmt.Sprintf."
    verify: "grep -rnE 'fmt\\.Sprintf\\(`SELECT|`INSERT|`UPDATE|`DELETE' internal/ || exit 0 && exit 1"

ac_bp:
  - id: AC-BP-GIN-ERROR-RETURN
    applies_to: [handler]
    text: "Handlers return errors to the middleware chain — no c.AbortWithStatus mid-handler without c.Error."
    verify: "grep -rn 'c\\.Error' internal/handlers/"
  - id: AC-BP-GIN-CONTEXT-TIMEOUT
    applies_to: [handler]
    text: "Long-running handlers use context.WithTimeout from c.Request.Context()."
    verify: "grep -rn 'context\\.WithTimeout' internal/handlers/"
```

### Register in `_work/stacks/registry.yaml`

```yaml
stacks:
  - name: go-gin
    source: _work/stacks/go-gin
    profile: _work/stacks/go-gin/profile.yaml
    ac_templates: _work/stacks/go-gin/ac-templates.yaml
    smoke_boot: _work/stacks/go-gin/smoke-boot.yaml
    enabled: true
```

That's it — the refinement agent will start injecting `AC-SEC-GIN-*` and
`AC-BP-GIN-*` into every Go-touching story, the validator will run their
`verify:` commands, and the orchestrator will boot + healthcheck your Gin
server in G4.1.

---

## Where to get help

- Framework built-in stacks are excellent references: `stacks/templates/*/`.
- Read `stacks/stack-profile-template.md` for field-by-field documentation.
- Ask on the SDD community channel — custom stacks are how the framework grows.
