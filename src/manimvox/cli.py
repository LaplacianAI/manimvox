"""The `manimvox` command line."""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

from . import __version__


def _cmd_new(args) -> int:
    from .tools import new_project

    r = new_project(args.dir, args.series, args.tagline, args.voice)
    print(f"project ready: {r.project}")
    print(f"next: {r.next}")
    return 0


def _confirm(args):
    import os

    from .confirm import make_confirm

    return make_confirm(args.yes, os.environ, sys.stdin)


def _cmd_draft(args) -> int:
    from .tools import draft

    if not args.every > 0:
        print("manimvox: --every must be greater than 0", file=sys.stderr)
        return 2
    r = draft(str(Path.cwd()), args.episode, args.every)
    print(f"draft: {r.video}")
    print(f"sheets: {', '.join(r.sheets)}")
    for f in r.findings:
        print(f)
    print(r.summary)
    return 0 if r.ok else 1


def _cmd_sheets(args) -> int:
    from .tools import contact_sheet

    if not args.every > 0:
        print("manimvox: --every must be greater than 0", file=sys.stderr)
        return 2
    r = contact_sheet(str(Path.cwd()), args.episode, args.every)
    print(f"video: {r.video}")
    print(f"sheets: {', '.join(r.sheets)}")
    return 0


def _cmd_render(args) -> int:
    from .tools import _render

    r = _render(str(Path.cwd()), args.episode, args.voice, _confirm(args), print)
    print(f"final: {r.video}  (voice {r.voice})")
    print(r.audio)
    return 0 if r.ok else 1


def _cmd_check(args) -> int:
    from .tools import check

    if args.what != "theme" and not args.episode:
        print(f"manimvox: check {args.what} needs an episode", file=sys.stderr)
        return 2
    r = check(str(Path.cwd()), args.what, args.episode)
    if r.check == "audio":
        lines = [*r.notes, r.summary, *(f"    {f}" for f in r.findings)]
    else:
        lines = [*r.findings, *r.notes, r.summary]
    for line in lines:
        print(line)
    return 0 if r.ok else 1


def _cmd_join(args) -> int:
    from .tools import join

    out = str(Path(args.output).resolve()) if args.output else None  # -o is relative to where the command runs
    r = join(str(Path.cwd()), args.episodes or None, out, cards=not args.no_cards)
    secs = round(r.seconds)
    n = len(r.episodes)
    print(f"joined {n} episode{'s' if n != 1 else ''}: {r.video} ({secs // 60}:{secs % 60:02d})")
    return 0


def _cmd_add(args) -> int:
    from .tools import _add_blocks, list_blocks

    if args.list or not args.names:
        for b in list_blocks().blocks:
            print(f"{b.name:<18} {b.description}  [{', '.join(b.tags)}]")
        if not args.list:
            print("add one: manimvox add <block>")
        return 0
    for b in _add_blocks(str(Path.cwd()), args.names, args.force, "pass --force to replace them").added:
        print(f"added {b.name}: {b.path}")
        print(f"  in an episode: {b.import_line}")
    return 0


def _cmd_voices(args) -> int:
    from .tools import _prepare_voice, voices

    if args.prepare:
        r = _prepare_voice(args.prepare, None, _confirm(args))
        print(f"ready: {r.voice}")
        if not args.engine:
            return 0
    if args.engine:
        r = voices(args.engine)
        for n in r.notes:
            print(n)
        for v in r.voices:
            print(f"{v.voice:<36} {v.description}".rstrip())
        return 0
    for e in voices().engines:
        print(f"{e.name:<11}{'ready' if e.ready else 'not ready':<10} {e.detail}")
        print(f"{'':<11}licence: {e.licence}")
        if e.online:
            print(f"{'':<11}online: narration text is sent to {e.online}")
        if e.noncommercial:
            print(f"{'':<11}non-commercial use only")
    print("voices of one engine: manimvox voices <engine>")
    return 0


def _cmd_doctor(args) -> int:
    from .tools import doctor

    r = doctor()
    for row in r.rows:
        print(f"{row.mark:<4} {row.what}{'  → ' + row.hint if row.mark == 'FAIL' else ''}")
    return 0 if r.ok else 1


def _cmd_index(args) -> int:
    from .tools import index

    r = index(str(Path.cwd()))
    for stem in r.skipped:
        print(f"skipped {stem} (not rendered)")
    print(f"wrote {r.page}: {r.episodes} episode{'s' if r.episodes != 1 else ''}, about {r.minutes} min")
    return 0


