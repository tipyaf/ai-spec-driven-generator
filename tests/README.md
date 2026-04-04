# Framework Self-Tests

Automated tests that validate the SSD framework itself — agents, skills, scripts, rules, templates, and data flow contracts. These tests run before every commit via a pre-commit hook.

## Setup

```bash
# Install the pre-commit hook (one-time, after cloning)
./scripts/setup-hooks.sh

# Install Python dependency
pip install pytest
```

After setup, **tests run automatically before every commit**. If any test fails, the commit is blocked.

## Manual run

```bash
# Full suite (151 tests)
pytest tests/framework/ -v

# By category
pytest tests/framework/test_pipeline.py -v     # Complete /build pipeline
pytest tests/framework/test_dataflow.py -v      # Data flow contracts
pytest tests/framework/test_crossrefs.py -v     # File reference integrity
pytest tests/framework/test_scripts.py -v       # Enforcement scripts
pytest tests/framework/test_models.py -v        # Agent model consistency
pytest tests/framework/test_agnostic.py -v      # Language-agnostic compliance

# Single test
pytest tests/framework/test_pipeline.py::TestRedPhase -v
```

## What each file tests

| File | Count | What it validates |
|------|-------|-------------------|
| `test_pipeline.py` | 51 | Full /build pipeline: prerequisites, setup, build file creation, dependency map, RED phase (4 steps), GREEN phase (3 steps), post-build, 7 quality gates, verdict logic, artefact checklist, stale detection, phase ordering, CLAUDE.md consistency |
| `test_scripts.py` | 50 | All 9 enforcement scripts: Python syntax, `main()` function, `if __name__` guard, CLI args (`--story`, `--spec-path`, `--require-ui-intentions`), config keys, dead code detection |
| `test_dataflow.py` | 21 | Producer/consumer contracts: test_intentions (story file, not spec overlay), dependency_map fields, 7 gates schema, AC verify: flow |
| `test_crossrefs.py` | 16 | File path references in agents, skills, rules all resolve to real files; enforcement scripts listed in CLAUDE.md |
| `test_models.py` | 8 | Every agent has valid frontmatter (name, description, model), CLAUDE.md model table matches agent defaults, .ref.md files exist when referenced |
| `test_agnostic.py` | 5 | Templates and build skill contain no hardcoded language-specific commands outside examples |

## How the pre-commit hook works

The hook only triggers when framework files are staged:

```
agents/  skills/  rules/  scripts/  specs/templates/  stacks/  tests/framework/
```

If none of these directories are in the commit, the hook exits immediately (no delay).

To bypass in an emergency:
```bash
git commit --no-verify
```

## When to update tests

| Framework change | Tests affected | Action |
|---|---|---|
| Rename/remove an agent or script | `test_crossrefs`, `test_models` | Tests catch it — fix framework or update test |
| Add a new agent | `test_models` may miss it | Add to `AGENT_DISPLAY_NAMES` if it should be in CLAUDE.md table |
| Change gate count or order | `test_pipeline`, `test_dataflow` | Update `GATE_DESCRIPTIONS` and expected count |
| Move data between files (e.g. test_intentions) | `test_dataflow` | Tests catch it — this is the exact bug class they prevent |
| Add a new enforcement script | `test_scripts`, `test_crossrefs` | Add to `ALL_CHECK_SCRIPTS` list |
| Change CLI args on a script | `test_scripts` | Update the arg expectations |
| Add language-specific content to a template | `test_agnostic` | Tests catch it — intended |
