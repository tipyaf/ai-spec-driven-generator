# Stack Profile Template (v5)

> **v5 change**: stack profiles are now **directories** containing YAML files.
> The former single `.md` file became the stack's `README.md`. Machine-consumable
> config moved to `profile.yaml`, `ac-templates.yaml`, and optionally
> `smoke-boot.yaml` / `migration-strategy.yaml` / `checks/*.py`.
>
> See `stacks/CUSTOM_STACK_GUIDE.md` for a step-by-step authoring guide with a
> full `go-gin` example.

---

## Directory layout

```
stacks/templates/<stack-name>/         # framework-provided stacks
_work/stacks/<stack-name>/             # project-provided custom stacks
├── profile.yaml           [REQUIRED] commands, forbidden patterns, coverage
├── ac-templates.yaml      [REQUIRED] ac_sec + ac_bp auto-injected by refinement
├── smoke-boot.yaml        [OPTIONAL] G4.1 boot strategy (omit for library stacks)
├── migration-strategy.yaml[OPTIONAL] only for data stacks (see postgres)
├── checks/                [OPTIONAL] stack-specific Python enforcement scripts
│   └── check_<rule>.py
└── README.md              [RECOMMENDED] human-facing coding standards & examples
```

---

## `profile.yaml` — required fields

| Field | Type | Description |
|---|---|---|
| `name` | string | Machine id, lowercase, must match directory name |
| `version` | string | Semver of the profile — bump on breaking forbidden-pattern changes |
| `languages` | list[str] | Primary languages (e.g. `[python]`, `[go]`, `[kotlin, java]`) |
| `test_command` | string | One-shot test command, run by the orchestrator for G2 |
| `build_command` | string | Build artefact command, run for G4 |
| `smoke_boot` | mapping | Inline G4.1 strategy OR reference to `smoke-boot.yaml` |

### Optional but recommended

- `min_version` — minimum language/framework major version
- `test_coverage_command`, `type_check_command`, `lint_command`, `format_command`
- `coverage: {line_min: int, branch_min: int, mutation_min: int}`
- `forbidden_patterns: [{regex, reason, severity, exclude?}]`
- `tools: {required: [...], recommended: [...], optional: [...]}`
- `checks: [{id, script, runs_on, description}]`
- `conventions: {source_dir, test_dir, entrypoint, ...}`

---

## `ac-templates.yaml` — required sections

Two top-level sections, each a list of AC objects:

```yaml
ac_sec:   # Security ACs
  - id: AC-SEC-<RULE-ID>
    applies_to: [endpoint, service, query, ...]   # story component kinds
    text: "One-sentence intent."
    verify: "command run by validator, or 'static -- description'"

ac_bp:    # Best Practice ACs
  - id: AC-BP-<RULE-ID>
    applies_to: [...]
    text: "..."
    verify: "..."
```

**Required IDs**: at least one `AC-SEC-*` and at least one `AC-BP-*` must exist.
This is enforced by `tests/test_stack_plugins.py`.

The refinement agent injects each AC whose `applies_to:` intersects the story's
component list. `verify:` is executed literally by the validator during G5
(Tier 1 ACs) — so prefer executable commands over `static --` descriptions when
mechanically possible.

---

## `smoke-boot.yaml` — optional (G4.1)

Declares how the orchestrator verifies the artefact boots and responds.

```yaml
strategy: <uvicorn_healthcheck | node_healthcheck | vite_preview_healthcheck | ...>
start_command: "..."
pre_boot_command: null        # optional: build step before boot
working_dir: "."
env: {KEY: "value"}
healthcheck:
  url: "http://localhost:PORT/health"
  expect_status: 200
  method: GET
  poll_interval_s: 1
  timeout_s: 30
teardown:
  signal: SIGTERM
  grace_period_s: 5
```

Omit this file for library stacks where "boot" doesn't apply — G4.1 is then
skipped for that stack.

---

## `checks/` — optional stack-specific scripts

Python 3 scripts run by the orchestrator when their trigger matches. Declared
in `profile.yaml`:

```yaml
checks:
  - id: my-rule
    script: checks/check_my_rule.py
    runs_on: [change, story, review]   # when the orchestrator dispatches this
    description: "one-line intent"
```

Built-in examples:
- `stacks/templates/typescript-react/checks/check_msw_contracts.py`
- `stacks/templates/postgres/checks/check_write_coverage.py`

---

## `README.md` — human documentation

Free-form Markdown with:
- Language + framework versions targeted
- Security / best-practice highlights (summarize what's in `ac-templates.yaml`)
- Forbidden patterns table with rationale
- Naming conventions
- Canonical test patterns
- Story refiner instructions

---

## Story Refiner interaction

When refining a story the Story Refiner MUST:

1. Load `ac-templates.yaml` for every `enabled` stack in `_work/stacks/registry.yaml`.
2. Inject each AC whose `applies_to:` intersects the story's component list.
3. Substitute placeholders (`<module>`, `<component>`, `<service>`, `<router>`, etc.)
   with actual file/module names for this story.
4. Add project-specific overrides AFTER the standard items — never replace them.
5. Add story-specific AC-FUNC-* items in the `### Functional (AC-FUNC-*)` section.

> **Note**: Test intention templates (Trigger A for computed values, Trigger C
> for UI rendering) are handled by the refinement agent's playbook, not by
> stack profiles. Stack profiles only provide `AC-SEC` and `AC-BP` templates.