def _cmd_package(args) -> int:
    from .tools import package

    r = package(str(Path.cwd()))
    for stem in r.skipped:
        print(f"skipped {stem} (not rendered)")
    for z in r.zips:
        print(f"{Path(z.path).name}: {z.megabytes:.1f} MB")
        if z.note:
            print(z.note)
    return 0


def _skills_scope(args) -> str:
    return "global" if getattr(args, "global_", False) else "project"


def _ask(prompt: str) -> str | None:
    try:
        return input(prompt).strip().lower()
    except EOFError:
        return None  # no answer is a no


def _pick_agents(args, found):
    """The agents to install for, or None after saying why not (the caller's exit code is in `_NO_AGENTS`)."""
    from . import skills_admin as sa

    if args.agent:
        return [sa.BY_ID[a] for a in args.agent]
    if args.yes:
        return list(found)
    if sa.is_tty():
        for i, a in enumerate(found, 1):
            print(f"  {i}. {a.id}")
        reply = _ask("Install for which agents? (e.g. 1,3 or all) ")
        if reply is None:
            return []
        if reply in ("", "all"):
            return list(found)
        try:
            return [found[int(n) - 1] for n in reply.replace(" ", "").split(",") if n]
        except (ValueError, IndexError):
            raise ValueError(f"not a list of numbers from 1 to {len(found)}: {reply}") from None
    print(
        "manimvox: no terminal to ask which agents: pass --agent ID (repeatable) or --yes for every detected agent",
        file=sys.stderr,
    )
    return None


def _skills_npx(args, sa, npx, ids, scope_global, home, src) -> int:
    """Hand the install to `npx skills`, after checking that it cannot clobber anything that is not ours."""
    scope = "global" if scope_global else "project"
    root = Path.cwd()
    agents = [sa.BY_ID[i] for i in ids] if ids else list(sa.AGENTS)
    dirs = sa.targets(agents + [sa.BY_ID["universal"]], scope, root, home)
    for d in dirs:
        sa._guard(d, src)
    refused = False
    for d in dirs:
        for name in sa.SKILL_NAMES:
            e = d / name
            if (e.exists() or sa._is_link(e)) and not sa._is_ours(e):
                print(f"{e} exists and is not a manimvox skill; left untouched")
                refused = True
    if refused:
        return 1
    cmd = sa.npx_command(ids, scope_global, args.copy, args.yes, src, npx)
    print("manimvox: running " + shlex.join(cmd))
    code = sa.run_npx(cmd)
    if code:
        print("manimvox: npx failed; `manimvox skills install --native` installs without it", file=sys.stderr)
    return code


def _skills_install(args, home) -> int:
    from . import skills_admin as sa
    from .skills import skills_path

    unknown = [a for a in args.agent or [] if a not in sa.BY_ID]
    if unknown:
        print(f"manimvox: unknown agent {unknown[0]}; known: {', '.join(sa.BY_ID)}", file=sys.stderr)
        return 2
    if not args.yes and not sa.is_tty():
        print("manimvox: no terminal to ask: pass --yes (with --agent ID to choose agents)", file=sys.stderr)
        return 2
    found = sa.detect_agents(home)
    scope_global = getattr(args, "global_", False)
    npx, ignored = (None, False) if args.native else sa.find_npx()
    if ignored and not npx:
        print("manimvox: ignored npx in the current folder; using the built-in installer", file=sys.stderr)
    old = sa.node_too_old(npx) if npx else None
    if old:
        print(f"manimvox: {old}; using the built-in installer", file=sys.stderr)
        npx = None
    if npx:
        real = [a.id for a in found if a.id != "universal"]  # npx maps "universal" to another folder
        ids = list(args.agent) if args.agent else (real if args.yes else None)
        if args.yes and not ids:
            # no -a would make npx install into every agent it knows (about 80): use the shared folder instead
            print("manimvox: no agent detected; installed into the shared .agents/skills folder")
        else:
            return _skills_npx(args, sa, npx, ids, scope_global, home, skills_path())
    agents = _pick_agents(args, found)
    if agents is None:
        return 2
    if not agents:
        print("manimvox: no agents chosen", file=sys.stderr)
        return 1
    if args.project:
        scope = "project"
    elif scope_global:
        scope = "global"
    elif args.yes or not sa.is_tty():
        scope = "project"
    else:
        scope = "global" if (_ask("Install for this project or globally? [P/g] ") or "").startswith("g") else "project"
    msgs, skipped = sa.install_checked(sa.targets(agents, scope, Path.cwd(), home), "copy" if args.copy else "link")
    for line in msgs:
        print(line)
    return 1 if skipped else 0


