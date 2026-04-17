"""Collection guard: the directories below this conftest are FIXTURE projects.

Their own tests are for the fixture to exercise, not for our outer pytest run.
`collect_ignore_glob` prevents pytest from descending into them.
"""
collect_ignore_glob = ["*/tests/*", "*/tests/", "*"]
