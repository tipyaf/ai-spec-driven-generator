---
name: review
description: Review code quality, security, and test coverage for a story or PR. Use before creating a PR or after implementation.
---

Load and follow the reviewer agent:
@../agents/reviewer.md

Load the security agent:
@../agents/security.md

Load the tester agent for test quality verification:
@../agents/tester.md

## Workflow
1. Read the git diff or PR changes
2. Run the 3-pass code review (KISS, static analysis, safety)
3. Run security audit
4. Verify test quality (no mock-soup, real integration tests)
5. Produce structured PASS/FAIL report
6. If FAIL, return issues to developer
