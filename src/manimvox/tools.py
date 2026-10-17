"""Typed functions that mirror the manimvox command, for agents with no shell.

Every tool takes the project folder (or any folder inside it) as `project`, where the command uses the current
folder. It returns a dataclass of plain values, so `dataclasses.asdict` gives JSON. A failed check is a result
with `ok=False` and its findings, as the command exits 1. A tool that cannot do what was asked raises ToolError,
whose message says what to do first. Nothing here prompts: a download goes ahead only with allow_download=True.
"""

from __future__ import annotations

import functools
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

Say = Callable[[str], None]
NEXT_STEPS = "facts into FACTS.md, outline into SERIES.md, episodes into series.json and episodes/"


class ToolError(Exception):
    """A tool could not do what was asked. The message says why, and what to run first."""


def _tool(fn):
    """Re-raise every failure the command reports as an error as a ToolError with the same message."""

    @functools.wraps(fn)
    def run(*args, **kwargs):
        from .post.options import PostError
        from .project import ProjectError
        from .runner import RenderError
        from .voice import VoiceError

        try:
            return fn(*args, **kwargs)
        except (ProjectError, VoiceError, RenderError, PostError, ValueError, OSError) as e:
            raise ToolError(str(e)) from e

    return run


def _open(project: str):
    from .project import find_project, load_project

    return load_project(find_project(Path(project).expanduser()))


def _layout_summary(found: list[str]) -> str:
    return "layout check: ok" if not found else f"layout check: {len(found)} finding(s)"


def _audio_lines(rep) -> tuple[str, list[str]]:
    """The audio report's first line, and one row per silent line."""
    head, *rows = str(rep).splitlines()
    return head, [r.strip() for r in rows]


@dataclass(frozen=True)
class ProjectResult:
    ok: bool
    project: str
    next: str


@dataclass(frozen=True)
class DraftResult:
    ok: bool
    video: str
    sheets: list[str]
    findings: list[str]
    summary: str


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    check: str
    summary: str
    findings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SheetsResult:
    ok: bool
    video: str
    sheets: list[str]


@_tool
def new_project(directory: str, series: str, tagline: str = "", voice: str = "kokoro:af_heart") -> ProjectResult:
    """Create a project folder with series.json, FACTS.md, SERIES.md, episodes/, out/ and research/.

    Args:
        directory: The folder to create, best given as an absolute path; it must not already hold a project.
        series: The series name shown on every title card, e.g. "Hash Maps, Explained".
        tagline: A short line shown under the series name.
        voice: The narration voice as engine:voice.
    """
    from .scaffold import new_project as scaffold

    d = scaffold(Path(directory).expanduser(), series, tagline, voice)
    return ProjectResult(True, str(d), NEXT_STEPS)


@_tool
def draft(project: str, episode: str, every: float = 5.0) -> DraftResult:
    """Render a fast 480p draft with no voice, write contact sheets and run the layout check.

    Args:
        project: The project folder, or any folder inside it.
        episode: The episode as listed in series.json: ep01, 1, or its file stem.
        every: Seconds between the frames sampled into the contact sheets; above 0.
    """
    from . import runner
    from .checks.layout import check_layout, load_layout
    from .checks.sheets import contact_sheets

    if not every > 0:
        raise ValueError("every must be greater than 0")
    pr = _open(project)
    ep = pr.episode(episode)
    mp4 = runner.render_episode(pr, ep, "draft", None)
    sheets = contact_sheets(mp4, pr.sheets_dir / ep.stem, every=every)
    found = [str(f) for f in check_layout(load_layout(pr.build_dir / ep.stem / "layout.json"))]
    return DraftResult(not found, str(mp4), [str(s) for s in sheets], found, _layout_summary(found))


