"""An edit as an OpenTimelineIO timeline (`out/<name>.otio`), to see and adjust it in Kdenlive, DaVinci Resolve or
any editor that reads OTIO.

What the file can name it names: pieces of footage, rendered episodes and plain stills are clips of their own
files, trimmed, with their speed as a LinearTimeWarp, and fades and dips as dissolves. What only manimvox can
draw (title cards, frames made by code, and any piece that is graded, stabilised, cropped, filled, moved, ramped
or changed by an effect) is rendered to a short file in build/edit/<name>/otio/ and placed instead, so the
timeline plays as the film. Every overlay is rendered the same way, as ProRes 4444 with its transparency, on a
video track of its own. Sound goes on audio tracks: the footage's, any picture-in-picture's, the narration (the
voice's files), the music and the sound files.

The JSON is written directly; nothing beyond manimvox is needed to make it. Levels and ducking are not part of
OTIO, so the footage is at its own level (the gain manimvox would use is in each clip's metadata), and the
rendered film's sound remains the reference.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from fractions import Fraction
from pathlib import Path

import av
import numpy as np

from .check import check_edit
from .load import resolve_path, source_path
from .probe import probe
from .render import EditError, _Layer, _Render, voice_lines
from .timeline import Clip, Grade, Image, Inset, Multicam, Music, Sound, Timeline


@dataclass
class OtioExport:
    path: str
    rendered: list[str] = field(default_factory=list)  # files made for pieces only manimvox can draw
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- OTIO's JSON


class _Doc:
    """OTIO objects as plain JSON, every time at the film's frame rate."""

    def __init__(self, fps: float):
        self.fps = fps

    def time(self, seconds: float) -> dict:
        return {"OTIO_SCHEMA": "RationalTime.1", "rate": self.fps, "value": round(seconds * self.fps, 6)}

    def frames(self, n: int) -> dict:
        return {"OTIO_SCHEMA": "RationalTime.1", "rate": self.fps, "value": float(n)}

    def range(self, start: float, frames: int) -> dict:
        return {"OTIO_SCHEMA": "TimeRange.1", "start_time": self.time(start), "duration": self.frames(frames)}

    def clip(self, name: str, path: Path, start: float, frames: int, speed: float = 1.0,
             meta: dict | None = None) -> dict:
        ref = {"OTIO_SCHEMA": "ExternalReference.1", "name": path.name, "target_url": path.resolve().as_uri(),
               "available_range": None, "available_image_bounds": None, "metadata": {}}
        effects = [] if speed == 1.0 else [{"OTIO_SCHEMA": "LinearTimeWarp.1", "name": "speed",
                                            "effect_name": "LinearTimeWarp", "time_scalar": speed, "metadata": {}}]
        return {"OTIO_SCHEMA": "Clip.2", "name": name, "source_range": self.range(start, frames),
                "effects": effects, "markers": [], "enabled": True, "color": None,
                "media_references": {"DEFAULT_MEDIA": ref}, "active_media_reference_key": "DEFAULT_MEDIA",
                "metadata": {"manimvox": meta} if meta else {}}

    def gap(self, frames: int) -> dict:
        return {"OTIO_SCHEMA": "Gap.1", "name": "", "source_range": self.range(0.0, frames), "effects": [],
                "markers": [], "enabled": True, "color": None, "metadata": {}}

    def dissolve(self, half: int) -> dict:
        return {"OTIO_SCHEMA": "Transition.1", "name": "dissolve", "transition_type": "SMPTE_Dissolve",
                "in_offset": self.frames(half), "out_offset": self.frames(half), "metadata": {}}

    @staticmethod
    def track(name: str, kind: str, children: list) -> dict:
        return {"OTIO_SCHEMA": "Track.1", "name": name, "kind": kind, "children": children, "source_range": None,
                "effects": [], "markers": [], "enabled": True, "color": None, "metadata": {}}


def _lay(doc: _Doc, items: list[tuple[int, int, dict]], total: int) -> list[dict]:
    """Items (from frame, frames, clip) on one track, in order, with gaps between them and to the end."""
    out, at = [], 0
    for k0, n, item in sorted(items, key=lambda x: x[0]):
        if k0 > at:
            out.append(doc.gap(k0 - at))
        out.append(item)
        at = k0 + n
    if at < total:
        out.append(doc.gap(total - at))
    return out


