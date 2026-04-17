"""Tiny CLI for the SDD e2e CLI fixture.

Supports: `--help`, `--version`, and `greet <name>`.
"""
from __future__ import annotations

import argparse
import sys

VERSION = "0.1.0"

USAGE = (
    "Usage: python -m app.cli [--help] [--version] greet NAME\n"
    "Commands:\n"
    "  greet NAME    Print a greeting to NAME.\n"
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="greet", add_help=False)
    p.add_argument("--help", action="store_true")
    p.add_argument("--version", action="store_true")
    p.add_argument("command", nargs="?")
    p.add_argument("args", nargs="*")
    return p


def run(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    if args.help:
        sys.stdout.write(USAGE)
        return 0
    if args.version:
        sys.stdout.write(VERSION + "\n")
        return 0
    if args.command == "greet":
        if not args.args:
            sys.stderr.write("greet requires a NAME\n")
            return 2
        sys.stdout.write(f"Hello {args.args[0]}!\n")
        return 0
    sys.stderr.write(USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
