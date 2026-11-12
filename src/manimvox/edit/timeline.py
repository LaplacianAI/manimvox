"""The edit timeline: what a finished video is made of, as plain frozen dataclasses.

One model, two front ends. An edit is `edits/<name>.json`, or `edits/<name>.py` that sets `timeline` to a
`Timeline` built from the classes in `manimvox.edit`. `Timeline.save()` writes the JSON a Python edit describes.
`parse` checks the shape and raises ValueError naming the field; `check.check_edit` checks it against the files.

Times on the output are seconds. A clip's `start` and `end` are seconds of its own file. Boxes and positions are
pixels of the output frame, counted from the top left.

Any layer can be code. A function hook is written `"path.py:name"` in JSON (the path relative to the project), or
is the function itself in Python: a `Frames` segment's source, a `Draw` overlay, a `Scene` overlay (a Manim scene
class) and the `effects` of a segment.
"""
from __future__ import annotations

import json
import math
import re
from collections.abc import Callable
from dataclasses import MISSING, dataclass, field, fields
from pathlib import Path
from typing import Any

VERSION = 1
FITS = ("contain", "cover", "crop")
MOVES = ("push", "pull", "left", "right")
TRANSITIONS = ("cut", "fade", "dip")
TEXT_KINDS = ("lower-third", "title", "label")
CAPTIONS = ("srt", "burn", "none")
SPEED = (0.25, 4.0)
DB = (-60.0, 12.0)
MAX_SIDE = 4096
REF = re.compile(r"^(?P<file>[^:]+\.py):(?P<name>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)$")

Ref = str | Callable[..., Any]  # "path.py:name", or the object itself


# ---------------------------------------------------------------- the main track

@dataclass(frozen=True)
class Transition:
    """How a segment begins after the one before it. "fade" crossfades picture and sound; "dip" goes through
    the theme's background. Both overlap the two segments by `seconds`, so the film is that much shorter."""
    kind: str = "cut"
    seconds: float = 0.5


@dataclass(frozen=True)
class Grade:
    """A colour grade for a segment's picture, applied before its effects; every control is neutral at its
    default. `exposure` is in stops; `contrast` and `saturation` multiply (1: unchanged); `temperature` warms (+)
    or cools (-) and `tint` turns magenta (+) or green (-), from -1 to 1; `lift`, `gamma` and `gain` move the
    shadows, mid-tones and highlights, each one number or [r, g, b]; `lut` is a 3D `.cube` file, applied last."""
    exposure: float = 0.0
    contrast: float = 1.0
    saturation: float = 1.0
    temperature: float = 0.0
    tint: float = 0.0
    lift: float | tuple[float, float, float] = 0.0
    gamma: float | tuple[float, float, float] = 1.0
    gain: float | tuple[float, float, float] = 1.0
    lut: str | None = None


GRADE_RANGES = {"exposure": (-4.0, 4.0), "contrast": (0.0, 3.0), "saturation": (0.0, 3.0),
                "temperature": (-1.0, 1.0), "tint": (-1.0, 1.0), "lift": (-0.5, 0.5), "gamma": (0.2, 5.0),
                "gain": (0.0, 4.0)}


@dataclass(frozen=True)
class Clip:
    """A piece of footage (`path`), or a rendered episode of this project (`episode`), from `start` to `end`
    seconds of the file (`end=None`: to its end).

    With a transcript of the file (`manimvox edit probe FILE --transcribe`): `from_words` and `to_words` set the
    start and end by what is said (searched between `start` and `end`, never cutting inside a word);
    `cut_silences` removes pauses longer than that many seconds; `cut_fillers` removes "um", "uh" and the like;
    `captions` captions what the speaker says. A clip with cuts plays as several pieces, joined by cuts."""
    path: str | None = None
    start: float = 0.0
    end: float | None = None
    episode: str | None = None
    speed: float = 1.0  # 0.25 to 4; the sound keeps its pitch
    volume: float = 0.0  # dB on the clip's own sound
    mute: bool = False
    fit: str = "contain"  # contain: letterbox; cover: fill and trim the edges; crop: show `crop`, scaled to fill
    crop: tuple[float, float, float, float] | None = None  # x, y, w, h in the source's pixels
    effects: tuple[Ref, ...] = ()  # fn(rgb, t) -> rgb, in order; t is seconds into the segment
    transition: Transition = field(default_factory=Transition)
    grade: Grade | None = None
    from_words: str | None = None
    to_words: str | None = None
    cut_silences: float | None = None
    cut_fillers: bool = False
    captions: bool = False

    @property
    def needs_transcript(self) -> bool:
        return bool(self.from_words or self.to_words or self.cut_silences or self.cut_fillers or self.captions)


