# Test Quality Rules

Shared rules for every agent that writes, reviews, or evaluates tests.
Referenced by: `developer.md`, `tester.md`, `reviewer.md`, `validator.md`.

**Every agent that writes or reviews tests MUST read this file before starting.**

---

## Rule 1: Tests must call real production code

1. **Every test must import and call the real function, endpoint, or component.** Tests that only verify fixture shapes, do inline arithmetic, or assert on mock return values are worthless and must not be written.

2. **`.skip()` and `.todo()` are not tests.** A skipped test catches nothing. If a test exists to expose a bug, it must EXECUTE.
   - In pytest: use `@pytest.mark.xfail(reason="BUG: ...")`
   - In vitest/jest (no xfail): assert the current broken value with a `// BUG:` comment
   - In other frameworks: use the equivalent xfail/expected-failure mechanism

3. **API mocks must return what the backend actually sends**, not what the frontend expects. The point of mocking is to catch frontend-backend mismatches. Procedure:
   1. Find the backend handler for the endpoint (grep for the URL path)
   2. Read the handler -- find the response model/type declaration
   3. Read the response model -- note every field name, type, and nesting
   4. Write the mock returning EXACTLY that shape -- same field names, same nesting, same types
   5. **Verify the URL**: the mock must intercept at the exact URL path declared in the backend (including prefix)
   6. **Cross-check**: if the frontend type has DIFFERENT field names than the backend model, that IS a bug the test must catch

   **Never read the frontend code first and write mocks from it.** Read the backend first. Always.

   ### MSW 6-step procedure (mandatory for frontend tests)

   The #1 cause of false-green tests: MSW mocks that match what the frontend expects instead of what the backend sends. For every MSW handler, follow this procedure -- no shortcuts:

   1. Find the backend router file (grep for the URL path in the routers directory)
   2. Read the router function -- find `response_model=XXX` and the exact URL path including prefix
   3. Read the Pydantic model XXX -- note every field name, type, and wrapper structure
   4. Write the MSW handler using the Pydantic field names and the exact backend URL
   5. Cross-check: if frontend TypeScript types have different field names than the Pydantic model, that IS a bug the test must catch
   6. Run the API contract checker (e.g. `python scripts/check_msw_contracts.py`) first -- every MISMATCH becomes a failing test

   This procedure is enforced by: `check_msw_contracts.py` (blocks camelCase fields not in Pydantic models), the test engineer's Read Before Write step, and the code reviewer Pass 1 (MSW field/URL mismatch = ERROR).

4. **Follow the plan.** If a story file says "test X, assert Y", the agent tests X and asserts Y. Not something else. Not a fixture check. Not a skip.

5. **Run tests and check the results.** If tests designed to catch bugs all pass, the tests are wrong. Stop. Investigate. Fix the tests before committing.

---

## Rule 2: Oracle Computation -- every numeric assertion must show its math

**"field is not NULL" catches nothing. "field == 2.20" with documented math catches everything.**

The difference between a useless test and a useful test is one step: computing the expected value from the inputs BEFORE writing the assertion.

### The ORACLE comment block (mandatory)

Every numeric assertion on a computed value MUST have an `# ORACLE:` (or `// ORACLE:`) comment block within 5 lines above it. The block shows the formula, the substitution with concrete values, and the expected result.

**Python example:**
```python
# ORACLE: fees_pct = total_fees / (entry_price * qty) * 100
#         = 2.20 / (100.00 * 10) * 100
#         = 2.20 / 1000 * 100
#         = 0.22
assert result.fees_pct == pytest.approx(Decimal("0.22"), abs=Decimal("0.01"))
```

**TypeScript example:**
```typescript
// ORACLE: feesPct = totalFees / equity * 100
//         = 5.20 / 1000 * 100
//         = 0.52
expect(result).toBeCloseTo(0.52, 2);
```

**Go example:**
```go
// ORACLE: feesPct = totalFees / (entryPrice * qty) * 100
//         = 2.20 / (100.00 * 10) * 100
//         = 0.22
assert.InDelta(t, 0.22, result.FeesPct, 0.01)
```

