"""Render an edit: every output frame is pulled from the segment that owns that moment, layers are drawn over it,
captions last, and the sound is mixed 30 seconds at a time as the frames go out, so memory does not grow with
the film's length.

`render_edit(root, name)` writes out/<name>.mp4 and .srt. `draft=True` renders at 480p with a fast encoder into
build/edit/<name>/; `start`/`end` render only that window of the film, for checking one fix in seconds.
"""
from __future__ import annotations

import hashlib
import itertools
import math
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..post.audio import RATE, duck_curve, read_audio
from ..post.draw import caption_overlay, card_image
from ..post.encode import Writer
from .check import SLACK, check_edit
from .load import frame_source, resolve_path, resolve_ref, source_path
from .picture import (
    Reader,
    blend,
    ceil_even,
    fade_level,
    fit_array,
    fit_frame,
    mix,
    moving,
    resize,
    smooth,
    text_layer,
    to_array,
)
from .sound import add_at, bed_window, db, envelope, fit_length, levelling_db, limit_stereo, read_span, samples, stretch
from .timeline import (
    Clip,
    Draw,
    Frames,
    Grade,
    Image,
    Inset,
    Music,
    Picture,
    Placed,
    Say,
    Scene,
    Sound,
    Text,
    Timeline,
    Title,
    place,
)

CHUNK = 30.0  # seconds of sound mixed at a time
CARD_ANIM = 0.6  # seconds a title card takes to type in
DRAFT_HEIGHT = 480


class EditError(ValueError):
    """An edit that cannot be rendered as it stands; the message says what to fix."""


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


@dataclass
class EditRender:
    video: str
    srt: str | None
    seconds: float
    size: tuple[int, int]
    notes: list[str] = field(default_factory=list)
    sheets: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- segments: one picture per moment

class _Segment:
    """Frames of one placed segment at the render size, read in order; `frame(u)` is u seconds into it."""

    def __init__(self, r: _Render, p: Placed):
        self.r, self.p, self.seg = r, p, p.segment
        self.effects = [r.hook(fx, f"segments[{p.index}].effects") for fx in getattr(self.seg, "effects", ())]
        self.look = r.look(getattr(self.seg, "grade", None), f"segments[{p.index}].grade")
        self.reader = None
        self.still = None
        self.source = None
        seg = self.seg
        if isinstance(seg, Clip):
            self.reader = Reader(source_path(r.root, seg))
        elif isinstance(seg, Image):
            from PIL import Image as PILImage

            with PILImage.open(resolve_path(r.root, seg.path)) as img:
                a = to_array(img, alpha=True)
            self.still = fit_array(a, r.W, r.H, seg.fit, r.bg, self.look)
        elif isinstance(seg, Frames):
            self.source = frame_source(r.root, seg.source)

    def frame(self, u: float) -> np.ndarray:
        seg, r = self.seg, self.r
        u = min(max(0.0, u), max(0.0, self.p.seconds - 1e-6))
        if isinstance(seg, Clip):
            rgb = fit_frame(self.reader.at(seg.start + u * seg.speed), r.W, r.H, seg.fit, seg.crop, r.bg, self.look)
        elif isinstance(seg, Image):
            rgb = moving(self.still, seg.move, u / seg.seconds if seg.seconds else 1.0, r.W, r.H)
        elif isinstance(seg, Title):
            rgb = r.card(seg, smooth(u / CARD_ANIM) if u < CARD_ANIM else 1.0)
        else:
            rgb = fit_array(to_array(self.source.get_frame(u), alpha=True), r.W, r.H, seg.fit, r.bg, self.look)
        for fx in self.effects:
            out = to_array(fx(rgb, u))
            if out.shape != rgb.shape:
                raise EditError(f"segments[{self.p.index}]: an effect returned a {out.shape[1]}x{out.shape[0]} "
                                f"frame for a {rgb.shape[1]}x{rgb.shape[0]} one; return the frame it was given")
            rgb = out
        return rgb

    def close(self) -> None:
        if self.reader is not None:
            self.reader.close()


