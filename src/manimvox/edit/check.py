"""`check edit`: an edit against its files, before anything is decoded. Every finding names the item and the
field, and says what is wrong in the item's own terms (seconds of the file, pixels of the frame)."""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from pathlib import Path

from .load import episode_video, frame_source, resolve_path, resolve_ref
from .probe import Media, MediaError, probe
from .timeline import (
    Clip,
    Draw,
    Frames,
    Image,
    Inset,
    Music,
    Picture,
    Say,
    Scene,
    Sound,
    Text,
    Timeline,
    Title,
    duration,
    place,
)

SLACK = 0.05  # seconds a time may run past a file's end: container lengths are rounded


@dataclass
class EditReport:
    findings: list[str] = field(default_factory=list)
    plan: list[str] = field(default_factory=list)  # where each segment lands on the output
    seconds: float = 0.0

    @property
    def ok(self) -> bool:
        return not self.findings


def _t(s: float) -> str:
    return f"{int(s // 60)}:{s % 60:05.2f}"


def _name(seg) -> str:
    if isinstance(seg, Clip):
        return f"episode {seg.episode}" if seg.episode is not None else f"clip {seg.path}"
    if isinstance(seg, Image):
        return f"image {seg.path}"
    if isinstance(seg, Title):
        return f"title {seg.text!r}"
    src = seg.source
    return f"frames {src if isinstance(src, str) else getattr(src, '__name__', type(src).__name__)}"


class _Media:
    """probe() once per file; a finding instead of an exception."""

    def __init__(self, root: Path, report: EditReport):
        self.root, self.report, self.seen = root, report, {}

    def get(self, where: str, path: str | Path, kinds: tuple[str, ...], what: str) -> Media | None:
        full = resolve_path(self.root, str(path)) if isinstance(path, str) else path
        if full not in self.seen:
            try:
                self.seen[full] = probe(full)
            except MediaError as e:
                self.seen[full] = e
        m = self.seen[full]
        if isinstance(m, MediaError):
            self.report.findings.append(f"{where}: {m}")
            return None
        if m.kind not in kinds and not ("audio" in kinds and m.audio):
            self.report.findings.append(f"{where}: {Path(full).name} is {m.kind}, not {what}")
            return None
        return m


def _hook(report: EditReport, root: Path, where: str, ref, kind: str):
    try:
        obj = resolve_ref(root, ref)
    except ValueError as e:
        report.findings.append(f"{where}: {e}")
        return None
    if kind == "class":
        if not isinstance(obj, type):
            report.findings.append(f"{where}: {ref} must name a Manim scene class")
            return None
    elif not callable(obj):
        report.findings.append(f"{where}: {ref} is not a function")
        return None
    return obj