@_tool
def check(project: str, what: str, episode: str | None = None) -> CheckResult:
    """Run one check: theme (colour contrast and fonts), layout (the last draft) or audio (every line audible).

    Args:
        project: The project folder, or any folder inside it.
        what: theme, layout or audio.
        episode: The episode, for layout and audio: ep01, 1, or its file stem.
    """
    what = what.strip().lower()
    if what not in ("theme", "layout", "audio"):
        raise ValueError(f"check must be theme, layout or audio, got {what!r}")
    pr = _open(project)
    if what == "theme":
        from .checks.theme import check_theme
        from .kit.theme import Theme

        theme = Theme.from_dict(pr.theme)
        found = [str(f) for f in check_theme(theme, pr.root)]
        notes = [f"note: roles from the kit's neutral default: {', '.join(theme.defaulted)}"] if theme.defaulted else []
        summary = "theme check: ok" if not found else f"theme check: {len(found)} failure(s)"
        return CheckResult(not found, "theme", summary, found, notes)
    if not episode:
        raise ValueError(f"check {what} needs an episode")
    ep = pr.episode(episode)
    if what == "layout":
        from .checks.layout import check_layout, load_layout

        found = [str(f) for f in check_layout(load_layout(pr.build_dir / ep.stem / "layout.json"))]
        return CheckResult(not found, "layout", _layout_summary(found), found)
    from .checks.audio import check_audio

    srt = pr.out_dir / f"{ep.stem}.srt"
    video = pr.out_dir / f"{ep.stem}.mp4"
    notes = []
    if pr.post.music is not None:
        from .runner import built_path

        video = built_path(pr, ep, "final")
        notes.append(f"note: checking the narration-only render {video}; out/{ep.stem}.mp4 has the music mixed in")
    rep = check_audio(video, srt)
    summary, rows = _audio_lines(rep)
    return CheckResult(rep.ok, "audio", summary, rows, notes)


@_tool
def contact_sheet(project: str, episode: str, every: float = 5.0) -> SheetsResult:
    """Write contact sheets (3 by 3 grids of frames) of an episode, from out/ if rendered, else the last draft.

    Args:
        project: The project folder, or any folder inside it.
        episode: The episode as listed in series.json: ep01, 1, or its file stem.
        every: Seconds between sampled frames; above 0.
    """
    from .checks.sheets import contact_sheets
    from .project import ProjectError
    from .runner import built_path

    if not every > 0:
        raise ValueError("every must be greater than 0")
    pr = _open(project)
    ep = pr.episode(episode)
    video = pr.out_dir / f"{ep.stem}.mp4"
    if not video.is_file():
        video = built_path(pr, ep, "draft")
    if not video.is_file():
        raise ProjectError(f"no video of {ep.stem} yet: draft it first (manimvox draft {ep.stem}, tool: draft)")
    sheets = contact_sheets(video, pr.sheets_dir / ep.stem, every=every)
    return SheetsResult(True, str(video), [str(s) for s in sheets])


@dataclass(frozen=True)
class RenderResult:
    ok: bool
    video: str
    subtitles: str
    voice: str
    audio: str  # the audio check's report: "audio check: ok  (N lines, all audible)" or FAILED with each silent line
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EngineInfo:
    name: str
    ready: bool
    detail: str
    licence: str
    online: str  # the service that receives the narration text; "" when nothing leaves the machine
    noncommercial: bool


@dataclass(frozen=True)
class VoiceInfo:
    voice: str
    description: str


@dataclass(frozen=True)
class VoicesResult:
    ok: bool
    engines: list[EngineInfo] = field(default_factory=list)
    voices: list[VoiceInfo] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PrepareResult:
    ok: bool
    voice: str


def _consent(allow: bool) -> Callable[[str], bool]:
    """A confirm that never prompts: yes only when the caller allowed it, or MANIMVOX_ASSUME_YES=1."""
    return lambda _prompt: allow or os.environ.get("MANIMVOX_ASSUME_YES") == "1"