@dataclass(frozen=True)
class Image:
    """A still for `seconds`, optionally moving slowly: push in, pull out, or pan left or right."""
    path: str
    seconds: float = 4.0
    move: str | None = None
    fit: str = "contain"
    effects: tuple[Ref, ...] = ()
    transition: Transition = field(default_factory=Transition)
    grade: Grade | None = None


@dataclass(frozen=True)
class Title:
    """The theme's title card: `text`, with up to 4 `lines` under it, typed in, then held."""
    text: str
    lines: tuple[str, ...] = ()
    seconds: float = 3.0
    transition: Transition = field(default_factory=Transition)


@dataclass(frozen=True)
class Frames:
    """Frames made by code: `source` is a frame source (a MoviePy clip, `frames(fn, seconds)` or
    `from_moviepy(clip)`), or a function of no arguments that returns one. `seconds` defaults to its length."""
    source: Ref
    seconds: float | None = None
    fit: str = "contain"
    effects: tuple[Ref, ...] = ()
    transition: Transition = field(default_factory=Transition)
    grade: Grade | None = None


Segment = Clip | Image | Title | Frames


# ---------------------------------------------------------------- over the main track

@dataclass(frozen=True)
class Picture:
    """An image over the picture from `at` to `until` seconds of the output: a logo, or a picture beside the
    speaker. `box` is x, y and width in output pixels; the height follows the image."""
    path: str
    at: float
    until: float
    box: tuple[float, float, float]
    fade: float = 0.3


@dataclass(frozen=True)
class Text:
    """Words over the picture in the theme's fonts: a lower third (a name, and a role in `sub`), a centred
    title, or a label at `pos` (x, y in output pixels)."""
    text: str
    at: float
    until: float
    kind: str = "lower-third"
    sub: str = ""
    pos: tuple[float, float] | None = None
    fade: float = 0.3


@dataclass(frozen=True)
class Inset:
    """A second video over the picture (picture-in-picture), from `start` seconds of its file, shown from `at`
    to `until` seconds of the output in `box` (x, y, width). Silent unless `volume` is given."""
    path: str
    at: float
    until: float
    box: tuple[float, float, float]
    start: float = 0.0
    volume: float | None = None
    fade: float = 0.3


@dataclass(frozen=True)
class Draw:
    """Graphics drawn by code from `at` to `until`: `fn(t)` returns the layer at t seconds into it, as a PIL
    image or an (h, w, 3|4) uint8 array (RGBA keeps transparency), over the whole frame or scaled into `box`."""
    fn: Ref
    at: float
    until: float
    box: tuple[float, float, float] | None = None
    fade: float = 0.0


@dataclass(frozen=True)
class Scene:
    """A Manim scene (`scene`: the class, or "path.py:Class") rendered with a transparent background and laid
    over the picture from `at`, for the scene's own length unless `until` cuts it short."""
    scene: Ref
    at: float
    until: float | None = None
    box: tuple[float, float, float] | None = None
    fade: float = 0.0


Overlay = Picture | Text | Inset | Draw | Scene


# ---------------------------------------------------------------- sound

@dataclass(frozen=True)
class Say:
    """A narration line in the project's voice, starting `at` seconds of the output."""
    text: str
    at: float


