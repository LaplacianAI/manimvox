"""A Clip: frames from another library, placed on the stage and played against narration."""
from __future__ import annotations

import hashlib
import io
from collections.abc import Sequence

import numpy as np
from manim import Animation, ImageMobject, linear, smooth
from PIL import Image

DEFAULT_WIDTH = 9.6  # scene units: three quarters of the safe stage's width
MAX_FRAMES = 3600  # two minutes at 30 fps; frames are held in memory as PNG bytes
ZOOM_PAD = 0.15  # a zoom leaves this fraction of the region's size as margin on each side


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
    Its width is set in scene units, so a draft and a final render place it the same.

    Positions on a clip are pixels of its source, counted from the top left. `space` is the source's size when
    the frames were scaled down from it, so positions read off the original screenshot or recording still hold."""

    def __init__(self, frames: Sequence[bytes], fps: float, width: float = DEFAULT_WIDTH,
                 space: tuple[float, float] | None = None, **kwargs):
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
        self.space = (float((space or self.pixels)[0]), float((space or self.pixels)[1]))
        self.view = self.whole  # the part of the source shown: x, y, w, h in `space`
        self.fps = float(fps)
        # Manim's play cache writes each bytes value as its type name, so frames 1..n would never reach the
        # key; this digest does, and a changed frame re-renders instead of reusing a stale partial movie.
        self.frames_digest = hashlib.sha256(b"".join(hashlib.sha256(f).digest() for f in frames)).hexdigest()
        self._shown = (0, self.view)
        super().__init__(self._decode(0), **kwargs)
        self.scale_to_fit_width(width)  # an ImageMobject's own size depends on the render's resolution

    @property
    def seconds(self) -> float:
        return len(self.frames) / self.fps

    @property
    def whole(self) -> tuple[float, float, float, float]:
        return (0.0, 0.0, *self.space)

    @property
    def shown(self) -> int:
        """The index of the frame on screen."""
        return self._shown[0]

    def _decode(self, i: int) -> np.ndarray:
        img = Image.open(io.BytesIO(self.frames[i])).convert("RGBA")
        if self.view != self.whole:  # crop the view out of the frame and fill the clip with it
            kx, ky = self.pixels[0] / self.space[0], self.pixels[1] / self.space[1]
            x, y, w, h = self.view
            img = img.resize(self.pixels, Image.Resampling.BICUBIC, box=(x * kx, y * ky, (x + w) * kx, (y + h) * ky))
        return np.asarray(img)

    def show(self, i: int) -> Clip:
        """Display frame `i` (a negative index counts from the end)."""
        i = range(len(self.frames))[i]
        if (i, self.view) != self._shown:
            self.pixel_array = self._decode(i)
            self._shown = (i, self.view)
        return self

    def at(self, x: float, y: float) -> np.ndarray:
        """The scene point over pixel (x, y) of the source, counted from the top left: where to put a label
        or an arrow tip on what the clip shows. It follows the clip when it moves, scales or zooms."""
        vx, vy, vw, vh = self.view
        u, v = (x - vx) / vw, (y - vy) / vh
        return self.get_center() + np.array([(u - 0.5) * self.width, (0.5 - v) * self.height, 0.0])

    def visible(self, x: float, y: float, w: float, h: float) -> tuple[float, float, float, float] | None:
        """The part of region (x, y, w, h) inside the current view, or None when none of it is."""
        vx, vy, vw, vh = self.view
        x0, y0, x1, y1 = max(x, vx), max(y, vy), min(x + w, vx + vw), min(y + h, vy + vh)
        return (x0, y0, x1 - x0, y1 - y0) if x1 > x0 and y1 > y0 else None

    def framing(self, x: float, y: float, w: float, h: float, pad: float = ZOOM_PAD) -> tuple[float, ...]:
        """The view that shows region (x, y, w, h) with a margin, in the clip's own shape and inside the source."""
        sw, sh = self.space
        if not (w > 0 and h > 0 and x < sw and y < sh and x + w > 0 and y + h > 0):
            raise SceneError(f"region ({x:g}, {y:g}, {w:g}, {h:g}) is not inside the {sw:g}x{sh:g} source")
        cx, cy = x + w / 2, y + h / 2
        w, h = w * (1 + 2 * pad), h * (1 + 2 * pad)
        w = min(sw, max(w, h * sw / sh))
        h = w * sh / sw
        cx, cy = min(max(cx, w / 2), sw - w / 2), min(max(cy, h / 2), sh - h / 2)
        return (cx - w / 2, cy - h / 2, w, h)

    def zoom(self, x: float, y: float, w: float, h: float, pad: float = ZOOM_PAD, **kwargs) -> Zoom:
        """The animation that zooms into region (x, y, w, h) of the source inside the clip's own frame, so the
        clip never grows past its place on the stage. Make overlays after it: they point at the zoomed picture."""
        return Zoom(self, self.framing(x, y, w, h, pad), **kwargs)

    def zoom_out(self, **kwargs) -> Zoom:
        """The animation back to the whole picture."""
        return Zoom(self, self.whole, **kwargs)

    def loop(self) -> Clip:
        """Keep playing the frames, over and over, under whatever the scene plays or waits next (a model
        turning while the narration goes on). `clip.clear_updaters()` stops it on the frame it shows."""
        self._looped = 0.0

        def step(m, dt):
            m._looped += dt
            m.show(int(m._looped * m.fps) % len(m.frames))

        self.add_updater(step)
        return self

    def play(self, run_time: float | None = None, start: float = 0.0, end: float | None = None,
             **kwargs) -> PlayClip:
        """The animation that runs through the frames from `start` to `end` seconds of the clip (default: all of
        it) over `run_time` seconds (default: that stretch's own length, so a recording plays at real speed).
        Play one recording in parts, one part per narrated line."""
        return PlayClip(self, run_time=run_time, start=start, end=end, **kwargs)


