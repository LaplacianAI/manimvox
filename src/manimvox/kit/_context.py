"""What the running episode needs to know: its project, theme, voice and episode stem.

Read once at import. The CLI sets the environment; run outside the CLI, the kit finds
series.json from the working directory, or falls back to the neutral theme."""
from __future__ import annotations

import os
from pathlib import Path

from ..project import Project, ProjectError, find_project, load_project
from ..voice import DEFAULT_VOICE, VoiceSpec, parse_voice
from .theme import Theme


def _load_project() -> Project | None:
    root = os.environ.get("MANIMVOX_PROJECT")
    if root:
        return load_project(Path(root))  # a wrong path set by the caller must fail loudly
    try:
        return load_project(find_project(Path.cwd()))
    except ProjectError:
        return None


PROJECT: Project | None = _load_project()
THEME: Theme = Theme.from_dict(PROJECT.theme if PROJECT else {})
NOTTS: bool = os.environ.get("MANIMVOX_NOTTS") == "1"
VOICE: VoiceSpec = parse_voice(os.environ.get("MANIMVOX_VOICE_RESOLVED")
                               or (PROJECT.voice if PROJECT and PROJECT.voice else DEFAULT_VOICE))
STEM: str | None = os.environ.get("MANIMVOX_STEM")
