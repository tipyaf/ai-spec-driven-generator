"""
ui_messages.py — unified output helpers for the SDD v5 framework.

All skills, the orchestrator, and the check_*.py scripts use these helpers
for user-facing output so the tone, structure, and affordances stay
consistent across the whole framework.

Design contract:
- Every message kind has a single helper (success, fail, next_step, escalation, warn, info, header).
- Output is plain text with ANSI colour codes when stdout is a TTY; stripped otherwise.
- Every fail() or escalation() includes a "how to fix" or "how to resume" line —
  no cryptic error without an actionable follow-up.
- JSON-mode emits machine-readable records (used by /next --json and CI workflows).

Usage:
    from scripts.ui_messages import success, fail, next_step, escalation, header

    header("Gate G2.1 — Mutation testing")
    success("G2.1", "score 87% on changed files (min 80%)")
    fail("G2.1", "score 67% on src/candidates.py", fix="run `mutmut run` locally and review surviving mutants")
    escalation(
        story_id="sc-0012",
        reason="3 cycles failed on G2.1",
        how_to_resume='/resume sc-0012 "reason..."',
    )

JSON mode (set env SDD_OUTPUT=json):
    Each helper writes one JSON object per line to stdout.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# --- Output mode ---------------------------------------------------------

class OutputMode(str, Enum):
    HUMAN = "human"
    JSON = "json"


def _output_mode() -> OutputMode:
    """Return current output mode, honouring SDD_OUTPUT env var."""
    env = os.environ.get("SDD_OUTPUT", "").lower()
    if env == "json":
        return OutputMode.JSON
    return OutputMode.HUMAN


def _use_colour() -> bool:
    """Only colourise when stdout is a TTY and NO_COLOR is not set."""
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


# --- ANSI colour codes ---------------------------------------------------

class _C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GREY = "\033[90m"


def _c(text: str, code: str) -> str:
    if not _use_colour():
        return text
    return f"{code}{text}{_C.RESET}"


# --- Message kinds (data model for JSON mode) ----------------------------

class Kind(str, Enum):
    HEADER = "header"
    SUCCESS = "success"
    FAIL = "fail"
    WARN = "warn"
    INFO = "info"
    NEXT_STEP = "next_step"
    ESCALATION = "escalation"
    TAMPERED = "tampered"


@dataclass
class Message:
    kind: Kind
    text: str
    gate: str | None = None
    story_id: str | None = None
    fix: str | None = None
    reason: str | None = None
    how_to_resume: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        payload = {
            "kind": self.kind.value,
            "text": self.text,
        }
        if self.gate:
            payload["gate"] = self.gate
        if self.story_id:
            payload["story_id"] = self.story_id
        if self.fix:
            payload["fix"] = self.fix
        if self.reason:
            payload["reason"] = self.reason
        if self.how_to_resume:
            payload["how_to_resume"] = self.how_to_resume
        if self.details:
            payload["details"] = self.details
        return json.dumps(payload, ensure_ascii=False)


# --- Emitters ------------------------------------------------------------

def _emit(msg: Message) -> None:
    """Write the message to stdout in the current output mode."""
    if _output_mode() == OutputMode.JSON:
        print(msg.to_json(), flush=True)
        return
    print(_format_human(msg), flush=True)


def _format_human(msg: Message) -> str:
    if msg.kind == Kind.HEADER:
        return "\n" + _c(f"━━━ {msg.text} ━━━", _C.BOLD + _C.CYAN)

    if msg.kind == Kind.SUCCESS:
        tag = _c("✅ PASS", _C.GREEN + _C.BOLD)
        gate = _c(f"[{msg.gate}]", _C.DIM) if msg.gate else ""
        return f"{tag} {gate} {msg.text}".strip()

    if msg.kind == Kind.FAIL:
        tag = _c("❌ FAIL", _C.RED + _C.BOLD)
        gate = _c(f"[{msg.gate}]", _C.DIM) if msg.gate else ""
        lines = [f"{tag} {gate} {msg.text}".strip()]
        if msg.fix:
            lines.append(_c(f"   → Fix: {msg.fix}", _C.YELLOW))
        return "\n".join(lines)

    if msg.kind == Kind.WARN:
        tag = _c("⚠️  WARN", _C.YELLOW + _C.BOLD)
        return f"{tag} {msg.text}"

    if msg.kind == Kind.INFO:
        return _c(f"ℹ  {msg.text}", _C.BLUE)

    if msg.kind == Kind.NEXT_STEP:
        return _c(f"▶  Next step: {msg.text}", _C.MAGENTA + _C.BOLD)

    if msg.kind == Kind.ESCALATION:
        tag = _c("🚨 ESCALATED", _C.RED + _C.BOLD)
        story = _c(f"[{msg.story_id}]", _C.DIM) if msg.story_id else ""
        lines = [f"{tag} {story} {msg.reason or msg.text}".strip()]
        if msg.how_to_resume:
            lines.append(_c(f"   → Resume: {msg.how_to_resume}", _C.YELLOW))
        return "\n".join(lines)

    if msg.kind == Kind.TAMPERED:
        tag = _c("🔒 TAMPERED", _C.RED + _C.BOLD)
        story = _c(f"[{msg.story_id}]", _C.DIM) if msg.story_id else ""
        lines = [f"{tag} {story} {msg.reason or msg.text}".strip()]
        if msg.how_to_resume:
            lines.append(_c(f"   → Resume: {msg.how_to_resume}", _C.YELLOW))
        return "\n".join(lines)

    return msg.text  # fallback


# --- Public API ----------------------------------------------------------

def header(text: str) -> None:
    """Section divider — use at the start of a gate or major phase."""
    _emit(Message(kind=Kind.HEADER, text=text))


def success(gate: str, detail: str, **details: Any) -> None:
    """A gate or check passed."""
    _emit(Message(kind=Kind.SUCCESS, text=detail, gate=gate, details=dict(details)))


def fail(gate: str, reason: str, fix: str, **details: Any) -> None:
    """A gate or check failed. `fix` is MANDATORY — no cryptic errors.

    `fix` is the concrete, actionable follow-up the dev can take right now.
    If you cannot name a fix, write "investigate <specific file:line>".
    """
    if not fix:
        raise ValueError(
            "fail() requires a non-empty `fix` argument. No cryptic errors allowed."
        )
    _emit(Message(kind=Kind.FAIL, text=reason, gate=gate, fix=fix, details=dict(details)))


def warn(text: str, **details: Any) -> None:
    """Non-blocking concern. Dev should see it but can continue."""
    _emit(Message(kind=Kind.WARN, text=text, details=dict(details)))


def info(text: str, **details: Any) -> None:
    """Neutral informational message."""
    _emit(Message(kind=Kind.INFO, text=text, details=dict(details)))


def next_step(action: str) -> None:
    """End-of-phase pointer: tell the dev exactly what to do next."""
    _emit(Message(kind=Kind.NEXT_STEP, text=action))


def escalation(story_id: str, reason: str, how_to_resume: str) -> None:
    """Story has hit max cycles and is locked until /resume."""
    if not how_to_resume:
        raise ValueError("escalation() requires `how_to_resume` (e.g. '/resume sc-0012 \"reason...\"').")
    _emit(
        Message(
            kind=Kind.ESCALATION,
            text=reason,
            story_id=story_id,
            reason=reason,
            how_to_resume=how_to_resume,
        )
    )


def tampered(story_id: str, reason: str, how_to_resume: str) -> None:
    """Bypass detected (--no-verify, test weakened, TDD order violated)."""
    if not how_to_resume:
        raise ValueError("tampered() requires `how_to_resume`.")
    _emit(
        Message(
            kind=Kind.TAMPERED,
            text=reason,
            story_id=story_id,
            reason=reason,
            how_to_resume=how_to_resume,
        )
    )


# --- Exit helpers --------------------------------------------------------

# Orchestrator exit codes (see plan §4).
EXIT_OK = 0
EXIT_GATE_FAIL = 1
EXIT_ESCALATED = 2
EXIT_CONFIG_ERROR = 3
EXIT_TAMPERED = 4


def exit_with(code: int) -> None:
    """Flush and exit with the given code."""
    sys.stdout.flush()
    sys.stderr.flush()
    sys.exit(code)


# --- Self-test ----------------------------------------------------------

if __name__ == "__main__":
    # Quick visual check: `python3 scripts/ui_messages.py`
    header("ui_messages.py self-test")
    success("G2", "coverage 87% line / 74% branch (min 80/70)")
    fail(
        "G2.1",
        "mutation score 67% on src/candidates.py (min 80%)",
        fix="run `mutmut show` to inspect survivors, then strengthen assertions",
    )
    warn("3 tests flaky on recent runs (2/10 fails)", flaky_tests=["test_retry", "test_timeout"])
    info("14 gates applicable for spec.type=web-api")
    next_step("/build sc-0014 (next gate: G4.1 smoke boot)")
    escalation(
        story_id="sc-0012",
        reason="3 cycles failed on G2.1 mutation score",
        how_to_resume='/resume sc-0012 "strengthened assertions in candidate_test.py:45"',
    )
    tampered(
        story_id="sc-0009",
        reason="test weakened in commit abc123 (assertion removed without justification)",
        how_to_resume='/resume sc-0009 "restored assertion after review"',
    )