def check_edit(root: Path, tl: Timeline) -> EditReport:
    root = Path(root)
    rep = EditReport()
    media = _Media(root, rep)
    W, H = tl.size
    lengths: list[float | None] = []
    for i, seg in enumerate(tl.segments):
        where = f"segments[{i}] ({_name(seg)})"
        length = None
        if isinstance(seg, Clip):
            if seg.episode is not None:
                try:
                    stem, path = episode_video(root, seg.episode)
                except Exception as e:  # noqa: BLE001 - a project or episode error, reported as a finding
                    rep.findings.append(f"{where}: {e}")
                    lengths.append(None)
                    continue
                if not path.is_file():
                    rep.findings.append(f"{where}: out/{stem}.mp4 is not rendered yet: manimvox render {stem}")
                    lengths.append(None)
                    continue
            else:
                path = seg.path
            m = media.get(where, path, ("video",), "a video")
            if m is not None:
                length = m.seconds
                if seg.start >= m.seconds:
                    rep.findings.append(f"{where}: start {seg.start:g} s is at or past the file's end "
                                        f"({m.seconds:.2f} s)")
                elif seg.end is not None and seg.end > m.seconds + SLACK:
                    rep.findings.append(f"{where}: end {seg.end:g} s is past the file's end ({m.seconds:.2f} s)")
                if seg.crop is not None:
                    x, y, w, h = seg.crop
                    if x + w > m.width + 0.5 or y + h > m.height + 0.5:
                        rep.findings.append(f"{where}: crop {list(seg.crop)} reaches outside the "
                                            f"{m.width}x{m.height} picture")
        elif isinstance(seg, Image):
            media.get(where, seg.path, ("image",), "an image")
        elif isinstance(seg, Frames):
            try:
                src = frame_source(root, seg.source)
                d = getattr(src, "duration", None)
                length = float(d) if d is not None else None
                if seg.seconds is None and length is None:
                    rep.findings.append(f"{where}: the source has no duration, so give seconds")
            except ValueError as e:
                rep.findings.append(f"{where}: {e}")
        for k, fx in enumerate(getattr(seg, "effects", ())):
            _hook(rep, root, f"{where}.effects[{k}]", fx, "function")
        lengths.append(length)

    placed = place(tl, lengths)
    for prev, p in itertools.pairwise(placed):
        if p.overlap and p.overlap > min(prev.seconds, p.seconds) + 1e-9:
            rep.findings.append(f"segments[{p.index}] ({_name(p.segment)}): its {p.segment.transition.kind} of "
                                f"{p.overlap:g} s is longer than it or the segment before it "
                                f"({min(prev.seconds, p.seconds):.2f} s)")
    total = duration(placed)
    rep.seconds = total
    rep.plan = [f"{_t(p.at)}-{_t(p.at + p.seconds)}  {_name(p.segment)}"
                + (f"  ({p.segment.transition.kind} {p.overlap:g} s)" if p.overlap else "") for p in placed]

    def inside(where: str, until: float | None) -> None:
        if until is not None and until > total + SLACK:
            rep.findings.append(f"{where}: until {until:g} s is past the film's end ({total:.2f} s)")

    def boxed(where: str, box, height: float | None) -> None:
        x, y, w = box
        h = height if height is not None else 0
        if x < 0 or y < 0 or x + w > W + 0.5 or y + h > H + 0.5:
            size = f"{w:g}x{h:.0f}" if height is not None else f"{w:g} wide"
            rep.findings.append(f"{where}: box {list(box)} ({size}) reaches outside the {W}x{H} frame")

    for i, o in enumerate(tl.overlays):
        where = f"overlays[{i}]"
        if isinstance(o, Picture):
            where += f" (image {o.path})"
            m = media.get(where, o.path, ("image",), "an image")
            inside(where, o.until)
            if m is not None:
                boxed(where, o.box, o.box[2] * m.height / m.width)
        elif isinstance(o, Inset):
            where += f" (clip {o.path})"
            m = media.get(where, o.path, ("video",), "a video")
            inside(where, o.until)
            if m is not None:
                boxed(where, o.box, o.box[2] * m.height / m.width)
                if o.start + (o.until - o.at) > m.seconds + SLACK:
                    rep.findings.append(f"{where}: showing {o.until - o.at:g} s from {o.start:g} s runs past the "
                                        f"file's end ({m.seconds:.2f} s)")
        elif isinstance(o, Text):
            where += f" (text {o.text!r})"
            inside(where, o.until)
            if o.pos is not None and not (0 <= o.pos[0] <= W and 0 <= o.pos[1] <= H):
                rep.findings.append(f"{where}: pos {list(o.pos)} is outside the {W}x{H} frame")
        elif isinstance(o, Draw):
            where += " (draw)"
            _hook(rep, root, where, o.fn, "function")
            inside(where, o.until)
            if o.box is not None:
                boxed(where, o.box, None)
        elif isinstance(o, Scene):
            where += " (scene)"
            _hook(rep, root, where, o.scene, "class")
            inside(where, o.until)
            if o.box is not None:
                boxed(where, o.box, None)
        if o.at >= total:
            rep.findings.append(f"{where}: at {o.at:g} s is at or past the film's end ({total:.2f} s)")

    for i, a in enumerate(tl.audio):
        where = f"audio[{i}]"
        if isinstance(a, Say):
            where += f" (say {a.text[:30]!r})"
        elif isinstance(a, Music):
            where += f" (music {a.path})"
            media.get(where, a.path, ("audio",), "sound")
            inside(where, a.until)
        elif isinstance(a, Sound):
            where += f" (sound {a.path})"
            m = media.get(where, a.path, ("audio",), "sound")
            if m is not None and a.start >= m.seconds:
                rep.findings.append(f"{where}: start {a.start:g} s is at or past the file's end ({m.seconds:.2f} s)")
            elif m is not None and a.end is not None and a.end > m.seconds + SLACK:
                rep.findings.append(f"{where}: end {a.end:g} s is past the file's end ({m.seconds:.2f} s)")
        if a.at >= total:
            rep.findings.append(f"{where}: at {a.at:g} s is at or past the film's end ({total:.2f} s)")
    return rep
