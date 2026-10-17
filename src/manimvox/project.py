"""A manimvox project: a folder with series.json, episodes/, out/."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

from .post.options import PostOptions, parse_post

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
    level: str = ""
    blurb: str = ""


@dataclass
class Project:
    root: Path
    series: str
    tagline: str = ""
    voice: str | None = None
    speed: float = 1.0
    pron: list[tuple[str, str]] = field(default_factory=list)
    theme: dict = field(default_factory=dict)
    post: PostOptions = field(default_factory=PostOptions)
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
    if not f.is_file():
        raise ProjectError(f"no series.json in {root}; run `manimvox new <dir>` first")
    try:
        text = f.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ProjectError(f"{f} is not UTF-8 text: {e}") from e
    except OSError as e:
        raise ProjectError(f"{f} cannot be read: {e}") from e
    try:
        data = json.loads(text)
    except ValueError as e:
        # JSONDecodeError, plus the int-digit limit that json raises as a bare ValueError
        raise ProjectError(f"{f} is not valid JSON: {e}") from e
    if not isinstance(data, dict):
        raise ProjectError(f"{f}: top level must be a JSON object")
    if not isinstance(data.get("series"), str) or not data["series"].strip():
        raise ProjectError(f"{f}: 'series' (the name shown on every title card) is required")
    raw_speed = data.get("speed", 1.0)
    if isinstance(raw_speed, bool) or not isinstance(raw_speed, (int, float)):
        raise ProjectError(f"{f}: 'speed' must be a number, got {raw_speed!r}")
    try:
        speed = float(raw_speed)
    except OverflowError as e:
        raise ProjectError(f"{f}: 'speed' is too large to be a number") from e
    if not math.isfinite(speed):
        raise ProjectError(f"{f}: 'speed' must be a number, got {raw_speed!r}")
    if speed <= 0:
        raise ProjectError(f"{f}: 'speed' must be greater than 0, got {raw_speed!r}")
    voice = data.get("voice")
    if voice is not None and not isinstance(voice, str):
        raise ProjectError(f"{f}: 'voice' must be a string like 'kokoro:af_heart', got {voice!r}")
    theme = data.get("theme", {})
    if not isinstance(theme, dict):
        raise ProjectError(f"{f}: 'theme' must be an object, got {theme!r}")
    try:
        post = parse_post(data.get("post"))
    except ValueError as e:
        raise ProjectError(f"{f}: {e}") from e
    return Project(
        root=root,
        series=data["series"],
        tagline=data.get("tagline", ""),
        voice=voice,
        speed=float(speed),
        pron=_pron(f, data.get("pron", [])),
        theme=dict(theme),
        post=post,
        episodes=_episodes(f, root, data.get("episodes", [])),
    )


def _episodes(f: Path, root: Path, raw: object) -> list[EpisodeRef]:
    if not isinstance(raw, list):
        raise ProjectError(f"{f}: 'episodes' must be a list, got {raw!r}")
    refs = []
    for i, e in enumerate(raw, start=1):
        if not isinstance(e, dict):
            raise ProjectError(f"{f}: episode {i} must be an object, got {e!r}")
        for key in ("n", "stem", "cls"):
            if key not in e:
                raise ProjectError(f"{f}: episode {i} is missing '{key}'")
        n = _int(f, f"episode {i} 'n'", e["n"])
        for key in ("stem", "cls"):
            if not isinstance(e[key], str):
                raise ProjectError(f"{f}: episode {i} '{key}' must be a string, got {e[key]!r}")
        stem = e["stem"]
        if not stem.startswith("ep"):
            raise ProjectError(f"{f}: episode stem '{stem}' must start with 'ep' (e.g. ep01_intro)")
        refs.append(EpisodeRef(n, stem, e["cls"], str(e.get("title", "")), root / "episodes" / f"{stem}.py",
                        str(e.get("level", "")), str(e.get("blurb", ""))))
    return refs


def _pron(f: Path, raw: object) -> list[tuple[str, str]]:
    if not isinstance(raw, list):
        raise ProjectError(f"{f}: 'pron' must be a list of [pattern, spoken] pairs, got {raw!r}")
    pairs = []
    for i, entry in enumerate(raw, start=1):
        if not (isinstance(entry, list) and len(entry) == 2 and all(isinstance(x, str) for x in entry)):
            raise ProjectError(f"{f}: pron entry {i} must be a 2-item list of strings, got {entry!r}")
        pairs.append((entry[0], entry[1]))
    return pairs


def _int(f: Path, where: str, value: object) -> int:
    if not isinstance(value, bool) and isinstance(value, (int, str)):
        try:
            return int(value)
        except ValueError:
            pass
    raise ProjectError(f"{f}: {where} must be an integer, got {value!r}")


def find_project(start: Path) -> Path:
    start = Path(start).resolve()
    for d in (start, *start.parents):
        if (d / SERIES_FILE).is_file():
            return d
    raise ProjectError(f"no series.json in {start} or any parent; run `manimvox new <dir>` first")