# ---------------------------------------------------------------- layers over the picture

class _Layer:
    def __init__(self, r: _Render, i: int, o):
        self.r, self.i, self.o = r, i, o
        self.until = getattr(o, "until", None)
        self.reader = None
        self.fixed = None  # (x, y, rgba) for a still layer
        s = r.scale
        if isinstance(o, Picture):
            from PIL import Image as PILImage

            with PILImage.open(resolve_path(r.root, o.path)) as img:
                a = to_array(img, alpha=True)
            w = max(1, round(o.box[2] * s))
            self.fixed = (round(o.box[0] * s), round(o.box[1] * s), resize(a, w, max(1, round(w * a.shape[0] / a.shape[1]))))
        elif isinstance(o, Text):
            self.fixed = text_layer(o, r.W, r.H, r.theme, s)
        elif isinstance(o, Inset):
            self.reader = Reader(resolve_path(r.root, o.path))
            self.key_rgb = None  # the key colour, found on the first frame drawn
        elif isinstance(o, Draw):
            self.fn = r.hook(o.fn, f"overlays[{i}].draw")
        elif isinstance(o, Scene):
            path = r.scene_video(o.scene, f"overlays[{i}].scene")
            self.reader = Reader(path)
            from .probe import probe

            length = probe(path).seconds or 0.0
            self.until = o.at + length if o.until is None else min(o.until, o.at + length)

    def active(self, t: float) -> bool:
        return self.o.at <= t < (self.until if self.until is not None else math.inf)

    def draw(self, frame: np.ndarray, t: float) -> None:
        o, _r, s = self.o, self.r, self.r.scale
        u = t - o.at
        level = fade_level(t, o.at, self.until, o.fade)
        if self.fixed is not None:
            x, y, rgba = self.fixed
        elif isinstance(o, Inset):
            f = self.reader.at(o.start + u)
            if o.box is None:  # fitted to the whole frame, centred
                k = min(_r.W / f.width, _r.H / f.height)
                w, h = max(2, round(f.width * k)), max(2, round(f.height * k))
                x, y = (_r.W - w) // 2, (_r.H - h) // 2
            else:
                w = max(2, round(o.box[2] * s))
                h = max(2, round(w * f.height / f.width))
                x, y = round(o.box[0] * s), round(o.box[1] * s)
            rgba = f.reformat(width=w, height=h, format="rgba").to_ndarray()
            if o.key is not None:
                from .key import key_color, keyed

                if self.key_rgb is None:
                    self.key_rgb = key_color(o.key, rgba)
                rgba = keyed(rgba, o.key, self.key_rgb)
        elif isinstance(o, Draw):
            rgba = to_array(self.fn(u), alpha=True)
            x, y, rgba = self._boxed(rgba)
        else:  # Scene
            f = self.reader.at(u)
            rgba = f.reformat(format="rgba").to_ndarray()
            x, y, rgba = self._boxed(rgba)
        blend(frame, rgba, x, y, level)

    def _boxed(self, rgba: np.ndarray) -> tuple[int, int, np.ndarray]:
        o, r, s = self.o, self.r, self.r.scale
        if o.box is None:
            return 0, 0, resize(rgba, r.W, r.H)
        w = max(1, round(o.box[2] * s))
        return round(o.box[0] * s), round(o.box[1] * s), resize(rgba, w, max(1, round(w * rgba.shape[0] / rgba.shape[1])))

    def close(self) -> None:
        if self.reader is not None:
            self.reader.close()


# ---------------------------------------------------------------- the render

