---
name: sonar
description: Quick SonarQube status check. Fetches current quality gate status and key metrics without running a new scan. Use for a fast dashboard view.
---

## Overview

Fetch current SonarQube quality gate status and key metrics without triggering a new scan. This is a read-only, fast status check.

## Prerequisites

- Environment variables set: `SONAR_TOKEN`, `SONAR_HOST_URL`, `SONAR_PROJECT_KEY`

## Workflow

1. **Fetch quality gate status**:
   ```bash
   curl -s -u "$SONAR_TOKEN:" "$SONAR_HOST_URL/api/qualitygates/project_status?projectKey=$SONAR_PROJECT_KEY"
   ```

2. **Fetch key metrics**:
   ```bash
   curl -s -u "$SONAR_TOKEN:" "$SONAR_HOST_URL/api/measures/component?component=$SONAR_PROJECT_KEY&metricKeys=ncloc,bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,sqale_rating,security_rating,reliability_rating"
   ```

3. **Output format** (concise markdown):
   ```
   ## SonarQube Status

   **Project:** ${PROJECT_KEY}
   **Quality Gate:** PASS / FAIL

   | Metric | Value |
   |--------|-------|
   | Lines of Code | N |
   | Bugs | N |
   | Vulnerabilities | N |
   | Code Smells | N |
   | Coverage | XX% |
   | Duplications | XX% |
   | Reliability | A-E |
   | Security | A-E |
   | Maintainability | A-E |

   **Dashboard:** ${SONAR_HOST_URL}/dashboard?id=${PROJECT_KEY}
   ```

4. **Actionable summary**: If quality gate is failing, list the failing conditions and suggest next steps:
   - Run `/scan` for local changes analysis
   - Run `/scan-full` for full repository analysis
   - Create fix stories for critical issues

## Error handling

- If SonarQube is unreachable, show connection error with URL
- If auth fails, suggest token regeneration
- If project not found, list available projects
