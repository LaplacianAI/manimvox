"""Frames from Pillow or numpy (`from_frames`), from pycairo (`from_cairo`), one image (`still`), a screenshot
file (`screenshot`) and a screen recording (`from_video`)."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .clip import DEFAULT_WIDTH, MAX_FRAMES, Clip, SceneError, VideoFrames, png


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
               max_width: int = 1280, sound: bool = False, volume: float = 0.0) -> Clip:
    """A recording (MP4, WebM, MOV) from `start` to `end` seconds as a Clip of `fps` frames a second, of any
    length: frames are read from the file as they are shown, not held in memory. Frames wider than `max_width`
    pixels are scaled down, but positions stay in the recording's own pixels. Play it with `clip.play()`, which
    runs at the recording's speed by default.

    `sound=True` keeps the recording's sound: it is heard whenever the clip plays, levelled to the project's
    loudness and `volume` dB from there, sped up or slowed with the clip (its pitch kept). Do not narrate over a
    clip that speaks. A looped clip is silent."""
    import hashlib

    import av

    p = _open(path)
    with av.open(str(p)) as box:
        if not box.streams.video:
            raise SceneError(f"{p.name} has no picture")
        stream = box.streams.video[0]
        size = (stream.codec_context.width, stream.codec_context.height)
        length = float(stream.duration * stream.time_base) if stream.duration else (box.duration or 0) / 1e6
        has_sound = bool(box.streams.audio)
    stop = min(end, length) if end is not None and length else (end if end is not None else length)
    count = round((stop - start) * fps) if stop else 0
    if start < 0 or count < 1:
        raise SceneError(f"{path} has no frames between {start:g} s and {'its end' if end is None else f'{end:g} s'}")
    if sound and not has_sound:
        raise SceneError(f"{p.name} has no sound; leave out sound=True")
    scaled = size if size[0] <= max_width else (max_width, 2 * round(size[1] * max_width / size[0] / 2))
    st = p.stat()
    digest = hashlib.sha256(f"{p.resolve()}|{st.st_size}|{st.st_mtime_ns}|{start}|{stop}|{fps}|{scaled}".encode()
                            ).hexdigest()
    frames = VideoFrames(p.resolve(), start, count, fps, scaled, digest)
    return Clip(frames, fps, width, space=size, sound=(str(p.resolve()), float(start), float(volume)) if sound else None)