@dataclass(frozen=True)
class Music:
    """A music bed from `at` to `until` (default: the whole film), looped, faded in and out, and lowered by
    the timeline's `duck_db` while anyone speaks."""
    path: str
    volume: float = -16.0
    at: float = 0.0
    until: float | None = None


@dataclass(frozen=True)
class Sound:
    """A sound file (an effect, a recorded voice-over) from `start` to `end` seconds of the file, placed `at`
    seconds of the output."""
    path: str
    at: float
    volume: float = 0.0
    start: float = 0.0
    end: float | None = None


Audio = Say | Music | Sound


@dataclass(frozen=True)
class Timeline:
    segments: tuple[Segment, ...]
    overlays: tuple[Overlay, ...] = ()
    audio: tuple[Audio, ...] = ()
    size: tuple[int, int] = (1920, 1080)
    fps: float = 30.0
    captions: str = "srt"  # srt: out/<name>.srt; burn: also drawn into the picture; none
    duck_db: float = -12.0  # how far the footage's sound and the music drop under narration
    spellings: tuple[tuple[str, str], ...] = ()  # (heard, written) fixes for speaker captions: names, jargon

    def to_dict(self, root: Path | None = None) -> dict:
        """The edit as JSON values. Function hooks are written "path.py:name" relative to `root` (the project);
        a function with no file there (a lambda, or one typed at a prompt) cannot be written."""
        return to_dict(self, root)

    def save(self, path) -> Path:
        """Write `edits/<name>.json`; `path` is that file, inside the project's edits/ folder."""
        p = Path(path)
        data = to_dict(self, p.resolve().parent.parent)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return p


# ---------------------------------------------------------------- checks of one value

def _num(where: str, v, lo: float = -math.inf, hi: float = math.inf, *, above: float | None = None) -> float:
    ok = not isinstance(v, bool) and isinstance(v, (int, float))
    try:
        ok = ok and math.isfinite(v) and lo <= v <= hi and (above is None or v > above)
    except OverflowError:
        ok = False
    if not ok:
        if above is not None:
            rng = f" above {above:g}" + (f" and at most {hi:g}" if math.isfinite(hi) else "")
        elif math.isfinite(lo) and math.isfinite(hi):
            rng = f" from {lo:g} to {hi:g}"
        elif math.isfinite(lo):
            rng = f" of at least {lo:g}"
        else:
            rng = ""
        raise ValueError(f"{where} must be a number{rng}, got {v!r}")
    return float(v)


def _text(where: str, v, longest: int = 300) -> str:
    if not (isinstance(v, str) and v.strip() and len(v) <= longest):
        raise ValueError(f"{where} must be text of 1 to {longest} characters, got {v!r}")
    return v


def _path(where: str, v) -> str:
    if not (isinstance(v, str) and v.strip()):
        raise ValueError(f"{where} must be a file path, relative to the project or absolute, got {v!r}")
    return v


def _choice(where: str, v, options) -> str:
    if v not in options:
        raise ValueError(f"{where} must be one of {', '.join(map(str, options))}, got {v!r}")
    return v


def _bool(where: str, v) -> bool:
    if not isinstance(v, bool):
        raise ValueError(f"{where} must be true or false, got {v!r}")  # noqa: TRY004 - edit errors are ValueError
    return v


def _tuple(where: str, v, n: int, what: str) -> tuple[float, ...]:
    if not (isinstance(v, (list, tuple)) and len(v) == n):
        raise ValueError(f"{where} must be {what}, got {v!r}")
    return tuple(_num(f"{where}[{i}]", x) for i, x in enumerate(v))


def _box(where: str, v) -> tuple[float, float, float]:
    box = _tuple(where, v, 3, "[x, y, width] in output pixels")
    if box[2] <= 0:
        raise ValueError(f"{where} width must be above 0, got {box[2]:g}")
    return box


def _ref(where: str, v) -> Ref:
    if callable(v):
        return v
    if isinstance(v, str) and REF.match(v.strip()):
        return v.strip()
    raise ValueError(f'{where} must be "path.py:name" (a function or class in a file of the project), '
                     f"or in Python the function itself, got {v!r}")


