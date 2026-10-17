"""Frames from Pillow or numpy (`from_frames`), from pycairo (`from_cairo`), and one image (`still`)."""
from __future__ import annotations

from collections.abc import Callable

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
