"""The `manimvox` command line."""

from __future__ import annotations

import argparse
import sys

from . import __version__


def _cmd_new(args) -> int:
    from .scaffold import new_project

    d = new_project(args.dir, args.series, args.tagline, args.voice)
    print(f"project ready: {d}")
    print("next: facts into FACTS.md, outline into SERIES.md, episodes into series.json and episodes/")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="manimvox", description="Narrated, animated explainer videos with Manim.")
    p.add_argument("--version", action="version", version=f"manimvox {__version__}")
    p.add_argument("-y", "--yes", action="store_true", help="answer yes to confirmations (model downloads)")
    p._sub = p.add_subparsers(dest="cmd", metavar="<command>")
    s = p._sub.add_parser("new", help="create a project folder")
    s.add_argument("dir")
    s.add_argument("--series", required=True, help='name on every title card, e.g. "Runtime, Explained"')
    s.add_argument("--tagline", default="")
    s.add_argument("--voice", default="kokoro:af_heart", help="engine:voice")
    s.set_defaults(func=_cmd_new)
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:
        p.print_help()
        return 2
    from .project import ProjectError
    from .voice import VoiceError

    try:
        return func(args)
    except (ProjectError, VoiceError, FileNotFoundError) as e:
        print(f"manimvox: {e}", file=sys.stderr)
        return 1
