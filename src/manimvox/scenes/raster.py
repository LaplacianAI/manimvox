"""Frames from Pillow or numpy (`from_frames`), from pycairo (`from_cairo`), one image (`still`), a screenshot
file (`screenshot`) and a screen recording (`from_video`)."""
from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

from .clip import DEFAULT_WIDTH, MAX_FRAMES, Clip, SceneError, png


def frame_count(seconds: float, fps: float) -> int:
    if not (seconds > 0 and fps > 0):
        raise SceneError(f"seconds and fps must be greater than 0, got {seconds} and {fps}")
    n = max(1, round(seconds * fps))
    if n > MAX_FRAMES:
        raise SceneError(f"{n} frames is more than {MAX_FRAMES}; lower fps or split the clip")
    return n


def from_frames(draw: Callable[[float], object], seconds: float, fps: float = 15,
                width: float = DEFAULT_WIDTH) -> Clip:
    """`draw(t)` returns the frame at t seconds as a PIL image or an (h, w, 3|4) uint8 array, every frame one size."""
    return Clip([png(draw(i / fps)) for i in range(frame_count(seconds, fps))], fps, width)


def from_cairo(draw: Callable, seconds: float, fps: float = 15, size: tuple[int, int] = (1280, 720),
               width: float = DEFAULT_WIDTH) -> Clip:
    """`draw(ctx, t, w, h)` paints the frame at t seconds on a fresh, transparent canvas of `size` pixels."""
    import cairo

    from .._cairo import surface_rgba

    w, h = size
    frames = []
    for i in range(frame_count(seconds, fps)):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        draw(cairo.Context(surf), i / fps, w, h)
        frames.append(png(surface_rgba(surf)))
    return Clip(frames, fps, width)


def still(image, width: float = DEFAULT_WIDTH) -> Clip:
    """One image (PIL or array) as a one-frame Clip, sized in scene units like every clip."""
    return Clip([png(image)], 1, width)


def _open(path) -> Path:
    p = Path(path)
    if not p.is_file():
        raise SceneError(f"{p} not found (a relative path is read from the project folder)")
    return p


def screenshot(path, width: float = DEFAULT_WIDTH) -> Clip:
    """A screenshot file (PNG, JPEG, WebP) as a one-frame Clip. Positions on it (`at`, `zoom`, the overlays in
    manimvox.scenes) are the image's own pixels, so read them off the file."""
    from PIL import Image

    with Image.open(_open(path)) as img:
        return Clip([png(img)], 1, width)


def from_video(path, fps: float = 15, start: float = 0.0, end: float | None = None, width: float = DEFAULT_WIDTH,
               max_width: int = 1280) -> Clip:
    """A screen recording (MP4, WebM, MOV) from `start` to `end` seconds as a Clip of `fps` frames a second.
    Frames wider than `max_width` pixels are scaled down to save memory, but positions stay in the recording's
    own pixels. Play it with `clip.play()`, which runs at the recording's speed by default."""
    import av
    from PIL import Image

    with av.open(str(_open(path))) as box:
        stream = box.streams.video[0]
        size = (stream.codec_context.width, stream.codec_context.height)
        length = float(stream.duration * stream.time_base) if stream.duration else (box.duration or 0) / 1e6
        stop = min(end, length) if end is not None and length else (end if end is not None else length)
        if start > 0:
            box.seek(int(start / stream.time_base), stream=stream, backward=True)
        frames, last = [], None  # frames[k] is what the recording shows at start + k / fps
        for frame in box.decode(stream):
            t = float(frame.time or 0.0)
            if stop and t >= stop - 1e-6:
                break
            k = math.floor((t - start) * fps + 1e-6)  # the clip frame this recording frame falls in
            if k < len(frames):  # more frames a second than the clip needs, or before `start`
                continue
            while last is not None and len(frames) < k:  # a gap in the recording: hold the frame before it
                frames.append(last)
            img = frame.to_image()
            if img.width > max_width:
                img = img.resize((max_width, round(img.height * max_width / img.width)), Image.Resampling.LANCZOS)
            last = png(img)
            frames.append(last)
            if len(frames) > MAX_FRAMES:
                raise SceneError(f"more than {MAX_FRAMES} frames; lower fps or pass start and end")
        while last is not None and len(frames) < round((stop - start) * fps):  # the last frame lasts to the end
            frames.append(last)
    if not frames:
        raise SceneError(f"{path} has no frames between {start:g} s and {'its end' if end is None else f'{end:g} s'}")
    return Clip(frames, fps, width, space=size)
