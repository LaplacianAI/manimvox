"""A manimvox project: a folder with series.json, episodes/, out/."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

SERIES_FILE = "series.json"


class ProjectError(Exception):
    """series.json is missing, malformed, or does not name what was asked for."""


@dataclass(frozen=True)
class EpisodeRef:
    n: int
    stem: str
    cls: str
    title: str
    path: Path


@dataclass
class Project:
    root: Path
    series: str
    tagline: str = ""
    voice: str | None = None
    speed: float = 1.0
    pron: list[tuple[str, str]] = field(default_factory=list)
    theme: dict = field(default_factory=dict)
    episodes: list[EpisodeRef] = field(default_factory=list)

    @property
    def out_dir(self) -> Path:
        return self.root / "out"

    @property
    def build_dir(self) -> Path:
        return self.root / "build"

    @property
    def cache_dir(self) -> Path:
        return self.root / ".manimvox" / "tts"

    @property
    def sheets_dir(self) -> Path:
        return self.root / "sheets"

    def episode(self, ref: str) -> EpisodeRef:
        ref = ref.strip()
        stem = Path(ref).stem if ref.endswith(".py") else ref
        m = re.fullmatch(r"(?:ep)?0*(\d+)", stem)
        for e in self.episodes:
            if e.stem == stem or (m and e.n == int(m.group(1))):
                return e
        have = ", ".join(e.stem for e in self.episodes) or "none yet"
        raise ProjectError(f"no episode '{ref}' in series.json (available: {have})")


def load_project(root: Path) -> Project:
    root = Path(root).resolve()
    f = root / SERIES_FILE
    if not f.exists():
        raise ProjectError(f"no series.json in {root}; run `manimvox new <dir>` first")
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ProjectError(f"{f} is not valid JSON: {e}") from e
    if not isinstance(data.get("series"), str) or not data["series"].strip():
        raise ProjectError(f"{f}: 'series' (the name shown on every title card) is required")
    episodes = []
    for e in data.get("episodes", []):
        stem = str(e.get("stem", ""))
        if not stem.startswith("ep"):
            raise ProjectError(f"{f}: episode stem '{stem}' must start with 'ep' (e.g. ep01_intro)")
        episodes.append(
            EpisodeRef(int(e["n"]), stem, str(e["cls"]), str(e.get("title", "")), root / "episodes" / f"{stem}.py")
        )
    return Project(
        root=root,
        series=data["series"],
        tagline=data.get("tagline", ""),
        voice=data.get("voice"),
        speed=float(data.get("speed", 1.0)),
        pron=[(str(a), str(b)) for a, b in data.get("pron", [])],
        theme=dict(data.get("theme", {})),
        episodes=episodes,
    )


def find_project(start: Path) -> Path:
    start = Path(start).resolve()
    for d in (start, *start.parents):
        if (d / SERIES_FILE).exists():
            return d
    raise ProjectError(f"no series.json in {start} or any parent; run `manimvox new <dir>` first")
