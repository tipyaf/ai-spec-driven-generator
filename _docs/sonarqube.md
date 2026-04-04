[< Back to Index](INDEX.md)

# SonarQube

How to install, configure, and run SonarQube for local code quality analysis.

---

## 1. Install SonarQube (Docker)

```bash
docker run -d \
  -p 9000:9000 \
  --name sonarqube \
  sonarqube:community
```

Wait ~30 seconds for startup, then open `http://localhost:9000` (or your VM hostname).

Default credentials: `admin` / `admin` -- you will be prompted to change the password on first login.

To reset a broken container:

```bash
docker stop sonarqube && docker rm sonarqube
# re-run the docker run command above
```

---

## 2. First-Time Configuration

### Create a project

1. Log in
2. Go to Projects > Create Project > Manually
3. Set a **Project Key** (e.g. `my-project`) -- this is the unique ID used by the scanner
4. Set a display name and click Set Up

### Generate an authentication token

1. Click your avatar (top right) > My Account > Security
2. Under Generate Token: give it a name, type = Project Analysis Token, no expiry
3. Click Generate and copy the token -- it starts with `squ_`
4. Store it immediately -- it is shown only once

---

## 3. Store Credentials

### Recommended: `.env` at project root (per-project)

Each project can have its own SonarQube configuration. Copy the example and fill in your values:

```bash
cp framework/stacks/hooks/.env.example .env
```

```env
# .env (gitignored — never commit this file)
SONAR_TOKEN=squ_your_token_here
SONAR_HOST_URL=http://localhost:9000
SONAR_PROJECT_KEY=your-project-key
```

The hook `sonar_check.py` reads `.env` first, then falls back to shell environment variables. This allows per-project configuration (different SonarQube instances, different project keys).

### Alternative: shell profile (global fallback)

If you prefer a single global config for all projects:

**macOS/Linux (~/.zshrc or ~/.bashrc):**

```bash
export SONAR_TOKEN="squ_your_token_here"
export SONAR_HOST_URL="http://localhost:9000"
export SONAR_PROJECT_KEY="your-project-key"
```

**Windows (PowerShell):**

```powershell
[System.Environment]::SetEnvironmentVariable("SONAR_TOKEN",       "squ_your_token_here",     "User")
[System.Environment]::SetEnvironmentVariable("SONAR_HOST_URL",    "http://your-host:9000",   "User")
[System.Environment]::SetEnvironmentVariable("SONAR_PROJECT_KEY", "your-project-key",        "User")
```

**Priority**: `.env` at project root > shell environment variables. If both exist, `.env` wins.

---

## 4. Run a Scan

No global install needed -- use npx:

```bash
npx sonar-scanner \
  -Dsonar.projectKey="$SONAR_PROJECT_KEY" \
  -Dsonar.sources=. \
  -Dsonar.host.url="$SONAR_HOST_URL" \
  -Dsonar.token="$SONAR_TOKEN" \
  -Dsonar.exclusions="node_modules/**,dist/**,.git/**"
```

To scan only files changed vs a branch:

```bash
CHANGED=$(git diff origin/develop --name-only --diff-filter=ACMR | tr '\n' ',')
npx sonar-scanner \
  -Dsonar.projectKey="$SONAR_PROJECT_KEY" \
  -Dsonar.sources=. \
  -Dsonar.inclusions="$CHANGED" \
  -Dsonar.host.url="$SONAR_HOST_URL" \
  -Dsonar.token="$SONAR_TOKEN" \
  -Dsonar.exclusions="node_modules/**,dist/**,.git/**"
```

### Using Framework Skills

The framework provides three skills for running scans:

| Skill | What it scans | When to use |
|-------|--------------|-------------|
| /sonar | Local changes only (staged + unstaged vs origin/develop) | During development, before committing |
| /scan | Full repository | Periodic quality check |
| /scan-full | Full repository with security hotspots and trends | Pre-release audit |

---

## 5. Hook Integration (sonar_check.py)

The framework includes `stacks/hooks/sonar_check.py` for automated SonarQube checks as part of the Claude Code hook system.

### Setup

1. Ensure the three environment variables are set (section 3)
2. The hook is configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python stacks/hooks/sonar_check.py",
            "timeout": 300
          }
        ]
      }
    ]
  }
}
```

See `stacks/hooks/settings-hooks-example.json` for a complete example.

### What it checks

The sonar_check.py hook:
- Runs the SonarQube scanner against changed files
- Parses the analysis results
- Reports issues by severity (BLOCKER, CRITICAL, MAJOR, MINOR, INFO)
- Returns a pass/block verdict based on severity thresholds

---

## 6. Coverage Reporting

SonarQube shows 0% coverage unless you generate a report before scanning.

**Python (pytest-cov):**

```bash
pytest --cov=. --cov-report=xml:coverage.xml
```

**JavaScript/TypeScript (vitest):**

```bash
npx vitest run --coverage
```

Then add to the scanner command:

```
-Dsonar.python.coverage.reportPaths=coverage.xml
-Dsonar.javascript.lcov.reportPaths=coverage/lcov.info
```

---

## 7. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Login form does not submit | Corrupt H2 database in container | Reset the container (section 1) |
| Authentication failed | Wrong or expired token | Regenerate token (section 2), update env var (section 3) |
| Cannot connect to server | Container not running or wrong URL | `docker ps` to verify; use hostname not IP if on a VM |
| Unknown skill: /sonar | Skills not symlinked | Run `framework/scripts/init-project.sh` or create symlinks manually |
| 0 files analyzed | sonar.inclusions is empty | Verify `git diff` returns files; check you have local changes |
| 0% coverage | No coverage report passed | Generate report first (section 6) |
| Scanner hangs | Network issue or SonarQube overloaded | Check `docker logs sonarqube`; restart container if needed |
| sonar_check.py not found | Hook path wrong in settings.json | Verify the path matches your project structure |
| SONAR_TOKEN not set | Environment variable not persisted | Re-add to ~/.zshrc and `source ~/.zshrc` |
