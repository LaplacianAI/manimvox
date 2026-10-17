"""Typed functions that mirror the manimvox command, for agents with no shell.

Every tool takes the project folder (or any folder inside it) as `project`, where the command uses the current
folder. It returns a dataclass of plain values, so `dataclasses.asdict` gives JSON. A failed check is a result
with `ok=False` and its findings, as the command exits 1. A tool that cannot do what was asked raises ToolError,
whose message says what to do first. Nothing here prompts: a download goes ahead only with allow_download=True.
"""

from __future__ import annotations

import functools
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
