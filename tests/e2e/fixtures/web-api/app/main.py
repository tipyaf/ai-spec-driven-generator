"""Minimal FastAPI app used as an e2e fixture for SDD gate routing tests.

Not a real product — just enough to exercise web-api pipeline shape.
"""
from __future__ import annotations


class _Route:
    def __init__(self, path: str, handler):
        self.path = path
        self.handler = handler


class _MicroApp:
    """Tiny FastAPI-lookalike so fixture runs without the real dep."""

    def __init__(self) -> None:
        self.routes: list[_Route] = []

    def get(self, path: str):
        def deco(fn):
            self.routes.append(_Route(path, fn))
            return fn
        return deco


app = _MicroApp()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/echo/{msg}")
def echo(msg: str) -> dict:
    return {"echo": msg}
