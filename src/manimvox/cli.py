"""The `manimvox` command line."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__


def _cmd_new(args) -> int:
    from .scaffold import new_project

    d = new_project(args.dir, args.series, args.tagline, args.voice)
    print(f"project ready: {d}")
    print("next: facts into FACTS.md, outline into SERIES.md, episodes into series.json and episodes/")
    return 0


def _project():
    from pathlib import Path

    from .project import find_project, load_project

    return load_project(find_project(Path.cwd()))


def _confirm(args):
    import os

    from .confirm import make_confirm

    return make_confirm(args.yes, os.environ, sys.stdin)


def _cmd_draft(args) -> int:
    from .checks.layout import check_layout, load_layout
    from .checks.sheets import contact_sheets
    from .runner import render_episode

    if not args.every > 0:
        print("manimvox: --every must be greater than 0", file=sys.stderr)
        return 2
    pr = _project()
    ep = pr.episode(args.episode)
    mp4 = render_episode(pr, ep, "draft", None)
    sheets = contact_sheets(mp4, pr.sheets_dir / ep.stem, every=args.every)
    print(f"draft: {mp4}")
    print(f"sheets: {', '.join(str(s) for s in sheets)}")
    findings = check_layout(load_layout(pr.build_dir / ep.stem / "layout.json"))
    for f in findings:
        print(f)
    print("layout check: ok" if not findings else f"layout check: {len(findings)} finding(s)")
    return 1 if findings else 0


def _cmd_render(args) -> int:
    import os
    import shutil

    from .checks.audio import check_audio
    from .runner import render_episode
    from .voice import get_engine, resolve_voice

    pr = _project()
    ep = pr.episode(args.episode)
    spec = resolve_voice(args.voice, pr.voice, os.environ)
    eng = get_engine(spec.engine)
    eng.prepare(spec.voice, _confirm(args), pr.root)
    if eng.online:
        print(f"note: narration text is sent to {eng.online} ({spec})")
    if eng.noncommercial:
        print(f"note: {spec.engine} is for non-commercial use only: {eng.licence}")
    out = pr.out_dir / f"{ep.stem}.mp4"
    out.unlink(missing_ok=True)
    (pr.out_dir / f"{ep.stem}.srt").unlink(missing_ok=True)
    built = render_episode(pr, ep, "final", spec)
    pr.out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built, out)
    print(f"final: {out}  (voice {spec})")
    rep = check_audio(out, pr.out_dir / f"{ep.stem}.srt")
    print(rep)
    return 0 if rep.ok else 1


def _cmd_check(args) -> int:
    from .checks.audio import check_audio
    from .checks.layout import check_layout, load_layout
    from .checks.theme import check_theme
    from .kit.theme import Theme

    pr = _project()
    if args.what == "theme":
        theme = Theme.from_dict(pr.theme)
        found = check_theme(theme, pr.root)
        for f in found:
            print(f)
        if theme.defaulted:
            print(f"note: roles from the kit's neutral default: {', '.join(theme.defaulted)}")
        print("theme check: ok" if not found else f"theme check: {len(found)} failure(s)")
        return 1 if found else 0
    if not args.episode:
        print(f"manimvox: check {args.what} needs an episode", file=sys.stderr)
        return 2
    ep = pr.episode(args.episode)
    if args.what == "layout":
        found = check_layout(load_layout(pr.build_dir / ep.stem / "layout.json"))
        for f in found:
            print(f)
        print("layout check: ok" if not found else f"layout check: {len(found)} finding(s)")
        return 1 if found else 0
    rep = check_audio(pr.out_dir / f"{ep.stem}.mp4", pr.out_dir / f"{ep.stem}.srt")
    print(rep)
    return 0 if rep.ok else 1


def _cmd_voices(args) -> int:
    from pathlib import Path

    from .project import ProjectError, find_project
    from .voice import engine_names, get_engine, parse_voice

    if args.prepare:
        p = args.prepare
        if ":" in p:
            spec = parse_voice(p)
            eng = get_engine(spec.engine)
            voice = spec.voice
        else:
            eng = get_engine(p.strip().lower())
            voice = eng.default_voice
        try:
            root = find_project(Path.cwd())
        except ProjectError:
            root = Path.cwd()
        eng.prepare(voice, _confirm(args), root)
        print(f"ready: {eng.name}:{voice}")
        if not args.engine:
            return 0
    if args.engine:
        eng = get_engine(args.engine.strip().lower())
        rows = eng.describe_voices()
        if not rows:
            print(f"{eng.name}: no voices listed ({eng.status().detail})")
        for v, desc in rows:
            print(f"{v:<36} {desc}".rstrip())
        return 0
    for name in engine_names():
        e = get_engine(name)
        st = e.status()
        print(f"{name:<11}{'ready' if st.ready else 'not ready':<10} {st.detail}")
        print(f"{'':<11}licence: {e.licence}")
        if e.online:
            print(f"{'':<11}online: narration text is sent to {e.online}")
        if e.noncommercial:
            print(f"{'':<11}non-commercial use only")
    print("voices of one engine: manimvox voices <engine>")
    return 0


def _cmd_doctor(args) -> int:
    import platform

    problems = 0

    def row(ok, what, hint=""):
        nonlocal problems
        problems += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {what}{'' if ok else '  → ' + hint}")

    row(sys.version_info >= (3, 11), f"python {platform.python_version()}", "manimvox needs Python 3.11+")
    cairo_hint = {
        "darwin": "brew install cairo pkg-config, then reinstall manimvox",
        "win32": "reinstall manimvox (pycairo ships Windows wheels; check your Python is 64-bit)",
    }.get(sys.platform, "sudo apt install libcairo2-dev pkg-config python3-dev (or your distro's cairo dev "
                        "package), then reinstall manimvox")
    for mod, hint in (("cairo", cairo_hint), ("manimpango", "reinstall manimvox"), ("av", "reinstall manimvox"),
                      ("manim", "reinstall manimvox")):
        try:
            m = __import__(mod)
            row(True, f"{mod} {getattr(m, '__version__', '')}".strip())
        except ImportError:
            row(False, mod, hint)
    try:
        import manimpango

        row(True, f"{len(manimpango.list_fonts())} fonts visible to Pango")
    except ImportError:
        pass
    from .voice import engine_names, get_engine

    for name in engine_names():
        st = get_engine(name).status()
        print(f"{'ok  ' if st.ready else '--  '} voice {name}: {st.detail}")
    return 1 if problems else 0


def _cmd_index(args) -> int:
    from .playlist import build_index

    page, n, total = build_index(_project())
    print(f"wrote {page}: {n} episode{'s' if n != 1 else ''}, about {max(1, round(total / 60))} min")
    return 0


def _cmd_package(args) -> int:
    from .playlist import package

    for z in package(_project()):
        print(f"{z.name}: {z.stat().st_size / 1e6:.1f} MB")
    return 0


def _skills_scope(args) -> str:
    return "global" if getattr(args, "global_", False) else "project"


def _pick_agents(args, found):
    from . import skills_admin as sa

    if args.agent:
        unknown = [a for a in args.agent if a not in sa.BY_ID]
        if unknown:
            raise ValueError(f"unknown agent {unknown[0]}; known: {', '.join(sa.BY_ID)}")
        return [sa.BY_ID[a] for a in args.agent]
    if sa.is_tty():
        for i, a in enumerate(found, 1):
            print(f"  {i}. {a.id}")
        reply = input("Install for which agents? (e.g. 1,3 or all) ").strip().lower()
        if reply in ("", "all"):
            return list(found)
        try:
            return [found[int(n) - 1] for n in reply.replace(" ", "").split(",") if n]
        except (ValueError, IndexError):
            raise ValueError(f"not a list of numbers from 1 to {len(found)}: {reply}") from None
    if args.yes:
        return list(found)
    print(
        "manimvox: no terminal to ask which agents: pass --agent ID (repeatable) or --yes for every detected agent",
        file=sys.stderr,
    )
    return None


def _skills_install(args, home) -> int:
    from . import skills_admin as sa
    from .skills import skills_path

    found = sa.detect_agents(home)
    scope_global = getattr(args, "global_", False)
    if sa.has_npx() and not args.native:
        if not args.yes and not sa.is_tty():
            print(
                "manimvox: no terminal to ask: pass --yes (with --agent ID to choose agents)",
                file=sys.stderr,
            )
            return 2
        ids = list(args.agent) if args.agent else ([a.id for a in found] if args.yes else None)
        return sa.run_npx(sa.npx_command(ids, scope_global, args.copy, args.yes, skills_path()))
    agents = _pick_agents(args, found)
    if agents is None:
        return 2
    if args.project:
        scope = "project"
    elif scope_global:
        scope = "global"
    elif sa.is_tty():
        scope = "global" if input("Install for this project or globally? [P/g] ").strip().lower().startswith("g") else "project"
    else:
        scope = "project"
    for line in sa.install(sa.targets(agents, scope, Path.cwd(), home), "copy" if args.copy else "link"):
        print(line)
    return 0


def _cmd_skills(args) -> int:
    from . import skills_admin as sa

    home = Path.home()
    if args.action == "install":
        return _skills_install(args, home)
    dirs = sa.targets(sa.detect_agents(home), _skills_scope(args), Path.cwd(), home)
    if args.action == "check":
        bad = False
        for t in dirs:
            if not sa.holds_ours(t):
                continue
            st = sa.status(t)
            if set(st.values()) == {"ok"}:
                print(f"{t}: ok")
            else:
                bad = True
                print(f"{t}: " + ", ".join(f"{n} {v}" for n, v in st.items() if v != "ok"))
        return 1 if bad else 0
    if args.action == "update":
        for t in dirs:
            if sa.holds_ours(t):
                linked = any((t / n).is_symlink() for n in sa.SKILL_NAMES)
                for line in sa.install([t], "link" if linked else "copy"):
                    print(line)
        return 0
    ours = [t for t in dirs if sa.holds_ours(t)]
    if not ours:
        print("no manimvox skills found")
        return 0
    if not args.yes:
        if not sa.is_tty():
            print("manimvox: no terminal to ask: pass --yes to remove the skills", file=sys.stderr)
            return 2
        if not input(f"Remove the manimvox skills from {', '.join(str(t) for t in ours)}? [y/N] ").strip().lower().startswith("y"):
            return 1
    for gone in sa.remove(ours):
        print(f"removed {gone}")
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
    s = p._sub.add_parser("draft", help="fast 480p render, no voice, contact sheets and layout check")
    s.add_argument("episode")
    s.add_argument("--every", type=float, default=5.0, help="seconds between sampled frames")
    s.set_defaults(func=_cmd_draft)

    s = p._sub.add_parser("render", help="1080p render with voice, then the audio check")
    s.add_argument("episode")
    s.add_argument("--voice", default=None, help="engine:voice (overrides series.json)")
    s.add_argument("-y", "--yes", action="store_true", default=argparse.SUPPRESS, help="answer yes to confirmations")
    s.set_defaults(func=_cmd_render)

    s = p._sub.add_parser("check", help="run one check")
    s.add_argument("what", choices=["theme", "layout", "audio"])
    s.add_argument("episode", nargs="?")
    s.set_defaults(func=_cmd_check)

    s = p._sub.add_parser("index", help="playlist page out/index.html from the rendered episodes")
    s.set_defaults(func=_cmd_index)

    s = p._sub.add_parser("package", help="share/<Name> and share/<Name>-720p folders and zips")
    s.set_defaults(func=_cmd_package)

    s = p._sub.add_parser("voices", help="voice engines: ready or not, licence, voices")
    s.add_argument("engine", nargs="?", help="list this engine's voices")
    s.add_argument(
        "--prepare", metavar="ENGINE[:VOICE]", help="get ENGINE (or one of its voices) ready: downloads ask first"
    )
    s.add_argument("-y", "--yes", action="store_true", default=argparse.SUPPRESS, help="answer yes to confirmations")
    s.set_defaults(func=_cmd_voices)

    s = p._sub.add_parser("skills", help="install, check, update or remove the agent skills")
    sub = s.add_subparsers(dest="action", metavar="<action>", required=True)
    yes = {"action": "store_true", "default": argparse.SUPPRESS, "help": "answer yes to confirmations"}
    a = sub.add_parser("install", help="put the skills where your coding agents look")
    a.add_argument("--agent", action="append", metavar="ID", help="an agent id (repeatable)")
    g = a.add_mutually_exclusive_group()
    g.add_argument("--global", dest="global_", action="store_true", help="install for every project")
    g.add_argument("--project", action="store_true", help="install in this project (default)")
    a.add_argument("--copy", action="store_true", help="copy the skills instead of linking them")
    a.add_argument("--native", action="store_true", help="do not use npx even if it is present")
    a.add_argument("-y", "--yes", **yes)
    a = sub.add_parser("check", help="say whether installed skills match this version")
    a.add_argument("--global", dest="global_", action="store_true")
    a = sub.add_parser("update", help="reinstall the skills where they already are")
    a.add_argument("--global", dest="global_", action="store_true")
    a = sub.add_parser("remove", help="delete the manimvox skills, and only those")
    a.add_argument("--global", dest="global_", action="store_true")
    a.add_argument("-y", "--yes", **yes)
    s.set_defaults(func=_cmd_skills)

    s = p._sub.add_parser("doctor", help="check system libraries, fonts and voice engines")
    s.set_defaults(func=_cmd_doctor)
    return p


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:  # a piped Windows console is cp1252: print what it cannot encode as escapes, never crash
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass
    p = build_parser()
    args = p.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:
        p.print_help()
        return 2
    from .project import ProjectError
    from .runner import RenderError
    from .voice import VoiceError

    try:
        return func(args)
    except (ProjectError, VoiceError, RenderError, ValueError, OSError) as e:
        print(f"manimvox: {e}", file=sys.stderr)
        return 1