def _refs(where: str, v) -> tuple[Ref, ...]:
    if v is None:
        return ()
    if isinstance(v, str) or callable(v):
        v = [v]
    if not isinstance(v, (list, tuple)):
        raise ValueError(f"{where} must be a list of functions, got {v!r}")  # noqa: TRY004 - edit errors are ValueError
    return tuple(_ref(f"{where}[{i}]", x) for i, x in enumerate(v))


def _words(where: str, v) -> str | None:
    if v is None:
        return None
    if not (isinstance(v, str) and re.search(r"\w", v) and len(v) <= 200):
        raise ValueError(f"{where} must be words said in the clip, up to 200 characters, got {v!r}")
    return v


def _transition(where: str, v) -> Transition:
    if v is None:
        return Transition()
    if isinstance(v, Transition):
        v = {"kind": v.kind, "seconds": v.seconds}
    if isinstance(v, str):
        v = {"kind": v}
    if not isinstance(v, dict):
        raise ValueError(f'{where} must be "cut", "fade", "dip" or {{"kind": ..., "seconds": ...}}, got {v!r}')  # noqa: TRY004 - edit errors are ValueError
    _unknown(where, v, ("kind", "seconds"))
    return Transition(_choice(f"{where}.kind", v.get("kind", "cut"), TRANSITIONS),
                      _num(f"{where}.seconds", v.get("seconds", 0.5), hi=10, above=0))


def _grade(where: str, v) -> Grade | None:
    if v is None:
        return None
    if isinstance(v, Grade):
        v = {f.name: getattr(v, f.name) for f in fields(Grade)}
    if not isinstance(v, dict):
        raise ValueError(f'{where} must be an object such as {{"exposure": 0.3, "saturation": 1.1}}, got {v!r}')  # noqa: TRY004 - edit errors are ValueError
    names = [f.name for f in fields(Grade)]
    _unknown(where, v, names)
    out: dict = {}
    for name, (lo, hi) in GRADE_RANGES.items():
        if name not in v:
            continue
        x = v[name]
        if name in ("lift", "gamma", "gain") and isinstance(x, (list, tuple)):
            if len(x) != 3:
                raise ValueError(f"{where}.{name} must be a number or [r, g, b], got {x!r}")
            out[name] = tuple(_num(f"{where}.{name}[{i}]", c, lo, hi) for i, c in enumerate(x))
        else:
            out[name] = _num(f"{where}.{name}", x, lo, hi)
    if v.get("lut") is not None:
        out["lut"] = _path(f"{where}.lut", v["lut"])
    return Grade(**out)


def _unknown(where: str, raw: dict, known) -> None:
    extra = sorted(set(raw) - set(known))
    if extra:
        raise ValueError(f"{where} has unknown key {extra[0]!r} (known: {', '.join(known)})")


def _lead(where: str, raw, table) -> str:
    if not isinstance(raw, dict):
        raise ValueError(f"{where} must be an object, got {raw!r}")  # noqa: TRY004 - edit errors are ValueError
    leads = [k for k in table if k in raw]
    if len(leads) != 1:
        raise ValueError(f"{where} must have exactly one of {', '.join(map(repr, table))}"
                         + (f", got {', '.join(map(repr, leads))}" if leads else ""))
    return leads[0]


def _span(where: str, raw) -> tuple[float, float]:
    at = _num(f"{where}.at", raw.get("at"), 0)
    return at, _num(f"{where}.until", raw.get("until"), above=at)


# ---------------------------------------------------------------- parsing an item
# Each item is an object led by one key that says what it is and holds its main value: {"clip": "a.mp4", ...}.

SEGMENT_LEADS = ("clip", "episode", "image", "title", "frames")
OVERLAY_LEADS = ("image", "text", "clip", "draw", "scene")
AUDIO_LEADS = ("say", "music", "sound")


