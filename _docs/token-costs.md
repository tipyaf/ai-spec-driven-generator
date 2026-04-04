[< Back to Index](INDEX.md)

# Token Cost Analysis

How this framework manages LLM token consumption across sessions, agents, and retries.

Last updated: 2026-04-04

---

## 1. Fixed Overhead Per Session

Every Claude Code session begins with `CLAUDE.md` injected automatically. Agents then load shared rules before their playbook.

| File | Lines | Loaded when |
|---|---|---|
| `rules/CLAUDE.md` | ~370 | Every session (auto-injected) |
| `rules/agent-conduct.md` | ~197 | Every agent, before playbook |
| `rules/test-quality.md` | ~340 | developer, tester, test-engineer, reviewer, validator, story-reviewer |
| `rules/coding-standards.md` | ~215 | developer, reviewer, tester, test-engineer, story-reviewer, all builders |

**Baseline per session**: ~567 lines (CLAUDE.md + agent-conduct.md) before any agent-specific content.

---

## 2. Per-Agent Cost Table

| Agent | Playbook | Ref file | Model | Used by skill |
|---|---|---|---|---|
| architect | ~247 | ~202 | opus | /spec |
| tester | ~248 | ~209 | opus | /review, /validate |
| refinement | ~245 | ~99 | opus | /refine |
| reviewer | ~179 | ~149 | opus | /review |
| developer | ~176 | ~54 | opus | /build |
| test-engineer | ~141 | ~123 | opus | /build (RED) |
| builder-exchange | ~147 | ~265 | opus | /build (exchange) |
| product-owner | ~162 | ~130 | sonnet | /spec, /refine |
| validator | ~188 | ~84 | sonnet | /validate, /build |
| story-reviewer | ~166 | ~130 | sonnet | /build (gate 7) |
| spec-generator | ~168 | ~162 | sonnet | /spec |
| security | ~131 | ~214 | sonnet | /review |
| ux-ui | ~132 | ~182 | sonnet | /spec, /ux |
| builder-service | ~131 | ~205 | sonnet | /build (backend) |
| builder-frontend | ~138 | ~232 | sonnet | /build (frontend) |
| builder-migration | ~167 | ~220 | sonnet | /build (migration) |
| builder-infra | ~113 | ~303 | sonnet | /build (infra) |
| devops | ~121 | ~132 | sonnet | deploy |
| orchestrator | ~124 | ~123 | opus | reference only |

**Total playbook lines**: ~2,934. **Total ref lines**: ~2,889.
Ref files are loaded on demand only — this is the framework's most impactful optimization.

---

## 3. Skill Session Budgets

| Skill | Agents loaded | Rules loaded | Skill file | Total core lines | Models |
|---|---|---|---|---|---|
| /build | developer + test-engineer + builder + validator + story-reviewer | all 4 rules | ~126 | ~1,900+ | opus + sonnet |
| /review | reviewer + security + tester | all 4 rules | ~65 | ~1,744 | opus + sonnet |
| /spec | product-owner + ux-ui + architect | conduct, CLAUDE.md | ~95 | ~1,202 | opus + sonnet |
| /refine | refinement + product-owner | conduct, CLAUDE.md | ~102 | ~1,075 | opus |
| /validate | validator + tester | conduct, CLAUDE.md, test-quality | ~83 | ~837 | sonnet + opus |
| /scan | inline (no agents) | CLAUDE.md only | ~84 | ~453 | n/a |
| /sonar | inline (no agents) | CLAUDE.md only | ~60 | ~429 | n/a |

**/build is the most expensive session** at ~1,900 lines of core context before stack profiles and story files.

---

## 4. Where Tokens Are Spent

### 4.1 CLAUDE.md (~370 lines) — loaded every session

Contains ~130 lines that duplicate content already in other loaded files:
- Model tier recommendations table (~12 lines) — duplicated by agent frontmatter `model:` fields
- Agent role guards table (~17 lines) — duplicated in orchestrator.md
- Acceptance criteria format block (~14 lines) — duplicated in product-owner.md and refinement.md
- Enforcement mechanisms table (~9 lines) — duplicated in agent-conduct.md

### 4.2 test-quality.md (~340 lines) — heaviest shared rule

Loaded by 6 agents. In a /build session, read by developer + test-engineer (same 340 lines read twice by two separate agents in the same pipeline).

### 4.3 coding-standards.md (~215 lines) — broad but not always relevant

Builder-infra (config-only) and builder-migration (migrations-only) load sections on API design and component architecture that are irrelevant to their scope.

### 4.4 Retry multiplier

When a RED phase fails gates, the test-engineer is re-dispatched with full context: CLAUDE.md + rules + playbook + build file. Each Opus retry is the most expensive operation in the pipeline. Max 3 validation cycles per feature can triple the token cost.

---

## 5. Already-Implemented Optimizations

| Optimization | Mechanism | Impact |
|---|---|---|
| **Ref files on demand** | `.ref.md` pattern — ~2,889 lines NOT loaded by default | ~2,889 lines avoided per session |
| **Skill-based loading** | Agents loaded only when their skill runs | Avoids loading all 19 agents upfront |
| **Model dispatch from frontmatter** | 12 sonnet agents, 7 opus — correct tier assignment | Prevents unnecessary opus calls |
| **Inline skills** | /scan, /scan-full, /sonar, /migrate: no agent files loaded | ~400 lines avoided per scan session |
| **Builder specialization** | 5 builders, each scoped to one domain | Prevents full-codebase context loading |
| **Sequential phase loading** | /spec loads PO → UX/UI → Architect one at a time | Avoids loading all spec agents simultaneously |

---

## 6. Possible Optimizations

| Change | Estimated saving | Effort | Risk |
|---|---|---|---|
| Trim CLAUDE.md duplicate sections (~130 lines) | ~70 lines/session | Low | Low — verify no section is the sole source |
| Split coding-standards.md into core + UI sections | ~60 lines for infra/migration builds | Low | Low |
| Remove product-owner.md from /refine setup | ~162 lines per /refine | Low | Verify AC format is self-contained in refinement.md |
| Split test-quality.md into writing vs reviewing | ~140 lines in /review sessions | Medium | Ensure reviewer gets all needed context |
| Reduce retry rate (improve refiner output quality) | ~2,000+ lines per avoided Opus retry | Ongoing | None — strictly positive |

**Total estimated saving (no retries)**: ~430 lines per session (~15% reduction on /build).
**Per avoided Opus retry**: ~2,000+ lines (the full RED phase context reload).

---

## 7. Summary

| Metric | Value |
|---|---|
| Fixed overhead (CLAUDE.md + agent-conduct.md) | ~567 lines |
| Lightest session (/sonar — inline) | ~429 lines |
| Lightest agent session (/validate) | ~837 lines |
| Heaviest session (/build) | ~1,900+ lines |
| Total playbook lines (all 19 agents) | ~2,934 lines |
| Total ref file lines (all 19 .ref.md) | ~2,889 lines |
| Ref files avoided per session (on-demand pattern) | ~2,889 lines |
