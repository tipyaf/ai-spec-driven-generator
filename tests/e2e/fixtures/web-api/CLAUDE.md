# web-api fixture

Minimal FastAPI-shaped project used by `tests/e2e/test_pipeline_per_type.py`
to exercise orchestrator routing for `spec.type: web-api`.

The SDD framework lives two directory levels up — tests pass
`SDD_FRAMEWORK_ROOT` via env var when invoking the orchestrator.