def _segment(where: str, raw) -> Segment:
    lead = _lead(where, raw, SEGMENT_LEADS)
    tr = _transition(f"{where}.transition", raw.get("transition"))
    effects = _refs(f"{where}.effects", raw.get("effects"))
    grade = _grade(f"{where}.grade", raw.get("grade")) if lead != "title" else None
    if lead in ("clip", "episode"):
        _unknown(where, raw, (lead, "start", "end", "speed", "volume", "mute", "fit", "crop", "effects",
                              "transition", "grade", "from_words", "to_words", "cut_silences", "cut_fillers", "captions"))
        start = _num(f"{where}.start", raw.get("start", 0.0), 0)
        end = raw.get("end")
        end = None if end is None else _num(f"{where}.end", end, above=start)
        fit = _choice(f"{where}.fit", raw.get("fit", "contain"), FITS)
        crop = raw.get("crop")
        crop = None if crop is None else _tuple(f"{where}.crop", crop, 4, "[x, y, w, h] in the source's pixels")
        if fit == "crop" and crop is None:
            raise ValueError(f'{where}.fit is "crop", so it needs "crop": [x, y, w, h]')
        if crop is not None and not (crop[0] >= 0 and crop[1] >= 0 and crop[2] > 0 and crop[3] > 0):
            raise ValueError(f"{where}.crop needs x and y of at least 0 and w and h above 0, got {list(crop)}")
        return Clip(path=_path(f"{where}.clip", raw["clip"]) if lead == "clip" else None,
                    episode=_text(f"{where}.episode", raw["episode"], 80) if lead == "episode" else None,
                    start=start, end=end, speed=_num(f"{where}.speed", raw.get("speed", 1.0), *SPEED),
                    volume=_num(f"{where}.volume", raw.get("volume", 0.0), *DB),
                    mute=_bool(f"{where}.mute", raw.get("mute", False)), fit=fit, crop=crop, effects=effects,
                    transition=tr, grade=grade,
                    from_words=_words(f"{where}.from_words", raw.get("from_words")),
                    to_words=_words(f"{where}.to_words", raw.get("to_words")),
                    cut_silences=None if raw.get("cut_silences") is None else _num(
                        f"{where}.cut_silences", raw["cut_silences"], 0.2, 10),
                    cut_fillers=_bool(f"{where}.cut_fillers", raw.get("cut_fillers", False)),
                    captions=_bool(f"{where}.captions", raw.get("captions", False)))
    if lead == "image":
        _unknown(where, raw, ("image", "seconds", "move", "fit", "effects", "transition", "grade"))
        move = raw.get("move")
        return Image(_path(f"{where}.image", raw["image"]),
                     _num(f"{where}.seconds", raw.get("seconds", 4.0), hi=600, above=0),
                     None if move is None else _choice(f"{where}.move", move, MOVES),
                     _choice(f"{where}.fit", raw.get("fit", "contain"), ("contain", "cover")), effects, tr, grade)
    if lead == "frames":
        _unknown(where, raw, ("frames", "seconds", "fit", "effects", "transition", "grade"))
        secs = raw.get("seconds")
        src = raw["frames"]  # from Python, a frame source itself (frames(...), a MoviePy clip) as well as a ref
        return Frames(src if hasattr(src, "get_frame") else _ref(f"{where}.frames", src),
                      None if secs is None else _num(f"{where}.seconds", secs, hi=3600, above=0),
                      _choice(f"{where}.fit", raw.get("fit", "contain"), ("contain", "cover")), effects, tr, grade)
    _unknown(where, raw, ("title", "lines", "seconds", "transition"))
    lines = raw.get("lines", [])
    if isinstance(lines, str):
        lines = [lines]
    if not (isinstance(lines, (list, tuple)) and len(lines) <= 4):
        raise ValueError(f"{where}.lines must be a list of up to 4 lines, got {lines!r}")
    return Title(_text(f"{where}.title", raw["title"], 80),
                 tuple(_text(f"{where}.lines[{i}]", s, 80) for i, s in enumerate(lines)),
                 _num(f"{where}.seconds", raw.get("seconds", 3.0), hi=30, above=0), tr)


