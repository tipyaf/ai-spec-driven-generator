---
name: scan
description: Run the code-quality scanner (SonarQube or stack-declared tool). Default scans local diff vs main; --full scans the whole repository; --report fetches the latest status without launching a new scan. Replaces v4 /scan + /scan-full + /sonar.
---

# /scan

## Usage
/scan [--full] [--report]

## What it does

Single entry point for code-quality scanning. The default is a fast scan of files changed vs `main`. Flags widen the scope:

| Invocation | Behaviour |
|---|---|
| `/scan` | Scan local diff only (staged + unstaged vs `origin/main`). |
| `/scan --full` | Scan the entire repository. |
| `/scan --report` | Read-only: fetch current quality gate + key metrics from the scanner API without relaunching a scan. |

`--full` and `--report` are mutually exclusive; `--report` wins if both are given (with a warning).

## How it works

1. Read SonarQube credentials from `.env` then shell env (`SONAR_TOKEN`, `SONAR_HOST_URL`, `SONAR_PROJECT_KEY`).
2. Resolve the scope:
   - Default: `git diff origin/main --name-only --diff-filter=ACMR`.
   - `--full`: `sonar.sources=.`.
   - `--report`: `GET /api/qualitygates/project_status` + `/api/measures/component`.
3. Invoke `sonar-scanner` (or `npx sonar-scanner`) with the computed inclusions, or call the API directly for `--report`.
4. Poll `/api/ce/activity` until analysis finishes (scan modes only).
5. Parse results and render a concise markdown report via `ui_messages.py`.
6. Suggest an actionable follow-up (e.g. "create a fix story for X critical issues") when non-zero.

## Arguments

None positional.

## Flags

| Flag | Description |
|---|---|
| `--full` | Scan the entire repository (heavier). |
| `--report` | Fetch status without triggering a new scan. |

## Exit conditions

- **0**: scan completed, quality gate PASS.
- **1**: quality gate FAIL or scanner error.
- **3**: credentials missing or scanner binary not installed.

## Files read / written

- Reads: `.env` (credentials), git state.
- Writes: nothing (scanner server holds the results).

## Migration from v4

| v4 command | v5 equivalent |
|---|---|
| `/scan` | `/scan` (unchanged) |
| `/scan-full` | `/scan --full` |
| `/sonar` | `/scan --report` |

Old skill directories (`skills/scan-full/`, `skills/sonar/`) are removed. Historical references in docs should be updated. Users who still type `/scan-full` or `/sonar` will get an "unknown command — did you mean `/scan --full`?" suggestion from `/help`.

## Related

- `/build` — G3 Code quality gate uses the same tool.
- `/status` — shows the latest scan result when available.
