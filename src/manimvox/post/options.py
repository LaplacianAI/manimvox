"""series.json → "post": the music bed, captions and end card that `render` adds after Manim."""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

KEYS = ("music", "music_db", "duck_db", "captions", "end_card", "card_seconds")


class PostError(Exception):
    """A post step could not run: a missing or unreadable file, or nothing to work on."""


@dataclass(frozen=True)
class PostOptions:
    music: Path | None = None  # relative to the project root, as written in series.json
    music_db: float = -16.0  # the music's level where nobody speaks
    duck_db: float = -12.0  # a further cut while the narration speaks
    captions: str = "srt"  # "srt": ship out/<stem>.srt; "burn": also draw them into the picture
    end_card: tuple[str, ...] = ()
    card_seconds: float = 3.0

    @property
    def active(self) -> bool:
        return self.music is not None or self.captions == "burn" or bool(self.end_card)


def _number(raw: dict, key: str, default: float, lo: float, hi: float) -> float:
    v = raw.get(key, default)
    try:
        ok = not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v) and lo <= v <= hi
    except OverflowError:  # an integer too large for a float is out of range, not a crash
        ok = False
    if not ok:
        raise ValueError(f"post.{key} must be a number from {lo:g} to {hi:g}, got {v!r}")
    return float(v)


def parse_post(raw: object) -> PostOptions:
    """series.json's "post" object, checked. Raises ValueError naming the bad key."""
    if raw is None:
        return PostOptions()
    if not isinstance(raw, dict):
        raise ValueError(f"'post' must be an object, got {raw!r}")  # noqa: TRY004 - callers catch ValueError
    unknown = sorted(set(raw) - set(KEYS))
    if unknown:
        raise ValueError(f"'post' has unknown key {unknown[0]!r} (known: {', '.join(KEYS)})")
    music = raw.get("music")
    if music is not None and (not isinstance(music, str) or not music.strip()):
        raise ValueError("post.music must be the path of an audio file, relative to the project")
    captions = raw.get("captions", "srt")
    if captions not in ("srt", "burn"):
        raise ValueError(f'post.captions must be "srt" or "burn", got {captions!r}')
    card = raw.get("end_card", [])
    if isinstance(card, str):
        card = [card]
    if not (isinstance(card, list) and len(card) <= 4
            and all(isinstance(s, str) and s.strip() and len(s) <= 80 for s in card)):
        raise ValueError("post.end_card must be a list of up to 4 lines of text, each at most 80 characters")
    return PostOptions(
        music=Path(music) if music else None,
        music_db=_number(raw, "music_db", -16.0, -60, 0),
        duck_db=_number(raw, "duck_db", -12.0, -60, 0),
        captions=captions,
        end_card=tuple(card),
        card_seconds=_number(raw, "card_seconds", 3.0, 1, 10),
    )
