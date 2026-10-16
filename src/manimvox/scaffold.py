"""`manimvox new`: a project folder ready for facts, an outline and episodes."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from . import __version__
from .project import SERIES_FILE, ProjectError
from .voice import DEFAULT_VOICE, parse_voice


def _template(name: str) -> str:
    return resources.files("manimvox.templates").joinpath(name).read_text(encoding="utf-8")


def _write_gitignore(path: Path) -> None:
    """Create .gitignore from the template, or append the template lines an existing one lacks."""
    if not path.exists():
        path.write_text(_template("gitignore"), encoding="utf-8")
        return
    existing = path.read_text(encoding="utf-8")
    present = {line.strip() for line in existing.splitlines()}
    wanted = [line.strip() for line in _template("gitignore").splitlines() if line.strip()]
    missing = [entry for entry in wanted if entry not in present]
    if not missing:
        return
    lead = "" if not existing or existing.endswith("\n") else "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(lead + "".join(entry + "\n" for entry in missing))


def new_project(directory: Path, series: str, tagline: str = "", voice: str = DEFAULT_VOICE) -> Path:
    d = Path(directory).expanduser().resolve()
    if (d / SERIES_FILE).exists():
        raise ProjectError(f"{d} already holds a project; edit its series.json instead")
    if not series.strip():
        raise ProjectError('series name is empty: pass --series "Name, Explained"')
    parse_voice(voice)  # fail before writing anything
    for sub in ("episodes", "out", "research"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    conf = {
        "manimvox": __version__,
        "series": series,
        "tagline": tagline,
        "voice": voice,
        "speed": 1.0,
        "pron": [],
        "theme": {"source": "kit neutral default; replace with the subject's own theme (see manimvox-creative)"},
        "episodes": [],
    }
    (d / SERIES_FILE).write_text(json.dumps(conf, indent=2) + "\n", encoding="utf-8")
    for name in ("FACTS.md", "SERIES.md"):
        if not (d / name).exists():
            (d / name).write_text(_template(name).replace("{{SERIES}}", series), encoding="utf-8")
    _write_gitignore(d / ".gitignore")
    return d