def _overlay(where: str, raw) -> Overlay:
    lead = _lead(where, raw, OVERLAY_LEADS)
    fade = _num(f"{where}.fade", raw.get("fade", 0.0 if lead in ("draw", "scene") else 0.3), 0, 5)
    if lead == "image":
        _unknown(where, raw, ("image", "at", "until", "box", "fade"))
        return Picture(_path(f"{where}.image", raw["image"]), *_span(where, raw), _box(f"{where}.box", raw.get("box")),
                       fade)
    if lead == "text":
        _unknown(where, raw, ("text", "at", "until", "kind", "sub", "pos", "fade"))
        kind = _choice(f"{where}.kind", raw.get("kind", "lower-third"), TEXT_KINDS)
        pos = raw.get("pos")
        if kind == "label" and pos is None:
            raise ValueError(f'{where} is a "label", so it needs "pos": [x, y]')
        sub = raw.get("sub", "")
        return Text(_text(f"{where}.text", raw["text"], 120), *_span(where, raw), kind,
                    _text(f"{where}.sub", sub, 120) if sub else "",
                    None if pos is None else _tuple(f"{where}.pos", pos, 2, "[x, y] in output pixels"), fade)
    if lead == "clip":
        _unknown(where, raw, ("clip", "at", "until", "box", "start", "volume", "fade"))
        vol = raw.get("volume")
        return Inset(_path(f"{where}.clip", raw["clip"]), *_span(where, raw), _box(f"{where}.box", raw.get("box")),
                     _num(f"{where}.start", raw.get("start", 0.0), 0),
                     None if vol is None else _num(f"{where}.volume", vol, *DB), fade)
    box = raw.get("box")
    box = None if box is None else _box(f"{where}.box", box)
    if lead == "draw":
        _unknown(where, raw, ("draw", "at", "until", "box", "fade"))
        return Draw(_ref(f"{where}.draw", raw["draw"]), *_span(where, raw), box, fade)
    _unknown(where, raw, ("scene", "at", "until", "box", "fade"))
    at = _num(f"{where}.at", raw.get("at"), 0)
    until = raw.get("until")
    return Scene(_ref(f"{where}.scene", raw["scene"]), at,
                 None if until is None else _num(f"{where}.until", until, above=at), box, fade)


def _audio(where: str, raw) -> Audio:
    lead = _lead(where, raw, AUDIO_LEADS)
    if lead == "say":
        _unknown(where, raw, ("say", "at"))
        return Say(_text(f"{where}.say", raw["say"], 1000), _num(f"{where}.at", raw.get("at"), 0))
    if lead == "music":
        _unknown(where, raw, ("music", "volume", "at", "until"))
        at = _num(f"{where}.at", raw.get("at", 0.0), 0)
        until = raw.get("until")
        return Music(_path(f"{where}.music", raw["music"]), _num(f"{where}.volume", raw.get("volume", -16.0), *DB),
                     at, None if until is None else _num(f"{where}.until", until, above=at))
    _unknown(where, raw, ("sound", "at", "volume", "start", "end"))
    start = _num(f"{where}.start", raw.get("start", 0.0), 0)
    end = raw.get("end")
    return Sound(_path(f"{where}.sound", raw["sound"]), _num(f"{where}.at", raw.get("at"), 0),
                 _num(f"{where}.volume", raw.get("volume", 0.0), *DB), start,
                 None if end is None else _num(f"{where}.end", end, above=start))


TOP_KEYS = ("version", "size", "fps", "captions", "duck_db", "spellings", "segments", "overlays", "audio")


def _spellings(v) -> tuple[tuple[str, str], ...]:
    """{"heard": "written"}: speech-to-text mishears names and terms; captions show the written form."""
    if isinstance(v, (list, tuple)) and all(isinstance(x, (list, tuple)) and len(x) == 2 for x in v):
        v = dict(v)  # a Timeline built in Python: (heard, written) pairs
    if not isinstance(v, dict) or not all(isinstance(k, str) and k.strip() and isinstance(w, str) and len(k) <= 100
                                          and len(w) <= 100 for k, w in v.items()):
        raise ValueError(f'spellings must be {{"heard": "written", ...}}, as text, got {v!r}')
    return tuple((k, w) for k, w in v.items())


