---
name: validate
description: Independently validate an implementation against its spec. Takes screenshots, greps for anti-patterns, curls endpoints. Use after development to verify before PR.
---

Load and follow the validator agent:
@../agents/validator.md

## Workflow
1. Read the spec and acceptance tests
2. Read the git diff to identify changes
3. Read the implementation manifest
4. Run all validation checks (visual, code, runtime, acceptance tests)
5. Produce structured PASS/FAIL report with evidence