def _cmd_skills(args) -> int:
    from . import skills_admin as sa

    home = Path.home()
    if args.action == "install":
        return _skills_install(args, home)
    scope = _skills_scope(args)
    dirs = [t for t in sa.known_targets(scope, Path.cwd(), home) if sa.holds_ours(t)]
    if args.action == "check":
        if not dirs:
            print(f"no manimvox skills installed in {scope} agent folders; run manimvox skills install")
            return 1
        bad = False
        for t in dirs:
            st = sa.status(t)
            if set(st.values()) == {"ok"}:
                print(f"{t}: ok")
            else:
                bad = True
                print(f"{t}: " + ", ".join(f"{n} {v}" for n, v in st.items() if v != "ok"))
        return 1 if bad else 0
    if args.action == "update":
        if not dirs:
            print(f"no manimvox skills installed in {scope} agent folders; run manimvox skills install")
            return 1
        skipped = False
        for t in dirs:
            linked = any(sa._is_link(t / n) and sa._is_ours(t / n) for n in sa.SKILL_NAMES)
            msgs, sk = sa.install_checked([t], "link" if linked else "copy")
            skipped = skipped or sk
            for line in msgs:
                print(line)
        return 1 if skipped else 0
    if not dirs:
        print("no manimvox skills found")
        return 0
    if not args.yes:
        if not sa.is_tty():
            print("manimvox: no terminal to ask: pass --yes to remove the skills", file=sys.stderr)
            return 2
        reply = _ask(f"Remove the manimvox skills from {', '.join(str(t) for t in dirs)}? [y/N] ")
        if not (reply or "").startswith("y"):
            return 1
    for gone in sa.remove(dirs):
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

    s = p._sub.add_parser("sheets", help="contact sheets of the finished video (else the last draft)")
    s.add_argument("episode")
    s.add_argument("--every", type=float, default=5.0, help="seconds between sampled frames")
    s.set_defaults(func=_cmd_sheets)

    s = p._sub.add_parser("check", help="run one check")
    s.add_argument("what", choices=["theme", "layout", "audio"])
    s.add_argument("episode", nargs="?")
    s.set_defaults(func=_cmd_check)

    s = p._sub.add_parser("index", help="playlist page out/index.html from the rendered episodes")
    s.set_defaults(func=_cmd_index)

    s = p._sub.add_parser("package", help="share/<Name> and share/<Name>-720p folders and zips")
    s.set_defaults(func=_cmd_package)

    s = p._sub.add_parser("join", help="join rendered episodes into one video behind a title card")
    s.add_argument("episodes", nargs="*", help="episodes in order (default: every rendered episode)")
    s.add_argument("-o", "--output", help="the joined MP4 (default: out/<series>.mp4)")
    s.add_argument("--no-cards", action="store_true", help="no title card (each episode keeps its own end card)")
    s.set_defaults(func=_cmd_join)

    s = p._sub.add_parser("add", help="copy blocks (reusable scene components) into this project's blocks/")
    s.add_argument("names", nargs="*", metavar="block")
    s.add_argument("--list", action="store_true", help="list the blocks")
    s.add_argument("--force", action="store_true", help="replace a block already in the project")
    s.set_defaults(func=_cmd_add)

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
    for verb, text, ask in (
        ("check", "say whether installed skills match this version", False),
        ("update", "reinstall the skills where they already are", True),
        ("remove", "delete the manimvox skills, and only those", True),
    ):
        a = sub.add_parser(verb, help=text)
        g = a.add_mutually_exclusive_group()
        g.add_argument("--global", dest="global_", action="store_true", help="the global agent folders")
        g.add_argument("--project", action="store_true", help="this project's agent folders (default)")
        if ask:
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
    from .post.options import PostError
    from .project import ProjectError
    from .runner import RenderError
    from .tools import ToolError
    from .voice import VoiceError

    try:
        return func(args)
    except (ToolError, ProjectError, VoiceError, RenderError, PostError, ValueError, OSError) as e:
        print(f"manimvox: {e}", file=sys.stderr)
        return 1
