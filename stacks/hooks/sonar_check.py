#!/usr/bin/env python3
"""
SonarQube Stop Hook
Runs after every Claude session that modifies source files.
Scans changed files (vs origin/develop) and blocks if new violations are found.

Exit codes:
  0             = PASS or not applicable — Claude stops normally
  0 + JSON out  = FAIL — decision:block feeds report back to Claude, forcing a fix
"""

import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def run(cmd: str, **kwargs) -> tuple[int, str]:
    r = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        cwd=str(ROOT), env=os.environ, **kwargs
    )
    return r.returncode, (r.stdout + r.stderr).strip()


def get_env(name: str) -> str:
    code, val = run(
        f'powershell -command "[Environment]::GetEnvironmentVariable(\'{name}\',\'User\')"'
    )
    return val.strip().strip("\r\n") if code == 0 else ""


def get_changed_files() -> str:
    code, out = run("git diff origin/develop --name-only --diff-filter=ACMR")
    if code != 0 or not out.strip():
        return ""
    return ",".join(out.strip().splitlines())


def run_scanner(token: str, host: str, project_key: str, inclusions: str) -> bool:
    cmd = (
        f'npx sonar-scanner'
        f' -Dsonar.projectKey="{project_key}"'
        f' -Dsonar.sources=.'
        f' -Dsonar.inclusions="{inclusions}"'
        f' -Dsonar.host.url="{host}"'
        f' -Dsonar.token="{token}"'
        f' -Dsonar.exclusions="node_modules/**,dist/**,.git/**"'
    )
    code, _ = run(cmd, timeout=180)
    return code == 0


def get_task_id() -> str:
    report = ROOT / ".scannerwork" / "report-task.txt"
    if not report.exists():
        return ""
    for line in report.read_text().splitlines():
        if line.startswith("ceTaskId="):
            return line.split("=", 1)[1].strip()
    return ""


def wait_for_analysis(token: str, host: str, task_id: str, timeout: int = 120) -> bool:
    creds = base64.b64encode(f"{token}:".encode()).decode()
    url = f"{host}/api/ce/task?id={task_id}"
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            req = urllib.request.Request(url, headers={"Authorization": f"Basic {creds}"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                status = data["task"]["status"]
                if status == "SUCCESS":
                    return True
                if status == "FAILED":
                    return False
        except Exception:
            pass
        time.sleep(3)
    return False


def get_new_violations(token: str, host: str, project_key: str) -> list[dict]:
    creds = base64.b64encode(f"{token}:".encode()).decode()
    url = f"{host}/api/issues/search?projectKeys={project_key}&sinceLeakPeriod=true&ps=50&resolved=false"
    try:
        req = urllib.request.Request(url, headers={"Authorization": f"Basic {creds}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("issues", [])
    except Exception:
        return []


def build_block_report(issues: list[dict], host: str, project_key: str) -> str:
    by_sev: dict[str, list[str]] = {}
    for issue in issues:
        sev = issue.get("severity", "UNKNOWN")
        component = issue.get("component", "").split(":")[-1]
        line = issue.get("line", "?")
        msg = issue.get("message", "")
        by_sev.setdefault(sev, []).append(f"  - `{component}:{line}` — {msg}")

    lines = [
        "## SonarQube — New Violations Found",
        "",
        f"**{len(issues)} new issue(s)** introduced by these changes. Fix all of them before committing.",
        "",
    ]
    for sev in ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]:
        if sev in by_sev:
            lines.append(f"### {sev} ({len(by_sev[sev])})")
            lines.extend(by_sev[sev])
            lines.append("")

    lines += [
        f"**Dashboard:** {host}/dashboard?id={project_key}",
        "",
        "---",
        "Fix all issues above, then I will re-scan automatically.",
    ]
    return "\n".join(lines)


def main() -> None:
    data = json.loads(sys.stdin.read() or "{}")
    if data.get("stop_hook_active"):
        sys.exit(0)

    token = get_env("SONAR_TOKEN")
    host = get_env("SONAR_HOST_URL")
    project_key = get_env("SONAR_PROJECT_KEY")

    if not token or not host or not project_key:
        print("[sonar_check] Missing env vars — skipping", file=sys.stderr)
        sys.exit(0)

    # Check SonarQube is reachable before doing anything
    try:
        creds = base64.b64encode(f"{token}:".encode()).decode()
        req = urllib.request.Request(
            f"{host}/api/system/status",
            headers={"Authorization": f"Basic {creds}"}
        )
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        print("[sonar_check] SonarQube not reachable — skipping", file=sys.stderr)
        sys.exit(0)

    changed = get_changed_files()
    if not changed:
        print("[sonar_check] No changed files — skipping", file=sys.stderr)
        sys.exit(0)

    print(f"[sonar_check] Scanning: {changed}", file=sys.stderr)

    if not run_scanner(token, host, project_key, changed):
        print("[sonar_check] Scanner failed — skipping gate", file=sys.stderr)
        sys.exit(0)

    task_id = get_task_id()
    if not task_id or not wait_for_analysis(token, host, task_id):
        print("[sonar_check] Analysis did not complete — skipping gate", file=sys.stderr)
        sys.exit(0)

    issues = get_new_violations(token, host, project_key)
    if not issues:
        print(f"[sonar_check] PASS — no new violations", file=sys.stderr)
        sys.exit(0)

    report = build_block_report(issues, host, project_key)
    print(json.dumps({"decision": "block", "reason": report}))
    sys.exit(0)


if __name__ == "__main__":
    main()
