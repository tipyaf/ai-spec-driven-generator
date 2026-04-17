# CHEATSHEET.md — v5 TL;DR (1 page)

30-second recap for any agent. For details see [`GUIDE.md`](GUIDE.md) and
[`../_docs/PIPELINE.md`](../_docs/PIPELINE.md).

---

## Commands (1-liner each)

| Command | What it does |
|---|---|
| `/spec` | Define the project (constitution, scope, UX, architecture). |
| `/ux <feature>` | UX design: IA, flows, wireframes, DS tokens. |
| `/refine <feature>` | Break feature into stories with `verify:` + oracle values. |
| `/build <story-id>` | Orchestrator: auto-dispatch builder, TDD RED→GREEN, run gates. |
| `/validate <story-id>` | Read-only rerun of gates on the current repo. |
| `/review [story-id\|--all]` | Read-only audit — PASS/FAIL verdict. No PR. |
| `/ship <story-id>` | Runs `/review`; on PASS pushes + opens PR with `sdd-validated-v5` tag. |
| `/scan [--full] [--report]` | SonarQube / semgrep / eslint scan. |
| `/next [--scope …] [--json]` | Prioritised action list — tape-le le matin. |
| `/status [story-id]` | Dashboard passif: état complet du projet. |
| `/help [command]` | Contextual help. |
| `/resume <story-id> "reason"` | Unlock an escalated/tampered story (reason mandatory). |
| `/migrate [--to VERSION]` | Run migration scripts (v3→v4, v4→v5). |

---

## Top 10 rules (in priority order)

1. **Never `gh pr create` manually** — only `/ship` produces the `sdd-validated-v5` tag.
2. **Never self-certify** — only the script exit code is evidence.
3. **Never skip a `test_intention`** from the story file — every intention is a test.
4. **Never assert a computed value without an `# ORACLE:` block** with step-by-step math.
5. **Never use Rule 2b weak assertions** as terminal assertions on computed fields
   (`!= None`, `len > 0`, `isinstance`, bare truthiness, status-only).
6. **Never do another agent's job manually** — use the skill.
7. **Never `git add .` / `git add -A`** — name files explicitly.
8. **Never bypass hooks** (`--no-verify` is detected at the next orchestrator pass — story → `tampered`).
9. **Always read `feature-tracker.yaml` + `LESSONS.md` + your playbook** before acting; list your steps.
10. **Always target `develop` for PRs** (never `main` except release PRs); unrelated work goes in a worktree.

---

## Gates G1–G14 (1-liner each)

| Gate | Applies to | One-liner |
|---|---|---|
| **G1** | All | OWASP patterns, AC-SEC-*, dep vulns. |
| **G2** | All | Unit tests — 3 runs, 0 flakiness, coverage threshold. |
| **G2.1** | All | Mutation testing ≥ 80% on changed files. |
| **G2.2** | All | Regression: rerun all tests from prior validated stories. |
| **G2.3** | All | Contract diff: API / public AST / DB schema / CLI surface. |
| **G3** | All | Code quality — tool mandatory, no subjective fallback. |
| **G4** | All | Build final artifact (binary, image, wheel, bundle). |
| **G4.1** | All | Smoke boot — app starts and responds. |
| **G5** | All | AC Tier 1 `verify:` commands pass. |
| **G6** | All | Story review — AC Tier 2/3 ↔ diff (agent `code-reviewer` mode `story`). |
| **G7** | All | Code review — scope, SOLID, 0 console errors (mode `code`). |
| **G8** | If touches validated module | Cross-story integration tests. |
| **G9.1** | web-ui, mobile | Design System conformity — tokens only. |
| **G9.2** | web-ui, mobile | Wireframe `data-testid` present; hierarchy match. |
| **G9.3** | web-ui, mobile | Visual regression pixelmatch on 3 viewports. |
| **G9.4** | web-ui, mobile | Interaction verification from `interactions:`. |
| **G9.5** | web-ui, mobile | Accessibility axe + keyboard + contrast. |
| **G9.6** | web-ui, mobile | Behavioral regression — rejoue anciennes `interactions:`. |
| **G10** | All (opt-in lib) | Performance budget + > 5% baseline regression = FAIL. |
| **G11** | web-api, web-ui, ml-pipeline | Observability — logs/metrics/traces ratio/LOC. |
| **G12** | web-api, web-ui | Runtime security / DAST-lite (ZAP, Schemathesis). |
| **G13** | If migration | Migration safety — rollback + data preserved. |
| **G14** | At `/ship` | Release readiness — CHANGELOG / VERSION / tags. |

---

## Orchestrator exit codes

| Code | Meaning | What to do |
|---|---|---|
| **0** | All gates pass | Proceed |
| **1** | Gate failed (normal) | Fix and retry (max 3 cycles) |
| **2** | `escalated` — max cycles reached | `/resume <story-id> "reason"` |
| **3** | Config error (missing project-type, unknown stack) | Fix config |
| **4** | `tampered` — bypass detected | `/resume <story-id> "reason"` |

---

## Feature tracker states

```
pending → refined → building → validated → shipped
                        │           ▲
                        │           │
                        └─── cycle ─┘ (max 3)
                             │
                             ▼
                         escalated ←→ tampered   ← terminal, requires /resume
```

| State | Set by |
|---|---|
| `pending` | `/spec` |
| `refined` | `/refine` |
| `building` | `/build` |
| `validated` | `/build` on PASS |
| `shipped` | `/ship` |
| `escalated` | `/build` after 3 cycles |
| `tampered` | Tamper detection (any gate) |

---

## See also

- [`GUIDE.md`](GUIDE.md) — full rules reference (principles, coding, tests, agent conduct, commits, git flow).
- [`../_docs/PIPELINE.md`](../_docs/PIPELINE.md) — full pipeline reference (commands, agents, scripts, gates).
- [`commands/`](commands/) — per-skill reference cards.