def parse(raw) -> Timeline:
    """An edit's JSON object as a Timeline. Raises ValueError naming the first bad field. Function hooks may be
    "path.py:name" strings or, from Python, the functions themselves."""
    if not isinstance(raw, dict):
        raise ValueError(f"an edit must be a JSON object, got {type(raw).__name__}")  # noqa: TRY004
    _unknown("the edit", raw, TOP_KEYS)
    if raw.get("version", VERSION) != VERSION:
        raise ValueError(f"version must be {VERSION}, got {raw.get('version')!r}")
    size = raw.get("size", [1920, 1080])
    if not (isinstance(size, (list, tuple)) and len(size) == 2
            and all(isinstance(v, int) and not isinstance(v, bool) and 16 <= v <= MAX_SIDE and v % 2 == 0
                    for v in size)):
        raise ValueError(f"size must be [width, height], even whole numbers from 16 to {MAX_SIDE}, got {size!r}")
    segs = raw.get("segments")
    if not (isinstance(segs, (list, tuple)) and segs):
        raise ValueError("segments must be a list of at least one clip, image, title or frames")
    lists = {}
    for key in ("overlays", "audio"):
        v = raw.get(key, [])
        if not isinstance(v, (list, tuple)):
            raise ValueError(f"{key} must be a list, got {v!r}")  # noqa: TRY004 - edit errors are ValueError
        lists[key] = v
    tl = Timeline(
        segments=tuple(_segment(f"segments[{i}]", s) for i, s in enumerate(segs)),
        overlays=tuple(_overlay(f"overlays[{i}]", o) for i, o in enumerate(lists["overlays"])),
        audio=tuple(_audio(f"audio[{i}]", a) for i, a in enumerate(lists["audio"])),
        size=(size[0], size[1]),
        fps=_num("fps", raw.get("fps", 30), 1, 120),
        captions=_choice("captions", raw.get("captions", "srt"), CAPTIONS),
        duck_db=_num("duck_db", raw.get("duck_db", -12.0), -60, 0),
        spellings=_spellings(raw.get("spellings", {})),
    )
    if tl.segments[0].transition.kind != "cut":
        raise ValueError("segments[0].transition: the first segment has nothing before it to fade from")
    if sum(isinstance(a, Music) for a in tl.audio) > 1:
        raise ValueError("audio has more than one music bed; join the tracks into one file, or use sound")
    return tl


def validate(tl: Timeline) -> Timeline:
    """A Timeline built in Python, checked exactly as its JSON would be, with lists made tuples."""
    if not isinstance(tl, Timeline):
        raise ValueError(f"an edit's `timeline` must be a manimvox.edit.Timeline, got {type(tl).__name__}")  # noqa: TRY004
    return parse(to_dict(tl, keep_functions=True))


# ---------------------------------------------------------------- writing

LEADS = {Clip: "clip", Image: "image", Title: "title", Frames: "frames", Picture: "image", Text: "text",
         Inset: "clip", Draw: "draw", Scene: "scene", Say: "say", Music: "music", Sound: "sound"}
MAIN = {Clip: "path", Image: "path", Title: "text", Frames: "source", Picture: "path", Text: "text",
        Inset: "path", Draw: "fn", Scene: "scene", Say: "text", Music: "path", Sound: "path"}
HOOKS = {"source", "fn", "scene", "effects"}


def ref_of(obj, root: Path | None) -> str:
    """ "path.py:name" for a function or class defined at the top level of a file inside `root`."""
    import inspect

    name = getattr(obj, "__qualname__", "")
    try:
        src = inspect.getsourcefile(obj)
    except TypeError:
        src = None
    if root is None or not src or "<" in name or not REF.match(f"x.py:{name}"):
        raise ValueError(f"{obj!r} cannot be written to JSON: only a function or class defined at the top level "
                         "of a .py file inside the project can be named there; keep the edit in Python instead")
    try:
        rel = Path(src).resolve().relative_to(Path(root).resolve())
    except ValueError:
        raise ValueError(f"{obj!r} is defined in {src}, outside the project {root}; move it into the project "
                         "(blocks/ or edits/)") from None
    return f"{rel.as_posix()}:{name}"


