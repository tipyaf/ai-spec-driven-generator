import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import app, health, echo


def test_health():
    assert health() == {"status": "ok"}


def test_echo():
    assert echo("hi") == {"echo": "hi"}


def test_routes_registered():
    paths = {r.path for r in app.routes}
    assert "/health" in paths
    assert "/echo/{msg}" in paths