def _stack(spans: list[tuple[int, int, dict]]) -> list[list[tuple[int, int, dict]]]:
    """Spans shared out over as few tracks as hold them without overlap: each to the first track free in time."""
    tracks: list[list] = []
    for s in sorted(spans, key=lambda x: x[0]):
        for tr in tracks:
            if tr[-1][0] + tr[-1][1] <= s[0]:
                tr.append(s)
                break
        else:
            tracks.append([s])
    return tracks


# ---------------------------------------------------------------- what can be named, and what must be drawn


def _plain(seg) -> bool:
    """A piece the timeline can name as its own file: trimmed, at one speed, and nothing else done to it."""
    if isinstance(seg, Clip):
        return (not isinstance(seg.speed, tuple) and seg.fit == "contain" and seg.crop is None and not seg.effects
                and (seg.grade is None or seg.grade == Grade()) and seg.stabilize is None)
    if isinstance(seg, Image):
        return seg.move is None and seg.fit == "contain" and not seg.effects and seg.grade is None
    return False


def _alpha_writer(path: Path, size: tuple[int, int], fps: float):
    c = av.open(str(path), "w")
    s = c.add_stream("prores_ks", rate=Fraction(fps).limit_denominator(1001))
    s.width, s.height, s.pix_fmt = size[0], size[1], "yuva444p10le"
    s.options = {"profile": "4"}  # 4444, which keeps an alpha channel
    return c, s


