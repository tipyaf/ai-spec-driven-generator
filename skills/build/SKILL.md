---
name: build
description: Build/implement a refined story. Reads the spec, follows the manifest, writes code, runs tests. Use after a story has been refined.
---

Load and follow the instructions in the orchestrator:
@../agents/orchestrator.md

Load the developer agent:
@../agents/developer.md

Load the validator agent for post-implementation verification:
@../agents/validator.md

## Workflow
1. Read the refined story and implementation manifest
2. Read LESSONS.md for known pitfalls
3. Follow the developer agent workflow to implement
4. Run the validator agent to verify (Phase 3.5)
5. If validation fails, fix and re-validate (max 3 cycles)
6. Report status to user
