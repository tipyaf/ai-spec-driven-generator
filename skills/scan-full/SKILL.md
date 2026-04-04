---
name: scan-full
description: Run SonarQube scanner on the entire repository. Full codebase analysis, returns quality summary with hotspots and trends.
---

## Overview

Run SonarQube analysis on the entire repository codebase.

## Prerequisites

- `sonar-scanner` or `npx sonar-scanner` must be available
- SonarQube credentials configured via **one of**:
  - `.env` file at project root (recommended — per-project)
  - Shell environment variables (`~/.zshrc`, `~/.bashrc`, or Windows User env)
- Required variables: `SONAR_TOKEN`, `SONAR_HOST_URL`, `SONAR_PROJECT_KEY`

## Workflow

1. **Run sonar-scanner on full codebase**:
   ```bash
   sonar-scanner \
     -Dsonar.projectKey=$SONAR_PROJECT_KEY \
     -Dsonar.sources=. \
     -Dsonar.host.url=$SONAR_HOST_URL \
     -Dsonar.token=$SONAR_TOKEN \
     -Dsonar.exclusions="node_modules/**,dist/**,.git/**"
   ```

2. **Fetch project metrics** from SonarQube API:
   ```bash
   GET /api/projects/measures/component?component=${PROJECT_KEY}&metricKeys=ncloc,bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,sqale_rating
   ```

3. **Output format** (markdown, actionable):
   ```
   ## SonarQube Full Codebase Analysis

   **Project:** ${PROJECT_KEY}
   **Scope:** Entire repository
   **Last Update:** [timestamp]

   ### Overall Quality
   | Metric | Value | Trend |
   |--------|-------|-------|
   | **Quality Gate** | PASS / WARN / FAIL | |
   | **Reliability** | A / B / C / ... | |
   | **Security** | A / B / C / ... | |
   | **Maintainability** | A / B / C / ... | |
   | **Coverage** | XX% | |

   ### Issue Summary
   | Type | Count | Critical % |
   |------|-------|-----------|
   | Bugs | N | X% |
   | Vulnerabilities | N | X% |
   | Code Smells | N | X% |
   | Duplications | XX% | -- |

   ### Top Hotspots (Highest Issue Density)
   1. path/to/file1.ts (XX issues, coverage YY%)
   2. path/to/file2.py (XX issues, coverage YY%)
   3. path/to/file3.tsx (XX issues, coverage YY%)

   ### Coverage by Component
   - **Backend:** XX%
   - **Frontend:** XX%

   **Dashboard:** ${SONAR_HOST_URL}/dashboard?id=${PROJECT_KEY}
   ```

4. **Trend analysis**: Compare with previous scan (if SonarQube history available):
   - Show improvements and regressions
   - Flag if quality is declining

### Recommended Actions
If quality gate failing or score declining:
- Create story: "Improve code quality: fix X critical issues, raise coverage to XX%"
- Focus on top 3 hotspots
- Target specific metric to improve

## Error handling

- If SonarQube is unreachable, show URL and connection error
- If auth fails, suggest token regeneration
- If metrics unavailable, fetch what is available and note gaps
- If sonar-scanner not installed, guide: `npm install -g sonarqube-scanner`
