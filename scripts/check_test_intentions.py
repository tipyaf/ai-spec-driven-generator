#!/usr/bin/env python3
"""
check_test_intentions.py -- Enforcement: every test_intention from spec must become a test.

Searches for test_intentions in this order:
1. --spec-path override (if provided)
2. specs/stories/*.yaml — story files (where refinement writes test_intentions)
3. _work/spec/sc-[ID].yaml — spec overlay (legacy fallback)

Then scans test files committed for this story to verify each intention has a
corresponding test function.

Matching logic:
- Each intention has a `function` field (e.g. "close_trade", "useLogs (URL contract)")
- Each intention has `assertions` (list of expected assertion strings)
- The script searches test files for:
  1. A test function whose name contains the function name (normalized to snake_case)
  2. Or a test function whose body references the function name
- If an intention has no matching test: VIOLATION

Usage:
    python check_test_intentions.py --story 1500
    python check_test_intentions.py --story 1500 --spec-path specs/stories/user-profile.yaml

Exit code: 0 = all intentions covered, 1 = missing test(s)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

# Optional: embedding-based semantic match. If sentence-transformers is
# installed we use it; otherwise we fall back to the existing regex
# heuristics (which are still applied as a second pass for recall).
_SENTENCE_TRANSFORMERS_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    _SENTENCE_TRANSFORMERS_AVAILABLE = True
except Exception:
    SentenceTransformer = None  # type: ignore


def _embedding_model():
    """Load the local embedding model once, cached on the module."""
    global _EMBED_MODEL
    if "_EMBED_MODEL" in globals():
        return _EMBED_MODEL
    if not _SENTENCE_TRANSFORMERS_AVAILABLE:
        _EMBED_MODEL = None
        return None
    try:
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        _EMBED_MODEL = None
    return _EMBED_MODEL


def _semantic_match(intent: str, test_blob: str, threshold: float = 0.55) -> bool:
    """Cosine-similarity check. Returns False when embeddings are unavailable."""
    model = _embedding_model()
    if model is None:
        return False
    try:
        import numpy as np  # provided alongside sentence-transformers
        vectors = model.encode([intent, test_blob], normalize_embeddings=True)
        cos = float(np.dot(vectors[0], vectors[1]))
        return cos >= threshold
    except Exception:
        return False

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"


def find_project_root() -> Path:
    script_dir = Path(__file__).resolve().parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / "CLAUDE.md").exists():
            return parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / ".git").is_dir():
            return parent
    return Path.cwd()


def parse_yaml_simple(content: str) -> list[dict]:
    """Extract test_intentions from YAML content.

    Uses PyYAML if available, otherwise falls back to regex parsing.
    """
    if yaml is not None:
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict) and "test_intentions" in data:
                intentions = data["test_intentions"]
                if isinstance(intentions, list):
                    return intentions
            return []
        except Exception:
            pass

    # Fallback: regex-based extraction
    intentions = []
    in_block = False
    current: dict = {}

    for line in content.splitlines():
        if re.match(r"^test_intentions:", line):
            in_block = True
            continue
        if in_block and re.match(r"^\S", line) and not line.startswith(" "):
            # New top-level key, end of test_intentions
            if current:
                intentions.append(current)
            break
        if not in_block:
            continue

        # Parse intention entries
        m = re.match(r"^\s+-\s+function:\s*(.+)", line)
        if m:
            if current:
                intentions.append(current)
            current = {"function": m.group(1).strip()}
            continue

        m = re.match(r"^\s+description:\s*[\"']?(.+?)[\"']?\s*$", line)
        if m and current:
            current["description"] = m.group(1)

        m = re.match(r"^\s+-\s+[\"'](.+?)[\"']\s*$", line)
        if m and current:
            current.setdefault("assertions", []).append(m.group(1))

    if current:
        intentions.append(current)

    return intentions


def normalize_function_name(name: str) -> str:
    """Convert function name to a searchable pattern.

    "close_trade" -> "close_trade"
    "useLogs (URL contract)" -> "uselogs|use_logs|url_contract"
    """
    # Remove parenthetical notes
    base = re.sub(r"\s*\([^)]*\)", "", name).strip()
    # Convert camelCase to snake_case
    snake = re.sub(r"([a-z])([A-Z])", r"\1_\2", base).lower()
    # Also keep original lowercase
    original = base.lower().replace(" ", "_")

    parts = {snake, original}
    # Add individual words for matching
    words = re.findall(r"\w+", name.lower())
    if len(words) >= 2:
        parts.add("_".join(words[:2]))

    return "|".join(parts)


def find_test_files_for_story(story_id: str, project_root: Path) -> list[Path]:
    """Find all test files in the project that could contain story tests."""
    import subprocess

    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--name-only",
                "--format=",
                f"--grep=\\[sc-{story_id}\\]",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=30,
        )
        if result.returncode != 0:
            return []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    test_files = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        is_test = re.match(r".*test_.*\.py$", line) or re.match(r".*_test\.py$", line)
        is_ts_test = re.match(r".*\.test\.(ts|tsx)$", line) or re.match(
            r".*\.spec\.(ts|tsx)$", line
        )
        if is_test or is_ts_test:
            full = project_root / line
            if full.exists():
                test_files.append(full)

    return list(set(test_files))


def check_intention_covered(
    intention: dict, test_contents: dict[str, str]
) -> str | None:
    """Check if a test_intention has a matching test. Returns None if covered, error if not."""
    func_name = intention.get("function", "")
    if not func_name:
        return None  # No function name to match

    pattern = normalize_function_name(func_name)
    description = intention.get("description", "")
    assertions = intention.get("assertions", [])

    # Build an intention blob used for semantic matching.
    intent_blob = " ".join(filter(None, [func_name, description, *assertions]))

    for filepath, content in test_contents.items():
        content_lower = content.lower()

        # Check 0 (v5): embedding semantic match — skipped when the lib is
        # unavailable. When it IS available it catches cases where the test
        # describes the same behaviour in different words.
        if _semantic_match(intent_blob, content):
            return None

        # Check 1: Test function name contains the function reference
        for variant in pattern.split("|"):
            if variant and variant in content_lower:
                return None  # Found a match

        # Check 2: Description keywords appear in test
        if description:
            desc_words = re.findall(r"\w{4,}", description.lower())
            if (
                desc_words
                and sum(1 for w in desc_words if w in content_lower)
                >= len(desc_words) // 2
            ):
                return None  # Enough keywords match

        # Check 3: Assertion text appears in test
        for assertion in assertions:
            # Extract key identifiers from assertion
            identifiers = re.findall(r"\w{4,}", assertion.lower())
            if identifiers and all(i in content_lower for i in identifiers[:3]):
                return None  # Assertion content found

    return (
        f"test_intention '{func_name}' has no matching test. "
        f"Description: {description or '(none)'}. "
        f"Expected assertions: {assertions[:2] if assertions else '(none)'}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check test_intentions coverage from spec"
    )
    parser.add_argument("--story", required=True, type=str, help="Story ID")
    parser.add_argument("--spec-path", type=str, help="Override spec file path")
    parser.add_argument(
        "--require-ui-intentions",
        action="store_true",
        help="Fail if test_intentions is empty (use for frontend stories with rendered fields — Trigger C)",
    )
    args = parser.parse_args()

    project_root = find_project_root()
    story_id = args.story

    # --- Step 1: Find the file containing test_intentions ---
    # Priority: --spec-path override > story file in specs/stories/ > spec overlay in _work/spec/
    # test_intentions are written by the refinement agent into the STORY file,
    # not the spec overlay. The spec overlay contains domain context (endpoints, schemas).
    spec_path: Path | None = None
    if args.spec_path:
        spec_path = Path(args.spec_path)
    else:
        # Search story files first (where refinement writes test_intentions)
        stories_dir = project_root / "specs" / "stories"
        if stories_dir.is_dir():
            for candidate in stories_dir.glob("*.yaml"):
                content_peek = candidate.read_text(errors="replace")
                if "test_intentions:" in content_peek and f"sc-{story_id}" in content_peek.lower():
                    spec_path = candidate
                    break
                # Also match by story id field
                if f'id: "sc-{story_id}"' in content_peek or f"id: sc-{story_id}" in content_peek:
                    spec_path = candidate
                    break
        # Fallback to spec overlay (legacy behavior)
        if spec_path is None:
            spec_path = project_root / "_work" / "spec" / f"sc-{story_id}.yaml"

    if not spec_path.exists():
        print(
            f"{YELLOW}[WARN]{NC} No story file or spec overlay found for sc-{story_id}. "
            f"Cannot check test_intentions."
        )
        return 0

    content = spec_path.read_text(errors="replace")

    # --- Step 2: Extract test_intentions ---
    intentions = parse_yaml_simple(content)
    if not intentions:
        if args.require_ui_intentions:
            print(
                f"{RED}[FAIL]{NC} --require-ui-intentions is set but no test_intentions "
                f"found in {spec_path.name}. Frontend stories with rendered fields must "
                f"have Trigger C test_intentions."
            )
            return 1
        print(f"{GREEN}No test_intentions in spec. Nothing to check.{NC}")
        return 0

    print(f"Found {len(intentions)} test_intention(s) in {spec_path.name}:")
    for i, intent in enumerate(intentions, 1):
        func = intent.get("function", "(unknown)")
        print(f"  {i}. {func}")

    # --- Step 3: Find test files ---
    test_files = find_test_files_for_story(story_id, project_root)
    if not test_files:
        print(
            f"\n{RED}[FAIL]{NC} {len(intentions)} test_intention(s) but no test files "
            f"found for sc-{story_id}."
        )
        return 1

    # Read all test file contents
    test_contents = {}
    for tf in test_files:
        test_contents[str(tf)] = tf.read_text(errors="replace")

    # --- Step 4: Check each intention ---
    violations = []
    for intent in intentions:
        error = check_intention_covered(intent, test_contents)
        if error:
            violations.append(error)

    if violations:
        print(f"\n{RED}Missing test coverage for spec intentions:{NC}")
        for v in violations:
            print(f"  {RED}[FAIL]{NC} {v}")
        print(
            f"\n{RED}Every test_intention in the spec MUST have a corresponding test. "
            f"No exceptions.{NC}"
        )
        return 1

    print(f"\n{GREEN}All {len(intentions)} test_intention(s) covered by tests.{NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
