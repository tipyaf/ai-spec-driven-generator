import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli import run, VERSION


def _capture(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = run(argv)
    return code, out.getvalue(), err.getvalue()


def test_help():
    code, out, _ = _capture(["--help"])
    assert code == 0
    assert "Usage" in out
    assert "Commands" in out


def test_version():
    code, out, _ = _capture(["--version"])
    assert code == 0
    assert VERSION in out


def test_greet():
    code, out, _ = _capture(["greet", "Alice"])
    assert code == 0
    assert out.strip() == "Hello Alice!"


def test_greet_missing_name():
    code, _, err = _capture(["greet"])
    assert code == 2
    assert "NAME" in err
