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


def new_project(directory: Path, series: str, tagline: str = "", voice: str = DEFAULT_VOICE) -> Path:
    d = Path(directory).expanduser().resolve()
    if (d / SERIES_FILE).exists():
        raise ProjectError(f"{d} already holds a project; edit its series.json instead")
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
    (d / ".gitignore").write_text(_template("gitignore"), encoding="utf-8")
    return d
