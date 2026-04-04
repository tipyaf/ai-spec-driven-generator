# Test Methodology: AI-Driven Test Generation

How this framework ensures AI agents write tests that catch real bugs, not tests that pass and prove nothing.

---

## The Problem

AI coding agents write tests that look correct but catch nothing. A typical project can have hundreds of green tests while production has NULL values, wrong calculations, and empty pages. The tests assert structure (status codes, field existence) but never check computed values.

Research (Meta FSE 2025, ICSE 2025 IntUT, MutGen 2025) confirms three root causes:

1. **No oracle.** The agent gets "write tests for this function" but not the business rules. Without knowing the expected value, it writes `assert result is not None` -- which passes for any value including NULL.

2. **LLMs predict, they don't compute.** Even with the formula, an LLM will guess a plausible number instead of calculating the correct one. The math must be done for them.

3. **Wrong feedback signal.** The agent's success metric is "tests pass" and "coverage goes up." Trivial assertions score perfectly on both while catching zero bugs.

---

## The Solution: Two Loops + Enforcement

### Loop 1: Spec to Test Intentions (proactive)

The **refinement agent** reads the spec and extracts every formula and business rule. For each formula, it picks concrete input values and does the step-by-step arithmetic. The results are written as `test_intentions` in the story file:

```yaml
test_intentions:
  - function: <function_name>
    description: "<what this tests>"
    inputs:
      field_a: <value>
      field_b: <value>
    oracle:
      intermediate: "formula = substitution = result"
      final: "formula = substitution = result"
    assertions:
      - "result.field == <expected>"
    edge_cases:
      - description: "<edge case name>"
        inputs: { field_a: <value>, field_b: <value> }
        oracle: { final: "formula = substitution = result" }
        assertions: ["result.field == <expected>"]
```

For frontend stories, the refinement agent also writes Trigger C intentions — one per rendered field — declaring the expected display string for null, formatted, and edge-case inputs. These are not formulas; they are display mapping oracles. The test engineer copies them into UI tests using the project's mocking and rendering tools (e.g., MSW + Testing Library for web, or the equivalent for your stack).

The **developer** reads the `test_intentions` and copies the oracle values into the test. The developer doesn't compute -- they copy. This solves the "LLMs can't compute" problem: the refiner does the math once, the developer uses the pre-computed answer.

The test then looks like:

```python
# ORACLE: final = formula
#         = substitution with concrete values
#         = step-by-step arithmetic
#         = expected_value
assert result.final == pytest.approx(expected_value)
```

If the production code returns NULL, 0, or any wrong value -- the test fails. Bug caught.

### Loop 2: Mutation Feedback (reactive)

After tests are written, mutation testing runs. The mutation tool flips operators in the production code (`+` to `-`, `* 100` to `* 200`, `>` to `>=`). If the tests don't catch the flip, they are weak.

Surviving mutants are fed back to the tester: "these mutants survived, write one test per survivor that would fail if this mutation were applied." Max 2 cycles.

This is the correction mechanism. Even if Loop 1 misses a case, Loop 2 catches it by empirically proving what the tests do and don't detect.

Meta deployed this approach across Messenger and WhatsApp (9,095 mutants, 73% engineer acceptance rate). MutGen (2025) achieved 89.5% mutation score with this loop vs 69.5% without.

### LLM Fault Scenarios

Mechanical mutation testing operates at the syntax level: it flips `+` to `-`, changes `True` to `False`. These are artificial. Real bugs are at the business logic level: "used the wrong field", "overwrote a value instead of accumulating."

The **tester agent** generates realistic fault scenarios by reading the production code and the spec. For each business rule, it produces 3-5 fault scenarios describing mistakes a developer (or AI) would actually make, with concrete inputs showing the correct vs faulty output.

Fault scenario categories:

| Category | Example |
|----------|---------|
| Wrong field reference | Using field_A where field_B is needed |
| Missing accumulation | Overwriting a running total with the latest value instead of adding |
| Off-by-one scaling | Ratio instead of percentage (missing * 100) |
| Null propagation | Computed field stays NULL when inputs are valid |
| Stale state | Reading a cached value instead of the freshly computed one |
| Wrong aggregation | Using AVG where SUM is needed |
| Boundary confusion | >= vs > in threshold checks |
| Type coercion | Integer division truncating decimal results |

Each fault scenario becomes a targeted test.

### Ensemble Test Assessment

Rule-based scripts check syntax patterns: "is there an ORACLE comment?" "is there a proper assertion?" But a test can have an ORACLE comment with wrong math, or assert a value that catches nothing.

After all automated gates pass, the tester reviews each test function and scores it:

