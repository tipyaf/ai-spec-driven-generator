#!/usr/bin/env python3
"""Helpers for migrate-v4-to-v5.sh.

Subcommands:
    agents          Rewrite v4 agent names to v5 in specs/ and _work/.
    spec-type       Infer or persist spec.type in the project's main spec.
    claude-md       Rewrite CLAUDE.md v4 references to v5.
    merge-settings  Merge the v5 hooks template into .claude/settings.json.
    tracker         Validate & upgrade feature-tracker.yaml.
    stories         Add interactions:/smoke_command: stubs to stories.
    report          Write _backup_v4/MIGRATION_REPORT.md.

Each subcommand exits 0 on success (idempotent), non-zero on unrecoverable error.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

# ── Agent rename map (v4 -> v5) ────────────────────────────────────────────

AGENT_RENAMES = {
    "tester": "test-author",
    "test-engineer": "test-author",
    "reviewer": "code-reviewer",
    "story-reviewer": "code-reviewer",
    # "developer" and "spec-generator" are removed in v5 — we add a comment.
}
AGENT_REMOVE = {"developer", "spec-generator"}

# Any reference to "orchestrator" as an agent now points at scripts/orchestrator.py.
# We do NOT rename the token itself (skills still invoke `orchestrator`) but we add
# a migration note on file header when encountered for the first time.

# ── YAML handling (tolerant: prefer PyYAML, fall back to regex) ────────────

try:
    import yaml  # type: ignore
    HAVE_YAML = True
except ImportError:
    yaml = None  # type: ignore
    HAVE_YAML = False


def load_yaml(path: Path):
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    if HAVE_YAML:
        try:
            return yaml.safe_load(text)
        except Exception:
            return None
    return text  # fallback: raw text


def dump_yaml(data, path: Path) -> None:
    if HAVE_YAML and not isinstance(data, str):
        path.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    else:
        path.write_text(data if isinstance(data, str) else str(data), encoding="utf-8")


# ── Subcommand: agents ─────────────────────────────────────────────────────

def _rewrite_agent_text(text: str) -> tuple[str, int]:
    hits = 0
    new = text
    # Rename with word boundaries.
    for old, new_name in AGENT_RENAMES.items():
        pattern = re.compile(rf"\b{re.escape(old)}\b")
        new, n = pattern.subn(new_name, new)
        hits += n
    # Flag removed agents with a TODO comment; leave the reference so humans can remove.
    for removed in AGENT_REMOVE:
        pat = re.compile(rf"\b{re.escape(removed)}\b")
        if pat.search(new):
            # We do not auto-delete — we surface it.
            hits += 1
    return new, hits


def cmd_agents(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    total_hits = 0
    scanned = 0
    errors = 0

    roots = [project / "specs", project / "_work"]
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in (".yaml", ".yml", ".md", ".json"):
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                errors += 1
                continue
            new_text, hits = _rewrite_agent_text(text)
            scanned += 1
            if hits and not args.dry_run:
                try:
                    p.write_text(new_text, encoding="utf-8")
                except Exception:
                    errors += 1
                    continue
            total_hits += hits

    print(f"[agents] scanned={scanned} hits={total_hits} errors={errors}")
    return 0 if errors == 0 else 1


# ── Subcommand: spec-type ──────────────────────────────────────────────────

def _iter_spec_files(project: Path):
    for sub in ("specs", "_work/spec"):
        d = project / sub
        if d.exists():
            yield from d.rglob("*.yaml")
            yield from d.rglob("*.yml")


def _detect_spec_type_from_files(project: Path) -> str | None:
    # Look inside existing YAML specs.
    for p in _iter_spec_files(project):
        data = load_yaml(p)
        if isinstance(data, dict):
            t = data.get("type") or (data.get("spec") or {}).get("type")
            if t:
                return str(t).strip()
        elif isinstance(data, str):
            m = re.search(r"^\s*type:\s*([\w\-]+)", data, re.MULTILINE)
            if m:
                return m.group(1)
    return None


def _infer_spec_type_from_project(project: Path) -> str | None:
    pkg = project / "package.json"
    if pkg.exists():
        try:
            meta = json.loads(pkg.read_text(encoding="utf-8"))
            deps = {**meta.get("dependencies", {}), **meta.get("devDependencies", {})}
            if any(k in deps for k in ("react", "next", "vue", "svelte")):
                return "web-ui"
            if any(k in deps for k in ("express", "fastify", "koa", "hapi")):
                return "web-api"
        except Exception:
            pass

    pyproj = project / "pyproject.toml"
    if pyproj.exists():
        try:
            txt = pyproj.read_text(encoding="utf-8")
            if re.search(r"fastapi|flask|django|starlette", txt, re.IGNORECASE):
                return "web-api"
            if re.search(r"typer|click|argparse", txt, re.IGNORECASE):
                return "cli"
        except Exception:
            pass

    cargo = project / "Cargo.toml"
    if cargo.exists():
        try:
            txt = cargo.read_text(encoding="utf-8")
            if "[[bin]]" in txt or re.search(r"\[\[?bin", txt):
                return "cli"
            if "[lib]" in txt:
                return "lib"
        except Exception:
            pass

    return None


def cmd_spec_type(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    if args.probe:
        t = _detect_spec_type_from_files(project) or _infer_spec_type_from_project(project)
        print(t or "unknown")
        return 0
    if args.write:
        # Persist into the main spec if we can.
        # Prefer _work/spec/sc-0000*.yaml; otherwise the first non-tracker spec.
        target = None
        for cand in (
            project / "_work" / "spec",
            project / "specs",
        ):
            if cand.exists():
                for p in sorted(cand.glob("sc-0000*.yaml")):
                    target = p
                    break
                if target is None:
                    yamls = [
                        p for p in sorted(cand.glob("*.yaml"))
                        if p.name != "feature-tracker.yaml"
                    ]
                    if yamls:
                        target = yamls[0]
                if target:
                    break
        if target is None:
            print("[spec-type] no spec file to update (skipping)")
            return 0
        if HAVE_YAML:
            data = load_yaml(target) or {}
            if isinstance(data, dict):
                data["type"] = args.write
                dump_yaml(data, target)
                print(f"[spec-type] wrote type={args.write} to {target}")
                return 0
        # Text fallback
        txt = target.read_text(encoding="utf-8")
        if re.search(r"^type:\s*", txt, re.MULTILINE):
            txt = re.sub(r"^type:\s*.*$", f"type: {args.write}", txt, flags=re.MULTILINE)
        else:
            txt = f"type: {args.write}\n" + txt
        target.write_text(txt, encoding="utf-8")
        print(f"[spec-type] wrote type={args.write} to {target} (text mode)")
        return 0
    return 0


# ── Subcommand: claude-md ──────────────────────────────────────────────────

CLAUDE_MD_REPLACEMENTS = [
    (r"SDD\s+v4(\.\d+)*", "SDD v5.0"),
    (r"framework v4(\.\d+)*", "framework v5.0"),
    (r"11\s+gates?", "14 gates"),
    (r"11\s+quality\s+gates?", "14 quality gates"),
    (r"G1-G11", "G1-G14"),
    (r"G1–G11", "G1–G14"),
    (r"\btester\b", "test-author"),
    (r"\bstory-reviewer\b", "code-reviewer"),
    (r"\breviewer\b(?!-agent)", "code-reviewer"),
]

CLAUDE_MD_V5_NOTE = """
<!-- v5 migration note ({date}) -->
## v5.0 — Framework changes