### What requires an ORACLE

Any assertion that compares against a literal number on a **computed field** (financial values, percentages, ratios, totals, scores, averages, weighted values).

### What does NOT require an ORACLE

Status codes, array lengths, boolean checks, string equality, UUID comparisons, array membership, enum values.

### Where do the oracle values come from?

**From the spec.** The story file (`specs/stories/[feature-id].yaml`) contains a `test_intentions` section with pre-computed test cases: concrete inputs, step-by-step oracle math, and expected assertions. The builder copies the oracle into the test's `# ORACLE:` comment and uses the assertions directly. See Rule 8 for the full `test_intentions` workflow.

If the spec has no `test_intentions` for this formula, the agent must compute the oracle itself from the business rules documented in the spec or the production code.

### Additional rules

1. **Every write-then-read test must call the real write function, then query.** Not INSERT fixture data then GET. A test that inserts fake data and then calls a read endpoint proves the SELECT works, not that anything WRITES correctly.

2. **Fixtures for computed fields must have an ORACLE block too.** If a fixture sets `fees_pct=0.22`, an ORACLE comment must prove 0.22 is correct given the fixture's own input values.

3. **If all tests pass on first write, at least one is wrong.** When writing tests for known bugs, at least one test MUST fail (or be xfail). If zero tests fail, STOP -- the test is asserting the broken behavior as correct.

---

## Rule 2b: Weak assertion banlist -- patterns that catch zero bugs

These patterns are BANNED as terminal/sole assertions on computed result fields. They always pass as long as the code returns *something*, which means they verify plumbing, not correctness.

**This rule is language-agnostic.** The categories below apply to every language and test framework. Adapt the syntax to your stack.

### Banned assertion categories

| Category | What it looks like | Why it catches zero bugs | What to write instead |
|----------|--------------------|--------------------------|----------------------|
| **Existence-only** | `!= null`, `is not None`, `toBeDefined()`, `!= nil`, `!= nullptr` | Passes for any value including `{}`, `0`, `""` | Assert the actual value: `== expected` |
| **Non-empty-only** | `len(x) > 0`, `.length > 0`, `.size() > 0`, `.Count > 0` | Passes if list has 1 item when it should have 10 | Assert exact count: `len(x) == 3` |
| **Type-only** | `isinstance(x, dict)`, `toBeInstanceOf(Object)`, `is T`, `typeof x === "object"` | Passes for any instance of that type, even empty | Assert fields and values inside the object |
| **Bare truthiness** | `assert x`, `expect(x).toBeTruthy()`, `assertTrue(x)`, `require.True(x)` | `0`, `""`, `[]` are falsy; `"error"` is truthy — semantics vary by language | Assert the concrete expected value |
| **Status-code-only** | `status == 200` / `StatusCode == 200` without body assertions | Never checks if the response has correct data | Always add body/field assertions after status check |

### When these patterns ARE legitimate

These patterns are acceptable ONLY as **guard assertions** before subsequent value assertions, or when testing a boolean fact (not a computed value):

- Existence check followed immediately by value assertion -- the guard is fine
- DOM presence check when testing that a component renders at all (not testing data values)
- Type check in a contract/schema test, as long as field values are also asserted downstream
- Status code `!= 200` alone for auth rejection / error tests (e.g. 401, 403, 404 -- no body needed)

**The rule: a weak pattern is banned when it is the terminal/sole assertion on a computed result field.**

### Stack-specific examples