| Score | Meaning |
|-------|---------|
| STRONG | Calls real production code, verifies a business rule from the spec, would catch the corresponding fault scenario, ORACLE math is correct |
| WEAK | Passes most checks but has a gap (e.g. ORACLE uses wrong formula) |
| USELESS | Only asserts is not None or status code, no computed value verification |

USELESS tests must be rewritten before the feature can proceed.

---

## Enforcement Scripts

Rules written in agent playbooks get ignored. Scripts run before every commit and block violations:

| Script | What it enforces |
|--------|-----------------|
| `check_test_quality.py` | No .skip(), no mock-soup in integration tests, no fixture-only tests, no weak-only assertions |
| `check_oracle_assertions.py` | Every numeric assertion on a computed value has an # ORACLE: comment showing step-by-step math |
| `check_write_coverage.py` | Every data store with a read endpoint has production code that writes to it |

All scripts live in `scripts/` and read project-specific configuration from `test_enforcement.json` at the project root. Existing violations are whitelisted (warnings, not blocking). New violations block the commit.

---

## The Full Pipeline

```
/refine --> test_intentions in story file (Loop 1: oracle values pre-computed)
    |
/build  --> developer writes code + tests with # ORACLE: blocks
    |
Tester generates LLM fault scenarios --> writes targeted tests
    |
Validator + enforcement scripts verify
    |
Mutation testing --> survivors --> tester writes kill-tests (Loop 2)
    |
Ensemble assessment --> rewrite USELESS tests
    |
Security audit --> Review --> Validated
```

---

## What Catches Each Bug Type

| Bug type | Loop 1 (spec to test) | Loop 2 (mutation) | Fault scenarios | Enforcement scripts |
|----------|----------------------|--------------------|-----------------|---------------------|
| Missing feature (empty page) | YES -- audit finds no writer | NO -- nothing to mutate | NO -- no code to fault | YES -- write coverage script |
| Wrong value (NULL) | YES -- oracle expects a value, gets NULL | YES -- mutant survives | YES -- null propagation | YES -- blocks assert-without-oracle |
| Wrong formula | YES -- oracle expects X, gets Y | YES -- mutant changes operator | YES -- off-by-one scaling | YES -- forces oracle comment |
| Overwritten value | YES -- oracle expects full result, gets partial | YES -- mutant catches overwrite | YES -- missing accumulation | YES -- forces oracle comment |
| Display bug | YES -- spec says show value | NO -- frontend | YES -- null propagation | NO -- not numeric |

---

## Adopting This in a New Project

1. During `/refine`, the refinement agent creates story files with `test_intentions` for features with formulas (Trigger A) and for frontend stories with rendered fields (Trigger C)
2. During `/build`, the developer reads test_intentions and copies oracle values into tests
3. During `/validate` and `/review`, enforcement scripts run automatically
4. Configure enforcement via `test_enforcement.json` (copy from `scripts/test_enforcement.json.example`)
5. Stack profiles specify the mutation testing tool and configuration

The agent playbooks already reference the test quality rules and test_intentions workflow. No additional configuration needed beyond the JSON config file.

---

## References

### Blog post (primary source)

**Mark Harman** -- *The Death of Traditional Testing: Agentic Development Broke a 50-Year-Old Field, JiTTesting Can Revive It*
Engineering at Meta, February 11, 2026

The article that directly informed the JiTTests / ensemble assessment / mutation-guided approach used in this framework.

### Research papers

**Noble Saji Mathews, Meiyappan Nagappan** -- *Design choices made by LLM-based test generators prevent them from finding bugs*
arXiv:2412.14137, December 2024

Shows that up to 68% of LLM-generated tests actively validate bugs rather than catch them. Root cause of why this framework uses oracle computation and mutation feedback.

**Mark Harman, Jillian Ritchey, Inna Harper et al.** -- *Mutation-Guided LLM-based Test Generation at Meta*
FSE 2025 Industry Papers

Applied to 10,795 Android Kotlin classes across Meta's Messenger and WhatsApp. 73% engineer acceptance rate. Source for "Loop 2: Mutation Feedback."

**ICSE 2025 Research Track** -- *Test Intention Guided LLM-based Unit Test Generation (IntUT)*

By supplying LLMs with explicit test intentions, IntUT achieves 94% improvement in branch coverage. Source for "Loop 1: Spec to Test Intentions."

**Max Schafer, Sarah Nadi, Aryaz Eghbali, Frank Tip** -- *An Empirical Evaluation of Using Large Language Models for Automated Unit Test Generation*
IEEE Transactions on Software Engineering, Vol. 50, No. 1, 2024

Confirms LLMs optimize for green tests, not bug detection, without iterative correction.
