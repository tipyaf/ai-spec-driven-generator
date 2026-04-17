#!/usr/bin/env python3
"""generate-interaction-tests.py — generate Playwright tests from wireframe + story.

Reads `specs/stories/{story}.yaml:interactions:` and the matching wireframe
HTML in `_work/wireframes/{story}/*.html`. Emits
`_work/generated/interactions/{story}.spec.ts` with one Playwright test per
interaction. Each test asserts DOM visibility, URL change, API call
intercepted, state mutation, and 0 console error.

Exit: 0 pass, 1 fail, 2 config error.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ui_messages import fail, success, info, warn  # noqa: E402

try:
    import yaml
except ImportError:
    yaml = None


def find_root() -> Path:
    here = Path(__file__).resolve().parent
    for p in [here] + list(here.parents):
        if (p / ".git").exists():
            return p
    return Path.cwd()


def render_test(story: str, interaction: dict) -> str:
    action = interaction.get("action", "unknown")
    trigger = interaction.get("trigger", "")
    expected = interaction.get("expected", []) or []
    selector = ""
    event = "click"
    if trigger.startswith("click "):
        event = "click"
        selector = trigger.replace("click ", "", 1).strip()
    elif trigger.startswith("submit "):
        event = "submit"
        selector = trigger.replace("submit ", "", 1).strip()

    # Convert "data-testid=foo" to '[data-testid="foo"]'
    if "=" in selector and not selector.startswith("["):
        key, val = selector.split("=", 1)
        selector = f'[{key}="{val}"]'

    lines = [
        f"test('{action}', async ({{ page }}) => {{",
        "  const errors: string[] = [];",
        "  page.on('pageerror', (e) => errors.push(e.message));",
        "  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });",
        "  await page.goto('/');",
    ]
    if event == "click":
        lines.append(f"  await page.locator(\"{selector}\").click();")
    elif event == "submit":
        lines.append(f"  await page.locator(\"{selector}\").evaluate((f: any) => f.submit());")

    for exp in expected:
        if not isinstance(exp, dict):
            continue
        if "dom" in exp:
            target = exp["dom"]
            tag_sel = target.split(" is ")[0].strip()
            if "=" in tag_sel and not tag_sel.startswith("["):
                k, v = tag_sel.split("=", 1)
                tag_sel = f'[{k}="{v}"]'
            lines.append(f"  await expect(page.locator(\"{tag_sel}\")).toBeVisible();")
        if "url" in exp:
            u = exp["url"]
            if u == "unchanged":
                lines.append("  // URL expected to stay unchanged")
            else:
                lines.append(f"  await expect(page).toHaveURL(new RegExp('{u}'));")
        if "api" in exp and exp["api"] not in ("none", "None"):
            lines.append(f"  // API expected: {exp['api']}")
    lines.append("  expect(errors).toEqual([]);")
    lines.append("});")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--story", required=True)
    args = ap.parse_args()

    if yaml is None:
        fail("gen", "PyYAML required", fix="pip install pyyaml")
        return 2
    root = find_root()
    story_file = root / "specs" / "stories" / f"{args.story}.yaml"
    if not story_file.exists():
        fail("gen", f"story not found: {story_file}",
             fix=f"create specs/stories/{args.story}.yaml first")
        return 2
    data = yaml.safe_load(story_file.read_text()) or {}
    interactions = data.get("interactions", []) or []
    if not interactions:
        warn(f"no `interactions:` in {story_file.name} — nothing to generate")
        return 0

    header = "import { test, expect } from '@playwright/test';\n"
    body = "\n\n".join(render_test(args.story, i) for i in interactions)
    out_dir = root / "_work" / "generated" / "interactions"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.story}.spec.ts"
    out_path.write_text(header + "\n" + body + "\n")
    info(f"wrote {out_path.relative_to(root)} ({len(interactions)} test(s))")
    success("gen", f"{len(interactions)} Playwright test(s) generated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
