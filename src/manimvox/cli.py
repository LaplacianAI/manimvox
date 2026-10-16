"""The `manimvox` command line."""

from __future__ import annotations

import argparse

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="manimvox", description="Narrated, animated explainer videos with Manim.")
    p.add_argument("--version", action="version", version=f"manimvox {__version__}")
    p.add_argument("-y", "--yes", action="store_true", help="answer yes to confirmations (model downloads)")
    p._sub = p.add_subparsers(dest="cmd", metavar="<command>")
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:
        p.print_help()
        return 2
    return func(args)
