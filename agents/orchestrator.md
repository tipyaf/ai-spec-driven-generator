---
name: orchestrator
description: STUB — the orchestrator is now an executable script, not an agent. See `scripts/orchestrator.py`.
---

# Orchestrator — now executable

In v5 the orchestrator is no longer a documentation agent. The logic lives in `scripts/orchestrator.py` and is invoked by the skills (`/build`, `/validate`, `/review`, `/ship`). This stub exists only to redirect readers of the v4 layout — the file will be removed in v5.1.