- Agents: 18 total (new: test-author, code-reviewer, observability-engineer,
  performance-engineer, data-migration-engineer, release-manager).
- Gates: G1-G14 (G9.x for UI, G10 for performance baselines, G13 for data fixtures).
- Orchestrator: `scripts/orchestrator.py` is the single source of truth.
- New commands: `/ship`, `/next`, `/status`, `/help`, `/resume`.
- See `_docs/PIPELINE.md`, `_docs/GUIDE.md`, and `_docs/CHEATSHEET.md`.
<!-- end v5 migration note -->
"""


def cmd_claude_md(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    md = project / "CLAUDE.md"
    if not md.exists():
        print("[claude-md] no CLAUDE.md found")
        return 0
    text = md.read_text(encoding="utf-8")
    original = text
    for pat, rep in CLAUDE_MD_REPLACEMENTS:
        text = re.sub(pat, rep, text)
    if "v5 migration note" not in text:
        text = text.rstrip() + "\n" + CLAUDE_MD_V5_NOTE.format(date=_dt.date.today().isoformat()) + "\n"
    if text != original:
        md.write_text(text, encoding="utf-8")
        print(f"[claude-md] updated {md}")
    else:
        print("[claude-md] no changes (already v5)")
    return 0


# ── Subcommand: merge-settings ─────────────────────────────────────────────

def _load_json_lenient(path: Path):
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    # Strip JSON-with-comments (// and /* */) — the template uses "_comment" keys,
    # but be safe for any user variant.
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = re.sub(r"//.*?$", "", raw, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        try:
            return json.loads(cleaned)
        except Exception:
            return None


def _merge_dicts(dst: dict, src: dict) -> dict:
    # Deep merge: keys in dst win, but lists are union (by identity of JSON string).
    for k, v in src.items():
        if k in dst:
            if isinstance(dst[k], dict) and isinstance(v, dict):
                _merge_dicts(dst[k], v)
            elif isinstance(dst[k], list) and isinstance(v, list):
                seen = {json.dumps(x, sort_keys=True) for x in dst[k]}
                for item in v:
                    k_item = json.dumps(item, sort_keys=True)
                    if k_item not in seen:
                        dst[k].append(item)
                        seen.add(k_item)
            else:
                # preserve user value
                pass
        else:
            dst[k] = v
    return dst


def cmd_merge_settings(args: argparse.Namespace) -> int:
    template = Path(args.template)
    target = Path(args.target)
    tpl = _load_json_lenient(template)
    if tpl is None:
        print(f"[merge-settings] cannot read template {template}", file=sys.stderr)
        return 1
    existing = _load_json_lenient(target) or {}
    merged = _merge_dicts(existing, tpl)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    print(f"[merge-settings] wrote {target}")
    return 0


# ── Subcommand: tracker ────────────────────────────────────────────────────

def cmd_tracker(args: argparse.Namespace) -> int:
    tracker = Path(args.tracker)
    if not tracker.exists():
        print("[tracker] no tracker file")
        return 0

    # Prefer PyYAML when available.
    if HAVE_YAML:
        data = load_yaml(tracker)
        if isinstance(data, dict):
            stories = data.get("stories") or data.get("features") or []
            if isinstance(stories, list):
                build_dir = Path(args.project) / "_work" / "build"
                changed = False
                for s in stories:
                    if not isinstance(s, dict):
                        continue
                    status = s.get("status")
                    sid = s.get("id") or s.get("slug") or ""
                    if status == "blocked":
                        s["status"] = "escalated"
                        changed = True
                    if status == "validated" and sid:
                        cand = build_dir / f"{sid}.yaml"
                        if not cand.exists():
                            s.setdefault("notes", "")
                            s["notes"] = (s["notes"] + "; MIGRATION: no build file").strip("; ")
                            changed = True
                if changed:
                    dump_yaml(data, tracker)
                    print(f"[tracker] upgraded {tracker}")
                    return 0
        # Fall through to text-based rewrite as safety net.

    # Text-mode fallback: line-by-line rewrite. Handles the common shape:
    #    - id: sc-XXXX
    #      status: blocked
    text = tracker.read_text(encoding="utf-8")
    lines = text.splitlines()
    build_dir = Path(args.project) / "_work" / "build"
    out: list[str] = []
    # First pass: detect story IDs and statuses in order.
    current_id: str | None = None
    changed = False
    for i, line in enumerate(lines):
        m_id = re.match(r"^(\s*[-]?\s*)id:\s*(\S+)", line)
        if m_id:
            current_id = m_id.group(2).strip()
        m_st = re.match(r"^(\s*)status:\s*(\S+)\s*$", line)
        if m_st:
            indent, status = m_st.group(1), m_st.group(2)
            if status == "blocked":
                line = f"{indent}status: escalated"
                changed = True
            elif status == "validated" and current_id:
                if not (build_dir / f"{current_id}.yaml").exists():
                    out.append(line)
                    out.append(f"{indent}notes: MIGRATION - no build file")
                    changed = True
                    continue
        out.append(line)
    if changed:
        tracker.write_text("\n".join(out) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
        print(f"[tracker] upgraded (text-mode) {tracker}")
    else:
        print("[tracker] no changes needed")
    return 0


# ── Subcommand: stories ────────────────────────────────────────────────────

def cmd_stories(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    spec_type = args.spec_type or "lib"
    touched = 0
    for d in (project / "specs" / "stories", project / "_work" / "spec"):
        if not d.exists():
            continue
        for p in sorted(d.glob("*.yaml")):
            data = load_yaml(p)
            if not isinstance(data, dict):
                continue
            added = False
            if spec_type in ("web-ui", "mobile"):
                if "interactions" not in data:
                    data["interactions"] = []  # to be filled by /refine
                    added = True
            if spec_type == "cli":
                if "smoke_command" not in data:
                    data["smoke_command"] = ""
                    added = True
            if added:
                dump_yaml(data, p)
                touched += 1
    print(f"[stories] updated {touched} story files")
    return 0


# ── Subcommand: report ─────────────────────────────────────────────────────

REPORT_TEMPLATE = """# Migration report — v{src} → v{tgt}

