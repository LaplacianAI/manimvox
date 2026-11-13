"""Edit your own footage into a finished video: cut, join, lay pictures, text, graphics and Manim scenes over it,
and mix its sound with narration and music.

An edit is `edits/<name>.json`, or `edits/<name>.py` that sets `timeline`:

    from manimvox.edit import Clip, Draw, Say, Text, Timeline, Title

    timeline = Timeline(
        segments=[Title("Setting up the board"), Clip("footage/take2.mp4", start=3.2, end=41, transition="fade")],
        overlays=[Text("Ada Lovelace", at=4, until=8, sub="Engineer")],
        audio=[Say("First, we flash the firmware.", at=5)],
    )

Any layer can be code: `Frames(source)` for a segment made by code (a MoviePy clip, or `frames(fn, seconds)`), `Draw(fn, ...)` for graphics drawn each frame, `Scene(cls, ...)` for a Manim scene over
the footage, and `effects=[fn, ...]` on a segment to change every frame (a blur, a vignette). `grade=Grade(...)` grades a
segment's colour: exposure, white balance, contrast, saturation, lift, gamma and gain, and a `.cube` LUT.
"""
from __future__ import annotations

from collections.abc import Callable

import numpy as np

from .timeline import (
    Audio,
    Clip,
    Draw,
    Frames,
    Grade,
    Image,
    Inset,
    Key,
    Multicam,
    Music,
    Overlay,
    Picture,
    Say,
    Scene,
    Segment,
    Sound,
    Stabilize,
    Text,
    Timeline,
    Title,
    Transition,
)


class FrameSource:
    """Frames made by `fn(t)` for `duration` seconds: a PIL image or an (h, w, 3|4) uint8 array each, one size.
    `sound`, if given, is float stereo samples, shape (2, n), at `rate` Hz."""

    def __init__(self, fn: Callable[[float], object], duration: float, sound: np.ndarray | None = None,
                 rate: int = 48000):
        if not callable(fn):
            raise ValueError(f"frames needs a function of t, got {fn!r}")  # noqa: TRY004 - edit errors are ValueError
        if not (duration and duration > 0):
            raise ValueError(f"frames needs a duration above 0, got {duration!r}")
        self.fn, self.duration, self.sound, self.rate = fn, float(duration), sound, rate

    def get_frame(self, t: float):
        return self.fn(t)

    def audio(self, rate: int) -> np.ndarray | None:
        if self.sound is None:
            return None
        if rate == self.rate:
            return self.sound
        n = round(self.sound.shape[1] * rate / self.rate)
        x = np.linspace(0, self.sound.shape[1] - 1, n)
        return np.stack([np.interp(x, np.arange(self.sound.shape[1]), ch) for ch in self.sound]).astype(np.float32)


def frames(fn: Callable[[float], object], seconds: float, sound: np.ndarray | None = None,
           rate: int = 48000) -> FrameSource:
    """A segment's worth of frames from code: `fn(t)` returns the frame at t seconds."""
    return FrameSource(fn, seconds, sound, rate)


class MoviePySource(FrameSource):
    """A MoviePy clip (or effect chain or composite) as a frame source, its mask kept as transparency and its
    sound kept."""

    def __init__(self, clip):
        if not (hasattr(clip, "get_frame") and getattr(clip, "duration", None)):
            raise ValueError(f"from_moviepy needs a MoviePy clip with a duration, got {clip!r}")
        self.clip = clip
        super().__init__(self._frame, clip.duration)

    def _frame(self, t: float) -> np.ndarray:
        rgb = np.asarray(self.clip.get_frame(t))
        if rgb.dtype != np.uint8:
            rgb = np.clip(rgb, 0, 255).astype(np.uint8)
        mask = getattr(self.clip, "mask", None)
        if mask is None:
            return rgb
        a = np.asarray(mask.get_frame(t), dtype=np.float32)
        return np.dstack([rgb[..., :3], np.clip(a * 255, 0, 255).astype(np.uint8)])

    def audio(self, rate: int) -> np.ndarray | None:
        a = getattr(self.clip, "audio", None)
        if a is None:
            return None
        arr = np.asarray(a.to_soundarray(fps=rate), dtype=np.float32)
        arr = arr.reshape(-1, 1) if arr.ndim == 1 else arr
        if arr.shape[1] == 1:
            arr = np.repeat(arr, 2, axis=1)
        return arr[:, :2].T.copy()


def from_moviepy(clip) -> MoviePySource:
    """A MoviePy clip as a frame source: a `Frames` segment, or a layer with `Draw(source.get_frame, ...)`.
    MoviePy is not a manimvox extra: its 2.2 release pins Pillow below 12, which would hold every install back.
    Install it beside manimvox (pip install moviepy) when you want it; any clip with get_frame works."""
    return MoviePySource(clip)


__all__ = ["Audio", "Clip", "Draw", "FrameSource", "Frames", "Grade", "Image", "Inset", "Key", "MoviePySource", "Multicam", "Music", "Overlay",
           "Picture", "Say", "Scene", "Segment", "Sound", "Stabilize", "Text", "Timeline", "Title", "Transition", "frames",
           "from_moviepy"]