Project stack profiles (in the project's `stacks/` directory) may provide language-specific banned patterns with exact regex for enforcement scripts. The categories above are the source of truth; stack-specific patterns are illustrations.

---

## Rule 3: Tests must cover ALL layers

**Every feature has layers. Every layer must have at least one test. No layer can be assumed to work because another layer was tested.**

1. **For every data store write path, there must be a test that verifies production code writes to it.** Not a fixture insert. A test that calls the real service/endpoint, then queries to verify the data exists with correct values. If no production code writes to it, the test must FAIL documenting the missing writer -- never skip, never TODO.

2. **For every endpoint/handler that reads data, there must be a test that the data source has data written by production code.** If the test must insert fixture data to make the endpoint work, that is a red flag: the write path is either broken or missing. Document it as a failing test.

3. **For every UI page/screen, there must be a test that verifies it displays real data.** Not mock data shaped to make the page work. Data shaped like what the backend actually sends, including NULLs.

4. **Test the chain, not the link.** A test that proves "the API returns data" is useless if nothing proves "the service writes data." Test the full path: write -> store -> read -> display. If any link is missing, the test for the next link must fail.

5. **Enumerate systematically.** When writing tests for a feature, list every data store the feature touches, every endpoint it exposes, every page it renders. Then verify each one has a write test, a read test, and a display test. Do not rely on memory or intuition.

---

## Rule 4: Coverage audit before writing tests

**Before writing a single test, perform this audit. Skip it and you will miss entire layers.**

### Step 0a: Enumerate all data stores the feature touches

For every table/collection/store that the feature reads from or writes to:
1. **What production code writes to it?** (grep for INSERT/UPDATE/save/add/create operations)
2. **Does a test exist that calls that production write code?** (not a fixture insert)

If answer to 1 is "nothing" -- that's a bug. Write a FAILING test documenting it.
If answer to 2 is "no" -- write a test that calls the real write function and asserts the data exists.

### Step 0b: Enumerate all endpoints the feature exposes

For every read endpoint, verify the data it returns comes from a store that has a tested write path (from Step 0a). If the endpoint reads from a store with no writer, document it.

### Step 0c: Enumerate all pages/screens the feature renders

For every page, verify it calls an endpoint (from Step 0b) that returns data from a store with a tested write path (from Step 0a). If any link in the chain is missing, write a test that documents the gap.

### Step 0d: Produce a coverage matrix

Before writing tests, output a table:

| Store | Writer exists? | Writer tested? | Endpoint reads it? | Page displays it? | Gap |
|-------|---------------|---------------|--------------------|--------------------|-----|
| ... | yes/NO | yes/no | yes/no | yes/no/N/A | describe gap |

Every row with a "Gap" becomes a test you must write.

**Batch sizing**: If coverage matrix shows 20+ gaps, batch them: write 10-15 tests, run, fix failures, then next batch. Never write 40+ tests in one pass — it wastes tokens and makes debugging harder.

---

## Rule 5: Backend test quality gates

### Real tests vs mock-soup

| Real test | Mock-soup (DO NOT WRITE) |
|-----------|-----------------------------|
| Connects to a real database (test instance) | Mocks the entire DB layer |
| Sends HTTP requests via test client | Calls functions with all deps mocked |
| Asserts on HTTP status + response body | Asserts `mock.assert_called_with(...)` |
| Catches schema drift, query errors, wrong values | Catches nothing -- tests pass even if code is broken |

**Never write mock-soup.** Mocks are acceptable ONLY for external third-party APIs that cannot be called in tests (payment gateways, email providers, etc.). The database, the ORM, and internal services must be real.

### Backend story requirements

1. **Integration tests present**: tests use a real test client against a real app instance with a real database. Tests that only mock the DB layer: **FAIL**.
2. **Endpoints covered**: every endpoint added/modified has at least one integration test. Missing coverage: **FAIL**.
3. **Response model on all endpoints**: every endpoint declares its response model and correct status code. Missing either: **FAIL**.
4. **Auth enforced**: at least one test per protected endpoint sends a request without a token and asserts 401. Missing: **FAIL**.
5. **Write-path tested**: for every store the story writes to, verify a test calls the real production write function. Missing: **FAIL**.
6. **No fixture-only coverage**: if every test for a store starts by inserting fixture data, and no test calls the real function that produces that data in production: **FAIL**.
7. **Missing tests IS a FAIL**: a backend story with zero test files is incomplete.

---

## Rule 6: Frontend test quality gates

1. **Source assertions banned**: tests that read source files and assert on their content test code shape, not behavior. Any found: **FAIL**.
2. **API stories require behavior tests**: if the story adds data fetching, the test must use mock API (MSW, nock, etc.) to test real component behavior. Missing: **FAIL**.
3. **Error states tested**: for data-fetching components, check for error path tests. Missing: **warning**, not a FAIL.
4. **Loading states tested**: data-fetching components should handle loading state. Missing: **warning**.

---

## Rule 7: Invariant guards (conftest / global setup)

When the project has business invariants (e.g. "a completed order must always have a total > 0",
"a closed account must have zero balance"), enforce them as post-test hooks:

**Python example:**
```python
@pytest.fixture(autouse=True)
async def _assert_invariants(db_session, request):
    """After every test, verify no data violates business invariants."""
    yield
    # Query for rows that violate invariants
    # pytest.fail() if any found
```

**TypeScript example:**
```typescript
afterEach(async () => {
  // Query for data that violates invariants
  // throw if any found
});
```

This catches bugs even when the individual test never asserts on the invariant. Any test that exercises a write path -- even indirectly -- will trigger the guard.

**Fixture self-consistency**: fixtures that insert computed values must include assertions proving the values match the production formula. If fixture values drift from reality, the fixture itself fails.

---

## Rule 8: Test intentions -- the spec is the oracle

The story file (`specs/stories/[feature-id].yaml`) can contain a `test_intentions` section. When it does, every intention is a MANDATORY test case -- the builder must implement it.

### Format

```yaml
test_intentions:
  - function: calculate_total
    description: "order total computation with tax"
    inputs:
      subtotal: 100.00
      tax_rate: 0.20
      discount: 10.00
    oracle:
      tax_amount: "subtotal * tax_rate = 100.00 * 0.20 = 20.00"
      total: "(subtotal - discount) + tax_amount = (100.00 - 10.00) + 20.00 = 110.00"
    assertions:
      - "order.tax_amount == 20.00"
      - "order.total == 110.00"
    edge_cases:
      - description: "zero discount"
        inputs: { subtotal: 100.00, tax_rate: 0.20, discount: 0 }
        oracle: { total: "(100.00 - 0) + 20.00 = 120.00" }
        assertions: ["order.total == 120.00"]
      - description: "100% discount"
        inputs: { subtotal: 100.00, tax_rate: 0.20, discount: 100.00 }
        oracle: { total: "(100.00 - 100.00) + 0.00 = 0.00" }
        assertions: ["order.total == 0.00"]
```

### Who writes test_intentions?

The **refinement agent** writes them during refinement. For every formula or business rule in the story, the refiner picks concrete input values, does the step-by-step math, and writes the result. The refiner does the math so the builder doesn't have to. For every field rendered in the UI (Trigger C), the refiner declares the expected display string for null, formatted, and edge-case inputs — no arithmetic needed, the oracle is the mapping.

### Who consumes test_intentions?

The **developer** and **tester** read `test_intentions` from the story file before writing tests. Each intention becomes one test function:

1. The intention's `inputs` become the test setup
2. The intention's `oracle` becomes the `# ORACLE:` comment block
3. The intention's `assertions` become assert statements with appropriate precision
4. Each `edge_case` becomes an additional test (or a parametrized case)

### Rules

1. **Every test_intention MUST become a test.** Skipping an intention is a build failure.
2. **Never change the oracle values.** They were computed from the business rules. If your test produces a different number, either the code has a bug (document with xfail) or you called the wrong function.
3. **If the spec has no test_intentions for a formula, compute the oracle yourself.** Read the business rule from the spec or the production code, pick inputs, do the math, write the ORACLE comment.

### UI rendering test intentions (Trigger C)

When a story renders fields in the UI, the refinement agent MUST write test_intentions covering:

| What to test | Oracle format |
|---|---|
| Null/undefined field | `"formatFn(null) = '—'"` or `"formatFn(undefined) = 'N/A'"` |
| Date formatting | `"formatDate('2026-01-15T10:00:00Z') = 'January 15, 2026'"` |
| Currency formatting | `"formatCurrency(1234.56, 'USD') = '$1,234.56'"` |
| Negative value | `"formatCurrency(-500, 'USD') = '-$500.00'"` |
| Boolean display | `"formatBool(true) = 'Active'"` |
| Enum label | `"statusLabel('PENDING_REVIEW') = 'Pending Review'"` |
| Empty collection | `"items=[] renders EmptyState component"` |
| Unicode string | `"name='Ëlena Ñoño' renders unmangled"` |

The `assertions` field describes the expected UI state using your stack's query API:
- `"UI shows '$1,234.56'"` (adapt to your framework: `screen.getByText` for Testing Library, `by.text` for Detox, etc.)
- `"UI shows '—' placeholder"`

UI rendering intentions do NOT require ORACLE arithmetic. The oracle IS the expected display string.

---

## Rule 9: Test quality verification tools

Five techniques to empirically verify test effectiveness. Agents must use them when available.

### Mutation testing (mechanical)

Mutate production code (flip operators: `+` to `-`, `* 100` to `* 200`, `>` to `>=`), run tests, check if tests catch the mutations. If mutation score < 70%, tests are weak -- add stronger assertions. **Recommended for all backend stories.** The project's stack profile should specify the mutation testing tool.

### LLM fault scenarios

Generate realistic, business-logic-level fault scenarios that mechanical mutation testing would miss. Categories:

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

Each fault scenario becomes a targeted test that the tester must write.

### Ensemble test assessment

After tests pass, an LLM reviews each test function and scores it:

| Score | Meaning |
|-------|---------|
| STRONG | Calls real production code, verifies a business rule from the spec, would catch the fault scenario, ORACLE math is correct |
| WEAK | Passes most checks but has a gap (e.g. ORACLE uses wrong formula, assertion is too loose) |
| USELESS | Only asserts is-not-None or status code, no computed value verification |

USELESS tests must be rewritten before the feature can proceed.

### Schema fuzzing (API projects)

Auto-generate API tests from the OpenAPI/Swagger spec. Tests are spec-derived, not code-derived -- they cannot be tautological. Configure via the project's stack profile.

For projects with OpenAPI/Swagger specs, use **Schemathesis** (Python) or equivalent to validate that API mocks (MSW, nock) match the real schema:
- Run: `schemathesis run http://localhost:<port>/openapi.json --stateful=links`
- Any mock that returns a shape not matching the schema = test is lying
- Configure in stack profile: `schema_fuzz_tool`, `schema_url`

### Property-based testing

Generate random inputs, check invariants hold. Use for calculations, validators, pure logic with complex edge cases. Available via Hypothesis (Python), fast-check (TypeScript), gopter (Go), QuickCheck (Haskell), etc.

---

## Hard Constraints (apply to every test-writing agent)

- **NEVER use .skip() or .todo()** -- every test must execute
- **NEVER write fixture-shape tests** -- tests must call production code
- **NEVER write API mocks that match frontend expectations instead of backend schema.** Read the backend first. Always.
- **NEVER insert fixture data without verifying that production code also writes to that store.** If no production writer exists, write a failing test documenting the gap.
- **NEVER commit without running tests first** -- verify pass/fail/xfail counts match expectations
- **ALWAYS run the coverage audit (Rule 4) before writing any tests** -- this produces the test plan
- **ALWAYS follow the story file exactly** -- if the story says "test X", test X
- **ALWAYS run enforcement scripts after each batch** -- all scripts must pass before committing
- **ALWAYS run mutation testing when available** before committing. Score < 70% = weak tests.
- **If 100% of bug-catching tests pass: STOP** -- something is wrong with the tests
- **ALWAYS test from the user's perspective first.** Before writing any unit test, ask: "What does the user see for this feature?" If it shows empty data, wrong numbers, or broken UI -- that is test #1.
- **NEVER assert a computed value without an ORACLE block.** No oracle = no commit.
- **NEVER skip a test_intention from the spec.** Every intention becomes a test. No exceptions.
- **NEVER change oracle values from test_intentions.** If the code produces a different number, the code has a bug -- use xfail.
- **NEVER write assertions that only check existence or type on computed results** -- see Rule 2b banlist