class PlayClip(Animation):
    """Steps a Clip through its frames from `start` to `end` seconds, stretched or squeezed to the run time."""

    def __init__(self, clip: Clip, run_time: float | None = None, start: float = 0.0, end: float | None = None,
                 rate_func=linear, **kwargs):
        if not isinstance(clip, Clip):
            raise SceneError(f"PlayClip plays a Clip, got {type(clip).__name__}")
        end = clip.seconds if end is None else end
        if not 0 <= start < end <= clip.seconds + 1e-9:
            raise SceneError(f"start and end must satisfy 0 <= start < end <= {clip.seconds:g} s (the clip's "
                             f"length), got {start:g} and {end:g}")
        self.first, self.last = int(start * clip.fps), min(len(clip.frames), round(end * clip.fps))
        super().__init__(clip, run_time=run_time or end - start, rate_func=rate_func, **kwargs)

    def interpolate_mobject(self, alpha: float) -> None:
        n = max(1, self.last - self.first)
        self.mobject.show(min(len(self.mobject.frames) - 1, self.first + min(n - 1, int(alpha * n))))


class Zoom(Animation):
    """Moves a Clip's view to `target` (x, y, w, h in its source's pixels). The size changes geometrically and
    the centre moves in step with it, so a deep zoom feels as steady at the end as at the start."""

    def __init__(self, clip: Clip, target: tuple[float, ...], run_time: float = 1.2, rate_func=smooth, **kwargs):
        if not isinstance(clip, Clip):
            raise SceneError(f"Zoom moves a Clip, got {type(clip).__name__}")
        self.target = tuple(float(v) for v in target)
        super().__init__(clip, run_time=run_time, rate_func=rate_func, **kwargs)

    def begin(self) -> None:
        self.start = self.mobject.view
        super().begin()

    def interpolate_mobject(self, alpha: float) -> None:
        (x0, y0, w0, h0), (x1, y1, w1, h1) = self.start, self.target
        w = w0 * (w1 / w0) ** alpha
        k = (w - w0) / (w1 - w0) if abs(w1 - w0) > 1e-9 else alpha
        cx = x0 + w0 / 2 + k * (x1 + w1 / 2 - x0 - w0 / 2)
        cy = y0 + h0 / 2 + k * (y1 + h1 / 2 - y0 - h0 / 2)
        h = w * h0 / w0
        sw, sh = self.mobject.space
        if alpha >= 1:  # land exactly on the target: zoom_out ends on the whole picture, uncropped
            self.mobject.view = self.target
        else:  # rounding can put an edge a hair outside the source (-1e-13), which the crop refuses
            self.mobject.view = (min(max(cx - w / 2, 0.0), sw - w), min(max(cy - h / 2, 0.0), sh - h), w, h)
        self.mobject.show(self.mobject.shown)