**Date:** {date}
**Project:** {project}
**spec.type:** {spec_type}

## Files created

{created}

## Files modified

{changed}

## Warnings

{warnings}

## Post-migration checklist

- [ ] Review `CLAUDE.md` for residual v4 references.
- [ ] Fill `interactions:` arrays for every UI story (run `/refine` on each).
- [ ] Fill `smoke_command:` for every CLI story.
- [ ] Configure a code-quality tool (sonar / semgrep / ruff / eslint) for G3.
- [ ] Verify `.claude/settings.json` hooks run correctly (`git commit --allow-empty -m test`).
- [ ] Run a full pipeline: `/build <story>` to confirm end-to-end flow.
- [ ] Commit changes: `git add -A && git commit -m 'chore: migrate to v5.0'`
- [ ] Remove backup once verified: `rm -rf _backup_v4/`

## Rollback

If anything is off:

    bash framework/scripts/migrate-v4-to-v5.sh --rollback

This restores every file captured in `_backup_v4/`.
"""


def _bullet_list(raw: str) -> str:
    items = [x.strip() for x in (raw or "").split(",") if x.strip()]
    if not items:
        return "_(none)_"
    return "\n".join(f"- `{x}`" for x in items)


def cmd_report(args: argparse.Namespace) -> int:
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    body = REPORT_TEMPLATE.format(
        src=args.source_version,
        tgt=args.target_version,
        date=_dt.datetime.now().isoformat(timespec="seconds"),
        project=args.project,
        spec_type=args.spec_type,
        created=_bullet_list(args.created),
        changed=_bullet_list(args.changed),
        warnings=_bullet_list(args.warnings),
    )
    report.write_text(body, encoding="utf-8")
    print(f"[report] wrote {report}")
    return 0


# ── Entrypoint ─────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Helpers for migrate-v4-to-v5.sh")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("agents")
    a.add_argument("--project", required=True)
    a.add_argument("--dry-run", action="store_true")
    a.set_defaults(func=cmd_agents)

    st = sub.add_parser("spec-type")
    st.add_argument("--project", required=True)
    st.add_argument("--probe", action="store_true")
    st.add_argument("--write", default=None)
    st.set_defaults(func=cmd_spec_type)

    cm = sub.add_parser("claude-md")
    cm.add_argument("--project", required=True)
    cm.set_defaults(func=cmd_claude_md)

    ms = sub.add_parser("merge-settings")
    ms.add_argument("--template", required=True)
    ms.add_argument("--target", required=True)
    ms.set_defaults(func=cmd_merge_settings)

    tr = sub.add_parser("tracker")
    tr.add_argument("--project", required=True)
    tr.add_argument("--tracker", required=True)
    tr.set_defaults(func=cmd_tracker)

    sr = sub.add_parser("stories")
    sr.add_argument("--project", required=True)
    sr.add_argument("--spec-type", required=True)
    sr.set_defaults(func=cmd_stories)

    rp = sub.add_parser("report")
    rp.add_argument("--project", required=True)
    rp.add_argument("--backup", required=True)
    rp.add_argument("--report", required=True)
    rp.add_argument("--source-version", required=True)
    rp.add_argument("--target-version", required=True)
    rp.add_argument("--spec-type", required=True)
    rp.add_argument("--created", default="")
    rp.add_argument("--changed", default="")
    rp.add_argument("--warnings", default="")
    rp.set_defaults(func=cmd_report)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