def _render(project: str, episode: str, voice: str | None, confirm: Callable[[str], bool],
            say: Say | None) -> RenderResult:
    import shutil

    from . import runner
    from .checks.audio import check_audio
    from .voice import get_engine, resolve_voice

    notes: list[str] = []

    def note(line: str) -> None:
        notes.append(line)
        if say:
            say(line)

    pr = _open(project)
    ep = pr.episode(episode)
    spec = resolve_voice(voice, pr.voice, os.environ)
    eng = get_engine(spec.engine)
    eng.prepare(spec.voice, confirm, pr.root)
    if eng.online:
        note(f"note: narration text is sent to {eng.online} ({spec})")
    if eng.noncommercial:
        note(f"note: {spec.engine} is for non-commercial use only: {eng.licence}")
    out = pr.out_dir / f"{ep.stem}.mp4"
    srt = pr.out_dir / f"{ep.stem}.srt"
    if pr.post.music is not None and not (pr.root / pr.post.music).is_file():
        from .post.options import PostError

        raise PostError(f"post.music: no file at {pr.root / pr.post.music}")  # before a long render, not after
    out.unlink(missing_ok=True)
    srt.unlink(missing_ok=True)
    built = runner.render_episode(pr, ep, "final", spec)
    pr.out_dir.mkdir(parents=True, exist_ok=True)
    rep = check_audio(built, srt)  # the narration alone: a music bed would hide a silent line
    if pr.post.active and rep.ok:
        from .checks.audio import read_cues
        from .kit.theme import Theme
        from .post.finish import finish

        steps = [n for n, on in (("music", pr.post.music is not None), ("captions", pr.post.captions == "burn"),
                                 ("end card", bool(pr.post.end_card))) if on]
        note(f"post: finishing ({', '.join(steps)}) ...")  # the re-encode takes minutes on a long episode
        for line in finish(built, out, read_cues(srt), pr.post, Theme.from_dict(pr.theme), pr.root):
            note(f"post: {line}")
    else:
        shutil.copy2(built, out)
        if pr.post.active:
            note("post: skipped until the audio check passes")
    return RenderResult(rep.ok, str(out), str(srt), str(spec), str(rep), notes)


@_tool
def render(project: str, episode: str, voice: str | None = None, allow_download: bool = False) -> RenderResult:
    """Render the final 1080p episode with the voice, apply series.json post, and run the audio check; takes minutes.

    Args:
        project: The project folder, or any folder inside it.
        episode: The episode as listed in series.json: ep01, 1, or its file stem.
        voice: engine:voice for this render; by default series.json's voice, then MANIMVOX_VOICE, then kokoro:af_heart.
        allow_download: True only when the user has agreed to download the voice model if it is missing.
    """
    return _render(project, episode, voice, _consent(allow_download), None)


@_tool
def voices(engine: str | None = None) -> VoicesResult:
    """List the voice engines (ready or not, licence, whether narration text leaves the machine), or one engine's voices.

    Args:
        engine: An engine name such as kokoro, to list its voices; leave it out to list the engines.
    """
    from .voice import engine_names, get_engine

    if engine:
        eng = get_engine(engine.strip().lower())
        rows = [VoiceInfo(v, d) for v, d in eng.describe_voices()]
        notes = [] if rows else [f"{eng.name}: no voices listed ({eng.status().detail})"]
        return VoicesResult(True, voices=rows, notes=notes)
    infos = []
    for name in engine_names():
        e = get_engine(name)
        st = e.status()
        infos.append(EngineInfo(name, st.ready, st.detail, e.licence, e.online, e.noncommercial))
    return VoicesResult(True, engines=infos)


def _prepare_voice(voice: str, project: str | None, confirm: Callable[[str], bool]) -> PrepareResult:
    from .project import ProjectError, find_project
    from .voice import get_engine, parse_voice

    if ":" in voice:
        spec = parse_voice(voice)
        eng, name = get_engine(spec.engine), spec.voice
    else:
        eng = get_engine(voice.strip().lower())
        name = eng.default_voice
    start = Path(project).expanduser() if project else Path.cwd()
    try:
        root = find_project(start)
    except ProjectError:
        root = start.resolve()
    eng.prepare(name, confirm, root)
    return PrepareResult(True, f"{eng.name}:{name}")


@_tool
def prepare_voice(voice: str, project: str | None = None, allow_download: bool = False) -> PrepareResult:
    """Get a voice engine, or one of its voices, ready to render: checks the voice and fetches a missing model.

    Args:
        voice: An engine (kokoro) or engine:voice (kokoro:af_heart).
        project: The project folder, where a cloning voice's reference recording is found.
        allow_download: True only when the user has agreed to download the model.
    """
    return _prepare_voice(voice, project, _consent(allow_download))
