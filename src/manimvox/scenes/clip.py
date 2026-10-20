"""A Clip: frames from another library, placed on the stage and played against narration."""
from __future__ import annotations

import hashlib
import io
from collections.abc import Sequence

import numpy as np
from manim import Animation, ImageMobject, linear
from PIL import Image

DEFAULT_WIDTH = 9.6  # scene units: three quarters of the safe stage's width
MAX_FRAMES = 3600  # two minutes at 30 fps; frames are held in memory as PNG bytes


class SceneError(Exception):
    """An adapter could not turn its input into frames."""


def rgba(img) -> np.ndarray:
    """A PIL image or an (h, w, 3|4) uint8 array as an (h, w, 4) uint8 array."""
    if isinstance(img, Image.Image):
        return np.asarray(img.convert("RGBA"))
    a = np.asarray(img)
    if a.dtype != np.uint8 or a.ndim != 3 or a.shape[2] not in (3, 4):
        raise SceneError(f"a frame must be a PIL image or an (h, w, 3|4) uint8 array, got {a.dtype} {a.shape}")
    if a.shape[2] == 3:
        a = np.concatenate([a, np.full(a.shape[:2] + (1,), 255, np.uint8)], axis=2)
    return a


def png(img) -> bytes:
    """One frame as PNG bytes (lossless, fast compression)."""
    buf = io.BytesIO()
    Image.fromarray(rgba(img), "RGBA").save(buf, format="PNG", compress_level=1)
    return buf.getvalue()


class Clip(ImageMobject):
    """Frames on the stage. Move and scale it like any mobject; `self.play(clip.play(), run_time=...)` plays it.
    Its width is set in scene units, so a draft and a final render place it the same."""

    def __init__(self, frames: Sequence[bytes], fps: float, width: float = DEFAULT_WIDTH, **kwargs):
        frames = list(frames)
        if not frames:
            raise SceneError("a clip needs at least one frame")
        if len(frames) > MAX_FRAMES:
            raise SceneError(f"{len(frames)} frames is more than {MAX_FRAMES}; lower fps or split the clip")
        if not fps > 0:
            raise SceneError(f"fps must be greater than 0, got {fps}")
        sizes = {Image.open(io.BytesIO(f)).size for f in frames}  # reads the headers only
        if len(sizes) > 1:
            raise SceneError(f"every frame must be the same size, got {sorted(sizes)}")
        self.frames = frames
        self.pixels = sizes.pop()  # (width, height) of every frame
        self.fps = float(fps)
        # Manim's play cache writes each bytes value as its type name, so frames 1..n would never reach the
        # key; this digest does, and a changed frame re-renders instead of reusing a stale partial movie.
        self.frames_digest = hashlib.sha256(b"".join(hashlib.sha256(f).digest() for f in frames)).hexdigest()
        self._shown = 0
        super().__init__(self._decode(0), **kwargs)
        self.scale_to_fit_width(width)  # an ImageMobject's own size depends on the render's resolution

    @property
    def seconds(self) -> float:
        return len(self.frames) / self.fps

    def _decode(self, i: int) -> np.ndarray:
        return np.asarray(Image.open(io.BytesIO(self.frames[i])).convert("RGBA"))

    def show(self, i: int) -> Clip:
        """Display frame `i` (a negative index counts from the end)."""
        i = range(len(self.frames))[i]
        if i != self._shown:
            self.pixel_array = self._decode(i)
            self._shown = i
        return self

    def at(self, x: float, y: float) -> np.ndarray:
        """The scene point over pixel (x, y) of the frames, counted from the top left: where to put a label
        or an arrow tip on what the clip shows. It follows the clip when it moves or scales."""
        w, h = self.pixels
        return self.get_center() + np.array([(x / w - 0.5) * self.width, (0.5 - y / h) * self.height, 0.0])

    def loop(self) -> Clip:
        """Keep playing the frames, over and over, under whatever the scene plays or waits next (a model
        turning while the narration goes on). `clip.clear_updaters()` stops it on the frame it shows."""
        self._looped = 0.0

        def step(m, dt):
            m._looped += dt
            m.show(int(m._looped * m.fps) % len(m.frames))

        self.add_updater(step)
        return self

    def play(self, run_time: float | None = None, **kwargs) -> PlayClip:
        """The animation that runs through every frame over `run_time` seconds (default: the clip's own length)."""
        return PlayClip(self, run_time=run_time, **kwargs)


class PlayClip(Animation):
    """Steps a Clip through its frames, stretched or squeezed to the animation's run time."""

    def __init__(self, clip: Clip, run_time: float | None = None, rate_func=linear, **kwargs):
        if not isinstance(clip, Clip):
            raise SceneError(f"PlayClip plays a Clip, got {type(clip).__name__}")
        super().__init__(clip, run_time=run_time or clip.seconds, rate_func=rate_func, **kwargs)

    def interpolate_mobject(self, alpha: float) -> None:
        n = len(self.mobject.frames)
        self.mobject.show(min(n - 1, int(alpha * n)))
