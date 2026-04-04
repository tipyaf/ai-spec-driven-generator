# Tester Agent — Reference

Code examples, test templates, report formats, and detailed tables for the Tester agent.
See `agents/tester.md` for the core behavioral rules.

---

## Code Examples

### Unit Test Structure (TypeScript)
```typescript
describe("[Module] - [Feature]", () => {
  describe("[Method/Action]", () => {
    it("should [expected behavior] when [condition]", () => {
      // Arrange — prepare data
      // Act — execute action
      // Assert — verify result
    });
  });
});
```

### Playwright E2E with Responsive Breakpoints
```typescript
import { test, expect } from "@playwright/test";

const breakpoints = [
  { name: "mobile", width: 320, height: 568 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "desktop", width: 1440, height: 900 },
];

for (const bp of breakpoints) {
  test(`[Feature] — user flow at ${bp.name}`, async ({ page }) => {
    await page.setViewportSize({ width: bp.width, height: bp.height });
    await page.goto("/target-page");
    // ... interact with the page ...
    await expect(page).toHaveScreenshot(`feature-${bp.name}.png`);
  });
}
```

### CLI Command Invocation Tests
```typescript
import { execSync } from "child_process";

describe("[CLI Feature]", () => {
  it("should output expected result for valid input", () => {
    const result = execSync("mycli run --input test.json").toString();
    expect(result).toContain("Success");
  });

  it("should exit with code 1 for invalid input", () => {
    expect(() => execSync("mycli run --input missing.json")).toThrow();
  });
});
```

### API Integration Test
```typescript
import request from "supertest";

describe("GET /api/resource", () => {
  it("should return 200 with expected data", async () => {
    const res = await request(app).get("/api/resource").expect(200);
    expect(res.body.data).toHaveLength(3);
    expect(res.body.data[0].id).toBe(expectedId);
  });
});
```

### WCAG Accessibility Audit (axe-core + Playwright)
```typescript
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("WCAG 2.1 AA audit — [page name]", async ({ page }) => {
  await page.goto("/target-page");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});
```

---

## What to Test by Layer

| Layer | What to test | Test type |
|-------|-------------|-----------|
| Models / Entities | Validation, transformations | Unit |
| Services / Use cases | Business logic, edge cases | Unit |
| Controllers / Routes | Request/response, status codes | Integration |
| Database | Queries, migrations | Integration |
| UI Components | Rendering, interactions | Unit (+ snapshot) |
| User journeys | Complete flows | E2E |
| Accessibility | WCAG 2.1 AA compliance | E2E (axe-core) |
| Visual regression | Screenshot comparison | E2E (Playwright) |

---

## Test Requirements by Project Type

### API/Backend
- [ ] Integration tests with real database (test instance)
- [ ] Every endpoint tested: status code + response shape
- [ ] Auth tests: 401 without token, 403 without permission
- [ ] Validation tests: 422 on invalid input
- [ ] Error handling: proper error responses on failures
- [ ] **NEVER** mock the database for integration tests

### Web/Frontend
- [ ] Behavior tests (test what user sees, not code structure)
- [ ] Mock Service Worker for API calls (not inline mocks)
- [ ] Error states tested (network failure, 500, empty data)
- [ ] Loading states tested
- [ ] **NEVER** use source assertions (testing code shape instead of behavior)
- [ ] Accessibility basics: aria-labels tested

### CLI
- [ ] Command output verified (exact match or pattern)
- [ ] Exit codes verified (0 for success, non-zero for errors)
- [ ] Error messages tested (invalid args, missing files)
- [ ] Help text verified

### Library
- [ ] Public API fully tested (every exported function/class)
- [ ] Edge cases: null, empty, boundary values
- [ ] Error handling: thrown exceptions documented and tested
- [ ] Type safety: generic type parameters tested

---

## AC Validation Report Template

```markdown
## AC Validation Report — Feature: [name]

| AC ID | Description | Status | Test(s) | Notes |
|-------|-------------|--------|---------|-------|
| AC-XXX-01 | [criterion summary] | PASS | test_xxx_01 | — |
| AC-XXX-02 | [criterion summary] | FAIL | test_xxx_02 | [failure reason] |
| AC-XXX-03 | [criterion summary] | PASS | test_xxx_03 | — |

**Result: X/Y passed — [FEATURE DONE | FEATURE NOT DONE]**
```

---

## Full Test Report Template

```markdown
## Test Report

### AC Validation
[AC Validation Report as above — ALWAYS FIRST]

### Automated Gate Results
| Gate | Status | Detail |
|------|--------|--------|
| Unit tests | PASS/FAIL | X passed / Y total |
| E2E tests | PASS/FAIL | X passed / Y total |
| WCAG audit | PASS/FAIL | X violations found |
| Visual regression | PASS/FAIL | X screenshots differ |
| Code coverage | PASS/FAIL | X% (threshold: Y%) |
| Linter | PASS/FAIL | X errors |
| Build | PASS/FAIL | — |

**Overall: ALL GATES PASSED / X GATE(S) FAILED**

### Additional Tests
- Unit tests: XX passed / XX total
- Integration tests: XX passed / XX total
- E2E tests: XX passed / XX total
- Coverage: XX%

### Tests by feature
#### Feature: [name]
- [test 1]: description — PASS
- [test 2]: description — PASS
- [test 3]: description — FAIL — REASON

### Identified edge cases
- [case 1]: covered / not covered
- [case 2]: covered / not covered

### Escalations (if any)
- [feature]: [reason it cannot be tested automatically] — MANUAL_REVIEW_REQUIRED

### Recommendations
- [suggested improvement]
```

---

## Escalation Details

When a feature cannot be tested automatically:

1. **Document** exactly WHY the test cannot be automated
2. **List** what manual verification would be needed
3. **Flag** with `ESCALATION: MANUAL_REVIEW_REQUIRED` in the test report
4. This is the **ONLY** case where human involvement is acceptable

Common untestable scenarios:
- External API with no sandbox/test environment
- Hardware dependencies (sensors, peripherals)
- Third-party OAuth flows without test mode
- Visual/UX quality requiring human judgment