class _Render:
    def __init__(self, root: Path, tl: Timeline, lengths, theme, scale: float, voice_lines, target: float | None,
                 say: Callable[[str], None], transcripts: dict | None = None):
        from .._cairo import hex_rgb

        self.root, self.tl, self.theme, self.scale, self.say = Path(root), tl, theme, scale, say
        self.W, self.H = ceil_even(tl.size[0] * scale), ceil_even(tl.size[1] * scale)
        self.bg = tuple(round(c * 255) for c in hex_rgb(theme["bg"]))
        self.placed = place(tl, lengths)
        self.total = max(p.at + p.seconds for p in self.placed)
        self.voice_lines = voice_lines  # [(Say, path, seconds)]
        self.cues = [Cue(a.at, a.at + secs, a.text) for a, _p, secs in voice_lines]  # narration
        self.speech = self._speech(transcripts or {})  # what the speakers in the footage say, as captions
        self.captions = sorted(self.cues + self.speech, key=lambda c: c.start)
        self.target = target
        self.notes: list[str] = []
        self._cards: dict = {}
        self._grades: dict = {}  # grade lookup tables, by grade
        self._gains: dict = {}
        self._made: dict[int, object] = {}  # Frames sources' sound, read once

    # ---- helpers

    def hook(self, ref, where: str):
        try:
            return resolve_ref(self.root, ref)
        except ValueError as e:
            raise EditError(f"{where}: {e}") from e

    def look(self, g, where: str):
        """The function that grades a picture by `g`, or None; each table is built once per render."""
        if g is None or g == Grade():
            return None
        if g not in self._grades:
            from .grade import apply_table, build_table, read_cube

            try:
                cube = None if g.lut is None else read_cube(resolve_path(self.root, g.lut))
            except ValueError as e:
                raise EditError(f"{where}.lut: {e}") from e
            if len(self._grades) >= 3:  # a table is 48 MB: keep the few segments around a seam
                self._grades.pop(next(iter(self._grades)))
            table = build_table(g, cube)
            self._grades[g] = lambda a, table=table: apply_table(table, a)
        return self._grades[g]

    def card(self, seg: Title, progress: float) -> np.ndarray:
        key = (seg.text, seg.lines, round(progress, 3))
        if key not in self._cards:
            if len(self._cards) > 64:
                self._cards.clear()
            self._cards[key] = card_image(seg.text, list(seg.lines), self.W, self.H, self.theme, progress)
        return self._cards[key]

    def scene_video(self, ref, where: str) -> Path:
        """A Manim scene rendered once with a transparent background at the render size, cached by its file."""
        import inspect

        if isinstance(ref, str):
            file, name = ref.split(":", 1)
            path = resolve_path(self.root, file)
        else:
            src = inspect.getsourcefile(ref)
            if not src or "<" in ref.__qualname__ or "." in ref.__qualname__:
                raise EditError(f"{where}: a Scene class must be defined at the top level of a .py file")
            path, name = Path(src), ref.__qualname__
        if not path.is_file():
            raise EditError(f"{where}: no file {path}")
        key = hashlib.sha1(f"{path.resolve()}|{path.stat().st_mtime_ns}|{name}|{self.W}x{self.H}|{self.tl.fps}"
                           .encode()).hexdigest()[:16]
        media = self.root / "build" / "edit" / "scenes" / key
        found = sorted(media.glob(f"videos/**/{name}.mov"))
        if found:
            return found[0]
        self.say(f"scene: rendering {name} from {path.name} with a transparent background ...")
        env = {k: v for k, v in os.environ.items() if not k.startswith("MANIMVOX_") or k == "MANIMVOX_CACHE"}
        env |= {"MANIMVOX_PROJECT": str(self.root), "MANIMVOX_NOTTS": "1", "PYTHONUTF8": "1"}
        cmd = [sys.executable, "-m", "manim", "render", "-t", "--fps", f"{self.tl.fps:g}", "-r", f"{self.W},{self.H}",
               "--progress_bar", "none", "--disable_caching", "--media_dir", str(media), "-o", name, str(path), name]
        r = subprocess.run(cmd, check=False, cwd=self.root, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        found = sorted(media.glob(f"videos/**/{name}.mov"))
        if r.returncode != 0 or not found:
            tail = "\n".join((r.stderr or r.stdout).strip().splitlines()[-20:])
            raise EditError(f"{where}: manim failed for {name}:\n{tail}")
        return found[0]

    def _speech(self, transcripts: dict) -> list[Cue]:
        """Captions of the words spoken in captioned clips, at their times on the output."""
        from .transcribe import caption_cues, respell

        # Each word goes to the captioned piece it overlaps most: word times drift, so a word whose sound was
        # kept can have a time that only partly falls in its piece, and a word over a cut is shown once.
        best: dict[tuple[int, int], tuple[float, tuple]] = {}
        for p in self.placed:
            tr = transcripts.get(p.index)
            if tr is None:
                continue
            seg = p.segment
            end = seg.start + p.seconds * seg.speed
            for k, w in enumerate(tr.words):
                # A word after a pause is given a start too early (the pause is folded into it), so its sound is
                # at its end: judge which piece it is in by its last 0.15 s.
                core = max(w.start, w.end - 0.15)
                if min(w.end, end) - max(core, seg.start) < (w.end - core) / 2:
                    continue
                lo, hi = max(w.start, seg.start), min(w.end, end)
                key = (id(tr), k)
                if key not in best or hi - lo > best[key][0]:
                    best[key] = (hi - lo, (p.at + (lo - seg.start) / seg.speed, p.at + (hi - seg.start) / seg.speed,
                                           w.text))
        words = sorted(v[1] for v in best.values())
        return [Cue(a, b, respell(text, self.tl.spellings)) for a, b, text in caption_cues(words)]

    # ---- sound

    def _duck(self, cues: list[Cue], t0: float, t1: float) -> np.ndarray:
        """The gain from t0 to t1 of sound that dips while `cues` are spoken."""
        n, margin = samples(t1 - t0), 1.0
        wide = duck_curve(samples(t1 - t0 + 2 * margin), [Cue(c.start - (t0 - margin), c.end - (t0 - margin), "")
                                                          for c in cues], self.tl.duck_db)
        duck = wide[samples(margin):samples(margin) + n]
        return np.pad(duck, (0, n - duck.shape[0]), constant_values=1.0)

    def _gain(self, key, read) -> float:
        """The levelling gain (dB) of one piece of footage sound, measured once over the whole piece."""
        if key not in self._gains:
            g, now = levelling_db(read(), self.target)
            self._gains[key] = g
            if now is not None and abs(g) >= 0.5:
                self.notes.append(f"{key[0]}: sound at {now:.1f} LUFS, {'raised' if g > 0 else 'lowered'} "
                                  f"{abs(g):.1f} dB" + (" (the most it is raised)" if g >= 11.99 else ""))
        return self._gains[key]

    def _segment_sound(self, p: Placed, lo: float, hi: float) -> np.ndarray | None:
        seg = p.segment
        n = samples(hi - lo)
        if isinstance(seg, Clip):
            if seg.mute:
                return None
            path = source_path(self.root, seg)
            s0, s1 = seg.start + (lo - p.at) * seg.speed, seg.start + (hi - p.at) * seg.speed
            pad = 0.25 * seg.speed if seg.speed != 1 else 0.0  # atempo settles in: read a little either side
            a0 = max(0.0, s0 - pad)
            x = read_span(path, a0, s1 + pad)
            x = stretch(x, seg.speed)
            x = fit_length(x[:, samples((s0 - a0) / seg.speed):], n)
            if seg.episode is not None:  # a rendered episode's narration is levelled already, line by line
                return x * db(seg.volume)
            end = seg.end if seg.end is not None else seg.start + p.seconds * seg.speed
            g = self._gain((f"segments[{p.index}] ({seg.path})", str(path), seg.start, end),
                           lambda: read_span(path, seg.start, end))
            return x * db(g + seg.volume)
        if isinstance(seg, Frames):
            if p.index not in self._made:
                src = frame_source(self.root, seg.source)
                a = src.audio(RATE) if hasattr(src, "audio") else None
                self._made[p.index] = None if a is None else fit_length(np.asarray(a, np.float32), samples(p.seconds))
            a = self._made[p.index]
            if a is None:
                return None
            g = self._gain((f"segments[{p.index}] (frames)", p.index), lambda: a)
            i = samples(lo - p.at)
            return fit_length(a[:, i:i + n], n) * db(g)
        return None

    def mix(self, t0: float, t1: float) -> np.ndarray:
        """The finished sound of the film from t0 to t1 seconds."""
        n = samples(t1 - t0)
        footage = np.zeros((2, n), np.float32)
        for i, p in enumerate(self.placed):
            lo, hi = max(p.at, t0), min(p.at + p.seconds, t1)
            if hi <= lo:
                continue
            x = self._segment_sound(p, lo, hi)
            if x is None:
                continue
            nxt = self.placed[i + 1] if i + 1 < len(self.placed) else None
            fade_in = (p.segment.transition.kind, p.overlap) if p.overlap else ("cut", 0.0)
            fade_out = (nxt.segment.transition.kind, nxt.overlap) if nxt is not None and nxt.overlap else ("cut", 0.0)
            i0 = samples(lo - p.at)
            env = envelope(samples(p.seconds), fade_in, fade_out, i0, i0 + x.shape[1])
            add_at(footage, x * env, lo - t0)
        for k, o in enumerate(self.tl.overlays):
            if isinstance(o, Inset) and o.volume is not None:
                lo, hi = max(o.at, t0), min(o.until, t1)
                if hi <= lo:
                    continue
                path = resolve_path(self.root, o.path)
                x = read_span(path, o.start + (lo - o.at), o.start + (hi - o.at))
                g = self._gain((f"overlays[{k}] ({o.path})", str(path), o.start, o.start + o.until - o.at),
                               lambda path=path, o=o: read_span(path, o.start, o.start + o.until - o.at))
                n_all = samples(o.until - o.at)
                i0 = samples(lo - o.at)
                env = envelope(n_all, ("fade", o.fade) if o.fade else ("cut", 0), ("fade", o.fade) if o.fade
                               else ("cut", 0), i0, i0 + x.shape[1])
                add_at(footage, x * env * db(g + o.volume), lo - t0)
        # the footage dips under the narration; the music dips under the narration and the speakers alike
        out = footage * self._duck(self.cues, t0, t1)
        music_duck = None
        for a in self.tl.audio:
            if isinstance(a, Music):
                if music_duck is None:
                    music_duck = self._duck(self.captions, t0, t1)
                music = self._music(a.path)
                out += bed_window(music, a.at, a.until if a.until is not None else self.total, t0, t1,
                                  a.volume) * music_duck
            elif isinstance(a, Sound):
                path = resolve_path(self.root, a.path)
                end = a.end if a.end is not None else None
                lo = max(a.at, t0)
                if lo >= t1 or (end is not None and a.at + (end - a.start) <= t0):
                    continue
                x = read_span(path, a.start + (lo - a.at), end)
                if end is None:
                    x = x[:, :samples(t1 - lo)]
                k = min(x.shape[1], samples(0.01))
                if k and lo == a.at:
                    x[:, :k] *= np.linspace(0, 1, k, dtype=np.float32)
                add_at(out, x, lo - t0, db(a.volume))
        for a, path, secs in self.voice_lines:
            if a.at < t1 and a.at + secs > t0:
                add_at(out, self._voice(path), a.at - t0)
        return limit_stereo(out)

    def _music(self, path: str) -> np.ndarray:
        if not hasattr(self, "_music_cache"):
            self._music_cache = {}
        if path not in self._music_cache:
            self._music_cache[path] = read_audio(resolve_path(self.root, path))
        return self._music_cache[path]

    def _voice(self, path: Path) -> np.ndarray:
        if not hasattr(self, "_voice_cache"):
            self._voice_cache = {}
        if path not in self._voice_cache:
            if len(self._voice_cache) > 16:
                self._voice_cache.clear()
            self._voice_cache[path] = read_audio(path)
        return self._voice_cache[path]

    # ---- picture

    def run(self, dst: Path, t0: float, t1: float, draft: bool, burn: bool, progress) -> int:
        fps = self.tl.fps
        k0, k1 = round(t0 * fps), round(t1 * fps)
        out = Writer(dst, (self.W, self.H), fps, crf=28 if draft else 18, preset="ultrafast" if draft else "medium")
        segs: dict[int, _Segment] = {}
        layers: dict[int, _Layer] = {}
        captions: dict[int, object] = {}
        mixed_to = t0
        try:
            for k in range(k0, k1):
                t = k / fps
                while mixed_to < min(t1, t + 2.0):  # keep a little sound ahead of the picture
                    nxt = min(t1, mixed_to + CHUNK)
                    out.audio(self.mix(mixed_to, nxt))
                    mixed_to = nxt
                live = [p for p in self.placed if p.at - 1e-9 <= t < p.at + p.seconds - 1e-9] or [self.placed[-1]]
                for i in [i for i in segs if all(p.index != i for p in live) and self.placed[i].at < t]:
                    segs.pop(i).close()

                def frame_of(p: Placed, t=t) -> np.ndarray:
                    if p.index not in segs:
                        segs[p.index] = _Segment(self, p)
                    return segs[p.index].frame(t - p.at)

                cur = live[-1]
                if len(live) > 1 and cur.overlap:
                    prev = live[-2]
                    q = (t - cur.at) / cur.overlap
                    if cur.segment.transition.kind == "fade":
                        frame = mix(frame_of(prev), frame_of(cur), q)
                    else:
                        blank = np.empty((self.H, self.W, 3), np.uint8)
                        blank[:] = self.bg
                        frame = mix(frame_of(prev), blank, q * 2) if q < 0.5 else mix(blank, frame_of(cur), q * 2 - 1)
                else:
                    frame = frame_of(cur)
                frame = np.array(frame, copy=True)
                for i, o in enumerate(self.tl.overlays):
                    if i not in layers:
                        if o.at > t:
                            continue
                        layers[i] = _Layer(self, i, o)
                    if layers[i].active(t):
                        layers[i].draw(frame, t)
                if burn:
                    for j, c in enumerate(self.captions):
                        if c.start <= t < c.end:
                            if j not in captions:
                                captions.clear()
                                captions[j] = caption_overlay(c.text, self.W, self.H, self.theme)
                            captions[j].blend(frame)
                            break
                out.add(frame)
                if progress and (k - k0) % max(1, round(fps * 10)) == 0:
                    progress(t - t0, t1 - t0)
            out.close()
        except BaseException:
            out.abort()
            raise
        finally:
            for s in segs.values():
                s.close()
            for la in layers.values():
                la.close()
        return k1 - k0


def _srt(cues: list[Cue], offset: float = 0.0) -> str:
    def ts(t: float) -> str:
        ms = round(max(0.0, t) * 1000)
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    return "\n".join(f"{i}\n{ts(c.start - offset)} --> {ts(c.end - offset)}\n{c.text}\n" for i, c in enumerate(cues, 1))


def _clock(t: float) -> str:
    return f"{int(t // 60)}m{t % 60:04.1f}s".replace(".", "_")


def render_edit(root: Path, name: str, *, voice: str | None = None, confirm: Callable[[str], bool] = lambda m: False,
                draft: bool = False, start: float | None = None, end: float | None = None,
                say: Callable[[str], None] | None = None, sheets: bool = True) -> EditRender:
    """Render the edit `name`; see the module docstring for where it goes."""
    from ..checks.sheets import contact_sheets
    from ..kit.theme import Theme
    from ..project import load_project
    from .load import load

    say = say or (lambda line: None)
    root = Path(root)
    pr = load_project(root)
    tl = load(root, name)
    stem = Path(name).stem
    rep = check_edit(root, tl)
    if not rep.ok:
        raise EditError(f"edits/{stem} has {len(rep.findings)} problem(s); fix them first "
                        f"(manimvox check edit {stem}):\n" + "\n".join(f"  {f}" for f in rep.findings))
    tl = rep.timeline  # clips cut by their transcripts, as the pieces they keep
    total = rep.seconds
    t0 = 0.0 if start is None else float(start)
    t1 = total if end is None else min(float(end), total)
    if not (0 <= t0 < t1):
        raise EditError(f"the window {t0:g} s to {t1:g} s is empty; the film is {total:.2f} s long")

    notes: list[str] = []
    lines = []
    says = sorted((a for a in tl.audio if isinstance(a, Say)), key=lambda a: a.at)
    if says:
        from ..voice import get_engine, resolve_voice
        from ..voice.cache import synth_cached
        from ..voice.pron import spoken_form

        spec = resolve_voice(voice, pr.voice, os.environ)
        eng = get_engine(spec.engine)
        eng.prepare(spec.voice, confirm, pr.root)
        if eng.online:
            notes.append(f"note: narration text is sent to {eng.online} ({spec})")
        say(f"voice: {len(says)} line(s) in {spec} ...")
        for a in says:
            path, secs = synth_cached(spec, spoken_form(a.text, pr.pron), pr.speed, pr.cache_dir, pr.loudness)
            lines.append((a, path, secs))
        for (a, _, sa), (b, _, _) in itertools.pairwise(lines):
            if b.at < a.at + sa - 0.05:
                raise EditError(f"the line {b.text[:40]!r} at {b.at:g} s starts before {a.text[:40]!r} ends at "
                                f"{a.at + sa:.2f} s; move it to {a.at + sa + 0.3:.1f} s or later")
        a, _, sa = lines[-1]
        if a.at + sa > total + SLACK:
            raise EditError(f"the line {a.text[:40]!r} runs to {a.at + sa:.2f} s, past the film's end "
                            f"({total:.2f} s); start it by {max(0.0, total - sa - 0.3):.1f} s")

    scale = min(1.0, DRAFT_HEIGHT / tl.size[1]) if draft else 1.0
    r = _Render(root, tl, rep.lengths, Theme.from_dict(pr.theme), scale, lines, pr.loudness, say, rep.transcripts)
    notes += rep.cuts
    whole = start is None and end is None
    if whole and not draft:
        dst = root / "out" / f"{stem}.mp4"
    else:
        tag = "draft" if draft else "final"
        dst = root / "build" / "edit" / stem / (f"{tag}.mp4" if whole else f"{tag}_{_clock(t0)}-{_clock(t1)}.mp4")
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.stem + ".part.mp4")
    burn = tl.captions == "burn"
    say(f"render: {t1 - t0:.1f} s at {r.W}x{r.H}, {tl.fps:g} fps{' (draft)' if draft else ''} ...")
    try:
        r.run(tmp, t0, t1, draft, burn, lambda done, of: say(f"  {done:.0f} of {of:.0f} s"))
        os.replace(tmp, dst)
    finally:
        tmp.unlink(missing_ok=True)
    srt = None
    if tl.captions != "none" and r.captions:
        srt_path = dst.with_suffix(".srt")
        shown = [c for c in r.captions if c.end > t0 and c.start < t1]
        srt_path.write_text(_srt(shown, t0), encoding="utf-8")
        srt = str(srt_path)
    shots = []
    if sheets:
        every = max(0.5, round((t1 - t0) / 18, 1))
        shots = [str(s) for s in contact_sheets(dst, root / "sheets" / "edit" / stem, every=every)]
    notes += r.notes
    return EditRender(str(dst), srt, round(t1 - t0, 3), (r.W, r.H), notes, shots)