def _stamp(canvas: np.ndarray, rgba: np.ndarray, x: int, y: int, level: float) -> None:
    """Paint RGBA pixels onto a transparent RGBA canvas (straight alpha), in place, clipped to it."""
    h, w = canvas.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(w, x + rgba.shape[1]), min(h, y + rgba.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    if src.shape[2] == 3:
        src = np.concatenate([src, np.full(src.shape[:2] + (1,), 255, np.float32)], axis=2)
    dst = canvas[y0:y1, x0:x1].astype(np.float32)
    sa = src[..., 3:] / 255.0 * level
    da = dst[..., 3:] / 255.0
    oa = sa + da * (1 - sa)
    rgb = (src[..., :3] * sa + dst[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-6)
    canvas[y0:y1, x0:x1, :3] = np.rint(rgb)
    canvas[y0:y1, x0:x1, 3:] = np.rint(oa * 255)


def _render_layer(r: _Render, i: int, o, dst: Path) -> tuple[float, float]:
    """Overlay `i` alone, over transparency, as ProRes 4444: (from, until) seconds of the film it covers."""
    layer = _Layer(r, i, o)
    try:
        until = layer.until if layer.until is not None else r.total
        fps = r.tl.fps
        k0, k1 = round(o.at * fps), round(min(until, r.total) * fps)
        c, s = _alpha_writer(dst, (r.W, r.H), fps)
        try:
            for k in range(k0, max(k0 + 1, k1)):
                canvas = np.zeros((r.H, r.W, 4), np.uint8)
                t = k / fps
                if layer.active(t):
                    x, y, rgba, level = layer.pixels(t)
                    _stamp(canvas, rgba, x, y, level)
                f = av.VideoFrame.from_ndarray(canvas, format="rgba")
                for p in s.encode(f):
                    c.mux(p)
            for p in s.encode():
                c.mux(p)
        finally:
            c.close()
        return k0 / fps, max(k0 + 1, k1) / fps
    finally:
        layer.close()


def _render_piece(r: _Render, tl: Timeline, i: int, dst: Path) -> None:
    """Segment `i` alone, over its whole placed length (so a dissolve has the frames it needs), with its sound."""
    p = r.placed[i]
    seg = p.segment
    one = replace(tl, segments=(replace(seg, transition=replace(seg.transition, kind="cut")),), overlays=(), audio=(),
                  captions="none")
    sub = _Render(r.root, one, [r.lengths[i]], r.theme, 1.0, [], r.target, r.say, {})
    sub.run(dst, 0.0, p.seconds, False, False, None)
    r.notes += sub.notes


# ---------------------------------------------------------------- the export


def export_edit(root: Path, name: str, *, voice: str | None = None, confirm: Callable[[str], bool] = lambda m: False,
                say: Callable[[str], None] | None = None) -> OtioExport:
    """Write out/<name>.otio for the edit `name`; see the module docstring for what goes in it."""
    from ..kit.theme import Theme
    from ..project import load_project
    from .load import load

    say = say or (lambda line: None)
    root = Path(root)
    pr = load_project(root)
    stem = Path(name).stem
    rep = check_edit(root, load(root, name))
    if not rep.ok:
        raise EditError(f"edits/{stem} has {len(rep.findings)} problem(s); fix them first "
                        f"(manimvox check edit {stem}):\n" + "\n".join(f"  {f}" for f in rep.findings))
    tl, total = rep.timeline, rep.seconds
    notes: list[str] = []
    lines = voice_lines(pr, tl, voice, confirm, say, total, notes)
    r = _Render(root, tl, rep.lengths, Theme.from_dict(pr.theme), 1.0, lines, pr.loudness, say, rep.transcripts)
    doc, fps = _Doc(tl.fps), tl.fps

    def F(s: float) -> int:  # a frame of the film, from seconds
        return round(s * fps)

    end = F(total)
    made = root / "build" / "edit" / stem / "otio"
    made.mkdir(parents=True, exist_ok=True)
    out = OtioExport(str(root / "out" / f"{stem}.otio"))

    # the main track: each piece from its cut to the next, a dissolve centred on each overlap
    placed = r.placed
    cuts = [F(p.at + p.overlap / 2) for p in placed] + [end]
    video, sound = [], []
    for i, p in enumerate(placed):
        seg = p.segment
        k0, n = cuts[i], cuts[i + 1] - cuts[i]
        u0 = k0 / fps - p.at  # seconds into the piece where it is first seen alone
        if i and p.overlap:
            half = max(1, round(p.overlap * fps / 2))
            video.append(doc.dissolve(half))
            if sound and sound[-1].get("OTIO_SCHEMA") == "Clip.2":
                sound.append(doc.dissolve(half))
        label = f"segments[{i}]"
        if isinstance(seg, Multicam):
            for a, b, cam in seg.spans(seg.start + p.seconds):
                ka, kb = max(k0, F(p.at + a - seg.start)), min(k0 + n, F(p.at + b - seg.start))
                if kb > ka:
                    path = resolve_path(root, seg.cameras[cam])
                    video.append(doc.clip(f"{label} camera {cam}", path, ka / fps - p.at + seg.start - seg.offsets[cam],
                                          kb - ka))
            if not seg.mute:
                cam = seg.sound
                sound.append(doc.clip(f"{label} sound", resolve_path(root, seg.cameras[cam]),
                                      u0 + seg.start - seg.offsets[cam], n, meta={"volume_db": seg.volume}))
            else:
                sound.append(doc.gap(n))
            continue
        if _plain(seg):
            path = source_path(root, seg) if isinstance(seg, Clip) else resolve_path(root, seg.path)
            if isinstance(seg, Clip):
                clock = r.clock(p)
                video.append(doc.clip(label, path, clock.source(u0), n, seg.speed))
                if seg.mute:
                    sound.append(doc.gap(n))
                else:
                    sound.append(doc.clip(f"{label} sound", path, clock.source(u0), n, seg.speed,
                                          meta={"volume_db": seg.volume}))
            else:
                video.append(doc.clip(label, path, 0.0, n))
                sound.append(doc.gap(n))
            continue
        dst = made / f"seg{i:02d}.mp4"
        say(f"otio: drawing {label} ...")
        _render_piece(r, tl, i, dst)
        out.rendered.append(str(dst))
        video.append(doc.clip(f"{label} (drawn)", dst, u0, n))
        has_sound = isinstance(seg, Clip) and not seg.mute or (getattr(seg, "source", None) is not None)
        sound.append(doc.clip(f"{label} (drawn) sound", dst, u0, n) if has_sound else doc.gap(n))

    def fill(items):
        if sum(int(x["source_range"]["duration"]["value"]) for x in items if "source_range" in x) < end:
            items.append(doc.gap(end - sum(int(x["source_range"]["duration"]["value"]) for x in items
                                           if "source_range" in x)))
        return items

    tracks = [doc.track("Main", "Video", fill(video))]

    # overlays, each drawn alone over transparency, on as few tracks as hold them
    spans = []
    for i, o in enumerate(tl.overlays):
        dst = made / f"layer{i:02d}.mov"
        say(f"otio: drawing overlays[{i}] ...")
        a, b = _render_layer(r, i, o, dst)
        out.rendered.append(str(dst))
        spans.append((F(a), F(b) - F(a), doc.clip(f"overlays[{i}] ({type(o).__name__.lower()})", dst, 0.0,
                                                   F(b) - F(a))))
    for k, tr in enumerate(_stack(spans)):
        tracks.append(doc.track(f"Overlays {k + 1}", "Video", _lay(doc, tr, end)))

    # sound
    tracks.append(doc.track("Footage sound", "Audio", fill(sound)))
    inset = [(F(o.at), F(o.until) - F(o.at), doc.clip(f"overlays[{i}] sound", resolve_path(root, o.path), o.start,
                                                     F(o.until) - F(o.at), meta={"volume_db": o.volume}))
             for i, o in enumerate(tl.overlays) if isinstance(o, Inset) and o.volume is not None]
    for k, tr in enumerate(_stack(inset)):
        tracks.append(doc.track(f"Picture-in-picture sound {k + 1}", "Audio", _lay(doc, tr, end)))
    if lines:
        said = [(F(a.at), F(secs), doc.clip(f"say {a.text[:40]!r}", Path(path), 0.0, F(secs)))
                for a, path, secs in lines]
        tracks.append(doc.track("Narration", "Audio", _lay(doc, said, end)))
    for a in tl.audio:
        if isinstance(a, Music):
            path = resolve_path(root, a.path)
            length = probe(path).seconds or total
            k, stop, beds = F(a.at), F(a.until if a.until is not None else total), []
            while k < stop:  # the bed loops: one clip per pass
                n = min(F(length), stop - k)
                beds.append((k, n, doc.clip(f"music {path.name}", path, 0.0, n, meta={"volume_db": a.volume})))
                k += n
            tracks.append(doc.track("Music", "Audio", _lay(doc, beds, end)))
    sounds = []
    for a in tl.audio:
        if isinstance(a, Sound):
            path = resolve_path(root, a.path)
            stop = a.end if a.end is not None else (probe(path).seconds or 0.0)
            n = min(F(stop - a.start), end - F(a.at))
            if n > 0:
                sounds.append((F(a.at), n, doc.clip(f"sound {path.name}", path, a.start, n,
                                                    meta={"volume_db": a.volume})))
    for k, tr in enumerate(_stack(sounds)):
        tracks.append(doc.track(f"Sounds {k + 1}", "Audio", _lay(doc, tr, end)))

    timeline = {"OTIO_SCHEMA": "Timeline.1", "name": stem, "global_start_time": None,
                "metadata": {"manimvox": {"edit": f"edits/{stem}", "size": list(tl.size), "fps": fps}},
                "tracks": {"OTIO_SCHEMA": "Stack.1", "name": "tracks", "children": tracks, "source_range": None,
                           "effects": [], "markers": [], "enabled": True, "color": None, "metadata": {}}}
    dst = Path(out.path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(timeline, indent=2) + "\n", encoding="utf-8")
    out.notes = notes + r.notes + [
        f"otio: {len(tracks)} tracks, {len(out.rendered)} piece(s) drawn by manimvox into {made.relative_to(root)}",
        ("otio: levels and ducking are not in the timeline: each clip plays at its own level (the gain manimvox "
         "uses is in its metadata), so compare with the rendered film's sound"),
    ]
    if any(isinstance(seg, Clip) and seg.speed != 1 for seg in tl.segments if _plain(seg)):
        out.notes.append("otio: speeds are LinearTimeWarp effects; check them in your editor, as some ignore them")
    if any(s.transition.kind == "dip" for s in tl.segments):
        out.notes.append("otio: dips are written as dissolves; OTIO has no dip through a colour")
    return out
