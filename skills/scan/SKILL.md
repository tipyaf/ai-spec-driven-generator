---
name: scan
description: Run SonarQube scanner on local changes only. Analyzes staged and modified files vs. the main branch, returns a concise quality report suitable for creating fix stories.
---

## Overview

Run SonarQube analysis scoped to local changes only (staged + unstaged files in the current branch vs. main).

## Prerequisites

- `sonar-scanner` or `npx sonar-scanner` must be available
- Environment variables set: `SONAR_TOKEN`, `SONAR_HOST_URL`, `SONAR_PROJECT_KEY`

## Workflow

1. **Get list of changed files**:
   ```bash
   git diff origin/main --name-only --diff-filter=ACMR
   ```

2. **Read environment variables**:
   ```bash
   # Use environment variables directly
   echo "SONAR_TOKEN=$SONAR_TOKEN"
   echo "SONAR_HOST_URL=$SONAR_HOST_URL"
   echo "SONAR_PROJECT_KEY=$SONAR_PROJECT_KEY"
   ```

3. **Run sonar-scanner scoped to changed files**:
   ```bash
   CHANGED=$(git diff origin/main --name-only --diff-filter=ACMR | tr '\n' ',')
   npx sonar-scanner \
     -Dsonar.projectKey="$SONAR_PROJECT_KEY" \
     -Dsonar.sources=. \
     -Dsonar.inclusions="$CHANGED" \
     -Dsonar.host.url="$SONAR_HOST_URL" \
     -Dsonar.token="$SONAR_TOKEN" \
     -Dsonar.exclusions="node_modules/**,dist/**,.git/**,**/*.md"
   ```
   If `$CHANGED` is empty (no local changes), report "no changes to analyze" and stop.

4. **Poll for analysis completion** and parse results (`GET /api/ce/activity`).

5. **Output format** (concise, markdown):
   ```
   ## SonarQube Analysis: Local Changes

   **Project:** ${PROJECT_KEY}
   **Branch:** Current (vs main)
   **Status:** PASS / WARN / FAIL

   ### Summary
   - **Quality Gate:** [status]
   - **Files Analyzed:** N
   - **New Issues:** N

   ### Issues Breakdown
   | Severity | Count |
   |----------|-------|
   | Critical | N |
   | Major | N |
   | Minor | N |
   | Info | N |

   ### Top Files (by issue count)
   - path/to/file.ts (5 issues)
   - path/to/file.py (3 issues)

   **Dashboard:** ${SONAR_HOST_URL}/dashboard?id=${PROJECT_KEY}&branch=...
   ```

6. **Make it actionable**: if issues found, suggest a story title like:
   ```
   Fix X critical/major issues in [files] (SonarQube)
   ```

## Error handling

- If SonarQube is unreachable, show the connection error with URL
- If auth fails, suggest token regeneration
- If no changes detected, report "no changes to analyze"
- If sonar-scanner not installed, guide: `npm install -g sonarqube-scanner`
