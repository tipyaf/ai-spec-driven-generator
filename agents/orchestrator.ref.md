# Orchestrator Reference

Supporting templates, examples, and configuration for the orchestrator agent.

## User Interaction Template

Every human-validated phase MUST end with this template:

```
**Phase [X] is complete.** Here is what was done:
- [bullet summary of outputs]

**What you need to decide:**
- [specific decision 1]
- [specific decision 2 if applicable]

**Options** (if applicable):
- A: [option with trade-off]
- B: [option with trade-off]

Reply with:
- "Approved" — proceed to Phase [next]
- "Changes needed: [your feedback]" — I will revise
```

This template is mandatory. Omitting it or replacing it with a vague "do you validate?" is not acceptable.

## Phase Summary Output Format

```markdown
## Phase [N]: [Name] — Completed

### What was done
- [action 1]
- [action 2]

### Files created/modified
- `path/to/file.ts` — description

### Decisions made
- [decision and justification]

### Points of attention
- [warning or recommendation]

### Action required
Do you validate this phase to proceed to the next one?
```

## Validation Report Format

```
Feature: [name]
Cycle: [n]/3

TypeScript compilation:    PASS/FAIL — [details]
Existing tests:            PASS/FAIL — [details]
New tests written:         PASS/FAIL — [details]
Visual checks:             PASS/FAIL — [details]
Code checks:               PASS/FAIL — [details]
Runtime checks:            PASS/FAIL — [details]
Acceptance tests:          PASS/FAIL — [details]
Manifest check:            PASS/FAIL — [details]
Clean code check:          PASS/FAIL — [details]

Result: [x]/9 passed — VALIDATION PASSED / VALIDATION FAILED
```

## AC Validation Report Format

```
Feature: [name]
AC-XXX-01: PASS
AC-XXX-02: FAIL — [reason]
AC-XXX-03: PASS
Result: [x]/[total] passed — FEATURE DONE / FEATURE NOT DONE
```

## Escalation Procedure

When the dev-validate loop has cycled **3 times** and validation still fails:

1. **STOP** all work on the feature immediately
2. **Present** the full validation report to the human, including:
   - All 3 cycle reports side by side
   - Which checks keep failing and why
   - What the developer attempted each time
   - Screenshots and evidence collected by the validator
3. **Ask the human** to choose one of:
   - **Fix approach**: human provides a specific fix direction, loop resets to cycle 1
   - **Skip check**: human explicitly waives a specific check (logged in memory with justification)
   - **Abandon**: stop work on this feature, move to next or halt project
4. **Log** the escalation and human decision in `memory/[project-name].md`

## Model Configuration

Each agent uses a specific model to optimize cost and quality.

### Default model mapping
| Agent | Recommended Model | Rationale |
|-------|------------------|-----------|
| `orchestrator` | opus | Complex coordination, decision-making |
| `product-owner` | opus | Nuanced understanding of user needs |
| `ux-ui` | sonnet | Creative design, good cost/quality balance |
| `architect` | opus | Critical technical decisions, system design |
| `refinement` | sonnet | Story decomposition, structured output |
| `developer` | sonnet | Code generation, high volume output |
| `validator` | sonnet | Independent validation, structured checks |
| `tester` | sonnet | Test generation, structured validation |
| `reviewer` | opus | Deep analysis, security/quality audit |
| `security` | opus | Critical security analysis |
| `devops` | sonnet | Configuration generation, scripts |

### Override rules
- Model mapping can be overridden in the project spec under `settings.models`
- If a task is unusually complex, the orchestrator MAY escalate to a higher model
- Example spec override:
  ```yaml
  settings:
    models:
      developer: opus    # Override for complex project
      tester: haiku      # Simple test generation
  ```