def _plain(name: str, v, root, keep: bool):
    if name in HOOKS:
        if name == "effects":
            return [x if (keep or isinstance(x, str)) else ref_of(x, root) for x in v]
        return v if (keep or isinstance(v, str)) else ref_of(v, root)
    if isinstance(v, Transition):
        return v.kind if v.seconds == 0.5 else {"kind": v.kind, "seconds": v.seconds}
    if isinstance(v, Grade):
        return {f.name: list(x) if isinstance(x, tuple) else x for f in fields(Grade)
                if (x := getattr(v, f.name)) != f.default}
    if isinstance(v, (tuple, list)):
        return list(v)
    return v


def _default(f):
    if f.default is not MISSING:
        return f.default
    if f.default_factory is not MISSING:
        return f.default_factory()
    return MISSING


def _item(obj, root, keep: bool) -> dict:
    cls = type(obj)
    if cls not in LEADS:
        raise ValueError(f"{obj!r} is not a segment, overlay or sound of manimvox.edit")
    main = MAIN[cls]
    if cls is Clip and obj.episode is not None:
        out = {"episode": obj.episode}
    else:
        out = {LEADS[cls]: _plain(main, getattr(obj, main), root, keep)}
    for f in fields(cls):
        if f.name in (main, "episode"):
            continue
        v = getattr(obj, f.name)
        d = _default(f)
        if d is not MISSING and (v == d or (isinstance(d, tuple) and tuple(v) == d)):
            continue
        out[f.name] = _plain(f.name, v, root, keep)
    return out


def to_dict(tl: Timeline, root: Path | None = None, keep_functions: bool = False) -> dict:
    out: dict = {"version": VERSION}
    for f in fields(Timeline):
        if f.name in ("segments", "overlays", "audio"):
            continue
        v = getattr(tl, f.name)
        if (tuple(v) if isinstance(v, list) else v) != _default(f):
            out[f.name] = dict(v) if f.name == "spellings" else list(v) if isinstance(v, (tuple, list)) else v
    for key in ("segments", "overlays", "audio"):
        items = getattr(tl, key)
        if items or key == "segments":
            out[key] = [_item(x, root, keep_functions) for x in items]
    return out


# ---------------------------------------------------------------- placing it in time

@dataclass(frozen=True)
class Placed:
    """A segment on the output: from `at` for `seconds`, overlapping the one before it by `overlap`."""
    index: int
    segment: Segment
    at: float
    seconds: float
    overlap: float


def seconds_of(seg: Segment, length: float | None) -> float:
    """How long a segment lasts on the output. `length` is its source's length: the file, for a clip without
    an end, or the frame source, for frames without `seconds`."""
    if isinstance(seg, Clip):
        end = seg.end if seg.end is not None else length
        return max(0.0, (end - seg.start) / seg.speed) if end is not None else 0.0
    if isinstance(seg, Frames):
        return seg.seconds if seg.seconds is not None else (length or 0.0)
    return seg.seconds


def place(tl: Timeline, lengths: list[float | None]) -> list[Placed]:
    """Where each segment sits on the output, given each source's length (None where it is not needed)."""
    out, t = [], 0.0
    for i, seg in enumerate(tl.segments):
        secs = seconds_of(seg, lengths[i])
        overlap = 0.0 if i == 0 or seg.transition.kind == "cut" else seg.transition.seconds
        at = max(0.0, t - overlap)
        out.append(Placed(i, seg, at, secs, overlap))
        t = at + secs
    return out


def duration(placed: list[Placed]) -> float:
    return max((p.at + p.seconds for p in placed), default=0.0)
