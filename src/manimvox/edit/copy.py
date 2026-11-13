"""The picture copied, not re-encoded: for an edit that is one untouched clip, the film's video is the clip's own
packets, so it keeps the camera's quality and renders in seconds. The sound is still mixed and encoded.

Why so narrow: an MP4 track carries one set of H.264 (or HEVC) parameters. Packets from another encoder decode
against the wrong ones without any error, as a wrong picture, so copied and re-encoded video cannot share a file.
Copying is therefore all or nothing, and only when nothing would change the picture: one clip at one speed, at
the film's size and frame rate, with no crop, fill, grade, stabilisation, effect, overlay or burned-in captions,
starting on a keyframe and ending on one (or at the file's end). After writing, the copy is decoded and its
frames counted; anything amiss and the caller encodes the film instead.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import av
import numpy as np

from ..post.audio import RATE
from ..post.encode import FASTSTART
from .load import source_path
from .timeline import Clip, Grade, Timeline

CODECS = ("h264", "hevc")
CHUNK = 30.0  # seconds of sound mixed and written at a time


def _keyframes(path: Path) -> list[float]:
    """The times (seconds of the file) of its video's keyframes, read from the packets without decoding."""
    with av.open(str(path)) as c:
        s = c.streams.video[0]
        return sorted(float(p.pts * s.time_base) for p in c.demux(s) if p.size and p.is_keyframe and p.pts is not None)


def copyable(root: Path, tl: Timeline, lengths) -> tuple[Path | None, str]:
    """(the clip's file, "") when the film's picture can be copied, else (None, why not)."""
    if len(tl.segments) != 1 or not isinstance(tl.segments[0], Clip):
        return None, "the film is more than one clip"
    seg = tl.segments[0]
    changed = [what for what, yes in (
        ("a speed change", seg.speed != 1.0), ("a fill or crop", seg.fit != "contain" or seg.crop is not None),
        ("a grade", seg.grade is not None and seg.grade != Grade()), ("stabilisation", seg.stabilize is not None),
        ("effects", bool(seg.effects)), ("overlays", bool(tl.overlays)), ("burned-in captions", tl.captions == "burn"),
    ) if yes]
    if changed:
        return None, f"the picture is changed ({', '.join(changed)})"
    path = source_path(root, seg)
    with av.open(str(path)) as c:
        s = c.streams.video[0]
        name, size = s.codec_context.name, (s.codec_context.width, s.codec_context.height)
        rate = float(s.average_rate or 0)
    if name not in CODECS:
        return None, f"{path.name} is {name}, not H.264 or HEVC"
    if size != tuple(tl.size):
        return None, f"{path.name} is {size[0]}x{size[1]}, the film {tl.size[0]}x{tl.size[1]}"
    if abs(rate - tl.fps) > 0.01:
        return None, f"{path.name} is {rate:g} fps, the film {tl.fps:g}"
    keys = _keyframes(path)
    half = 0.5 / tl.fps
    if not any(abs(k - seg.start) < half for k in keys):
        near = min(keys, key=lambda k: abs(k - seg.start)) if keys else 0.0
        return None, f"it starts at {seg.start:g} s, not on a keyframe (the nearest is {near:.3f} s)"
    length = lengths[0]
    at_end = seg.end is None or (length is not None and seg.end >= length - half)
    if not at_end and not any(abs(k - seg.end) < half for k in keys):
        return None, f"it ends at {seg.end:g} s, neither on a keyframe nor at the file's end"
    return path, ""


def write_copied(r, src: Path, dst: Path, start: float, end: float | None, frames: int) -> bool:
    """The film to `dst`: `src`'s video packets from `start` up to `end`, and the mix `r.mix` gives, as AAC.
    True if the copy decodes to exactly `frames` frames; otherwise `dst` is removed and False returned."""
    out = av.open(str(dst), "w", options=FASTSTART)
    try:
        with av.open(str(src)) as c:
            vin = c.streams.video[0]
            vout = out.add_stream_from_template(vin)
            aout = out.add_stream("aac", rate=RATE, layout="stereo")
            aout.bit_rate = 192_000
            tb = vin.time_base
            s0 = round(start / tb)
            stop = None if end is None else round(end / tb)
            started = False
            sound_to, written, total = 0.0, 0, r.total
            for p in c.demux(vin):
                if p.pts is None or not p.size:
                    continue
                if not started:  # from the keyframe at `start`; the GOP before it is not needed
                    if not (p.is_keyframe and p.pts >= s0 - 1):
                        continue
                    started, s0 = True, p.pts
                elif stop is not None and p.is_keyframe and p.pts >= stop - 1:
                    break  # the next GOP: everything shown before `end` has been sent
                t = float((p.pts - s0) * tb)
                while sound_to < min(total, t + 1.0):  # sound kept a little ahead of the picture
                    nxt = min(total, sound_to + CHUNK)
                    written = _audio(out, aout, r.mix(sound_to, nxt), written)
                    sound_to = nxt
                # times from the keyframe's display time, so the picture starts with the sound; a decode time
                # before it (a B-frame's delay) goes below zero, which the MP4 muxer keeps in an edit list
                dts = p.dts if p.dts is not None else p.pts
                p.pts, p.dts = p.pts - s0, dts - s0
                p.stream = vout
                out.mux(p)
            while sound_to < total:
                nxt = min(total, sound_to + CHUNK)
                written = _audio(out, aout, r.mix(sound_to, nxt), written)
                sound_to = nxt
            for p in aout.encode():
                out.mux(p)
    except BaseException:
        out.close()
        dst.unlink(missing_ok=True)
        raise
    out.close()
    try:
        with av.open(str(dst)) as c:
            got = sum(1 for _ in c.decode(video=0))
    except av.error.FFmpegError:
        got = -1
    if got != frames:
        dst.unlink(missing_ok=True)
        return False
    return True


def _audio(out, stream, x: np.ndarray, written: int) -> int:
    for i in range(0, x.shape[1], 1024):
        chunk = np.ascontiguousarray(x[:, i:i + 1024], np.float32)
        fr = av.AudioFrame.from_ndarray(chunk, format="fltp", layout="stereo")
        fr.sample_rate, fr.pts, fr.time_base = RATE, written, Fraction(1, RATE)
        written += chunk.shape[1]
        for p in stream.encode(fr):
            out.mux(p)
    return written
