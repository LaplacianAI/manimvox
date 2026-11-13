"""Pictures for the renderer: reading video frames in order, fitting any frame to the output, and the layers drawn
over it. Everything is an (h, w, 3) or (h, w, 4) uint8 array at the size being rendered."""
from __future__ import annotations

import math
from pathlib import Path

import av
import numpy as np
from PIL import Image as PILImage

from .._cairo import hex_rgb, surface_rgba
from ..post.draw import _face, _rounded
from ..post.encode import decode_video
from .timeline import Text


class Reader:
    """The frames of a video file read forward: `at(s)` is the frame showing at `s` seconds of the file (the last
    one starting at or before it). It seeks on the first read and when asked to jump back or far ahead."""

    JUMP = 3.0  # seconds ahead beyond which a seek beats decoding through

    def __init__(self, path: Path):
        self.path = Path(path)
        self.c = av.open(str(path))
        self.s = self.c.streams.video[0]
        self.s.thread_type = "AUTO"
        self.width, self.height = self.s.codec_context.width, self.s.codec_context.height
        self._gen = None
        self.cur = self.nxt = None

    def _time(self, f) -> float:
        return float(f.pts * self.s.time_base) if f.pts is not None else 0.0

    def _seek(self, s: float) -> None:
        self.c.seek(max(0, int(s / self.s.time_base)), stream=self.s, backward=True, any_frame=False)
        self._gen = decode_video(self.c, self.s)
        self.cur, self.nxt = None, next(self._gen, None)

    def at(self, s: float) -> av.VideoFrame:
        if self._gen is None or (self.cur is not None and s < self._time(self.cur) - 1e-6) or (
                self.nxt is not None and s > self._time(self.nxt) + self.JUMP):
            self._seek(s)
        while self.nxt is not None and self._time(self.nxt) <= s + 1e-6:
            self.cur, self.nxt = self.nxt, next(self._gen, None)
        if self.cur is None:  # asked for a time before the first frame
            self.cur = self.nxt
        if self.cur is None:
            raise ValueError(f"{self.path.name} has no frame at {s:.2f} s")
        return self.cur

    def close(self) -> None:
        self.c.close()


def to_array(img, alpha: bool = False) -> np.ndarray:
    """A PIL image or array as uint8 RGB (or RGBA with `alpha`)."""
    if isinstance(img, PILImage.Image):
        img = img.convert("RGBA" if alpha else "RGB")
        return np.asarray(img)
    a = np.asarray(img)
    if a.dtype != np.uint8:
        a = np.clip(a, 0, 255).astype(np.uint8)
    if a.ndim == 2:
        a = np.repeat(a[..., None], 3, axis=2)
    if a.shape[2] == 4 and not alpha:
        return a[..., :3]
    if a.shape[2] == 3 and alpha:
        return np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
    return a


def resize(a: np.ndarray, w: int, h: int) -> np.ndarray:
    if a.shape[1] == w and a.shape[0] == h:
        return a
    mode = "RGBA" if a.shape[2] == 4 else "RGB"
    return np.asarray(PILImage.fromarray(a, mode).resize((max(1, w), max(1, h)), PILImage.Resampling.BILINEAR))


def _fit_size(sw: int, sh: int, w: int, h: int, cover: bool) -> tuple[int, int]:
    k = max(w / sw, h / sh) if cover else min(w / sw, h / sh)
    return max(2, round(sw * k)), max(2, round(sh * k))


def place(a: np.ndarray, w: int, h: int, bg: tuple[int, int, int], look=None) -> np.ndarray:
    """A picture already scaled to fit: centred on a `bg` canvas (contain) or cut to the frame (cover). `look`
    (an array function, such as a grade) changes the picture itself, never the background around it."""
    if look is not None:
        a = look(a)
    ph, pw = a.shape[:2]
    if a.shape[2] == 4:  # transparency over the background
        canvas = np.empty((ph, pw, 3), np.uint8)
        canvas[:] = bg
        blend(canvas, a, 0, 0)
        a = canvas
    if (pw, ph) == (w, h):
        return np.ascontiguousarray(a)
    out = np.empty((h, w, 3), np.uint8)
    out[:] = bg
    x0, y0 = (w - pw) // 2, (h - ph) // 2  # negative when the picture is larger: cut
    sx, sy = max(0, -x0), max(0, -y0)
    dx, dy = max(0, x0), max(0, y0)
    cw, ch = min(pw - sx, w - dx), min(ph - sy, h - dy)
    out[dy:dy + ch, dx:dx + cw] = a[sy:sy + ch, sx:sx + cw]
    return out


def fit_frame(frame: av.VideoFrame, w: int, h: int, fit: str, crop, bg, look=None) -> np.ndarray:
    """A decoded video frame at the output size: letterboxed (contain), filled (cover), or a region of it in the
    source's pixels (crop) scaled to fit. FFmpeg's scaler does the resizing."""
    if fit == "crop":
        x, y, cw, ch = (round(v) for v in crop)
        rgb = frame.to_ndarray(format="rgb24")[y:y + ch, x:x + cw]
        tw, th = _fit_size(rgb.shape[1], rgb.shape[0], w, h, cover=False)
        return place(resize(rgb, tw, th), w, h, bg, look)
    tw, th = _fit_size(frame.width, frame.height, w, h, cover=fit == "cover")
    return place(frame.reformat(width=tw, height=th, format="rgb24").to_ndarray(), w, h, bg, look)


def fit_array(a: np.ndarray, w: int, h: int, fit: str, bg, look=None) -> np.ndarray:
    """An image or a made frame (RGB or RGBA) at the output size, letterboxed or filled."""
    tw, th = _fit_size(a.shape[1], a.shape[0], w, h, cover=fit == "cover")
    return place(resize(a, tw, th), w, h, bg, look)


def blend(frame: np.ndarray, rgba: np.ndarray, x: int, y: int, opacity: float = 1.0) -> None:
    """Draw RGBA pixels onto an RGB frame at (x, y), in place, clipped to the frame."""
    if opacity <= 0:
        return
    H, W = frame.shape[:2]
    h, w = rgba.shape[:2]
    sx, sy = max(0, -x), max(0, -y)
    dx, dy = max(0, x), max(0, y)
    cw, ch = min(w - sx, W - dx), min(h - sy, H - dy)
    if cw <= 0 or ch <= 0:
        return
    src = rgba[sy:sy + ch, sx:sx + cw]
    region = frame[dy:dy + ch, dx:dx + cw]
    a = src[..., 3:4].astype(np.float32) * (opacity / 255.0)
    region[:] = (region * (1.0 - a) + src[..., :3] * a + 0.5).astype(np.uint8)


def mix(a: np.ndarray, b: np.ndarray, k: float) -> np.ndarray:
    """`a` crossfaded to `b` by k (0..1)."""
    if k <= 0:
        return a
    if k >= 1:
        return b
    return (a.astype(np.float32) * (1 - k) + b.astype(np.float32) * k + 0.5).astype(np.uint8)


def smooth(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def moving(canvas: np.ndarray, move: str | None, k: float, w: int, h: int) -> np.ndarray:
    """A slow move over a still, `k` (0..1) of the way through: push in, pull out, or pan left or right."""
    if move is None:
        return canvas
    z0, z1 = {"push": (1.0, 1.12), "pull": (1.12, 1.0)}.get(move, (1.1, 1.1))
    z = z0 + (z1 - z0) * smooth(k)
    cw, ch = canvas.shape[1] / z, canvas.shape[0] / z
    spare = canvas.shape[1] - cw
    x = {"left": spare * (1 - smooth(k)), "right": spare * smooth(k)}.get(move, spare / 2)
    y = (canvas.shape[0] - ch) / 2
    box = (x, y, x + cw, y + ch)
    img = PILImage.fromarray(canvas).resize((w, h), PILImage.Resampling.BILINEAR, box=box)
    return np.asarray(img)


# ---------------------------------------------------------------- text over the picture

def text_layer(o: Text, w: int, h: int, theme, scale: float = 1.0) -> tuple[int, int, np.ndarray]:
    """A lower third (bottom left: an accent bar, the text bold, `sub` muted under it), a title (centred, large)
    or a label (at `pos`), each on a plate of the theme's background. Returns x, y and the RGBA pixels."""
    import cairo

    size = h * {"lower-third": 0.046, "title": 0.075, "label": 0.032}[o.kind]
    sub_size = size * 0.68
    probe = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    _face(probe, theme, bold=True)
    probe.set_font_size(size)
    tw = probe.text_extents(o.text).x_advance
    sw = 0.0
    if o.sub:
        _face(probe, theme)
        probe.set_font_size(sub_size)
        sw = probe.text_extents(o.sub).x_advance
    pad = size * 0.5
    bar = size * 0.16 if o.kind == "lower-third" else 0.0
    pw = int(min(w, max(tw, sw) + 2 * pad + bar))
    ph = int(size * 1.35 + (sub_size * 1.4 if o.sub else 0) + pad)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, max(1, pw), max(1, ph))
    ctx = cairo.Context(surf)
    _rounded(ctx, pw, ph, size * 0.3)
    ctx.set_source_rgba(*hex_rgb(theme["bg"]), 0.86)
    ctx.fill()
    if bar:
        ctx.set_source_rgb(*hex_rgb(theme["accent"]))
        ctx.rectangle(0, 0, bar, ph)
        ctx.fill()
    _face(ctx, theme, bold=True)
    ctx.set_font_size(size)
    ctx.set_source_rgb(*hex_rgb(theme["ink"]))
    x0 = bar + pad if o.kind != "title" else (pw - tw) / 2
    ctx.move_to(x0, pad * 0.5 + size)
    ctx.show_text(o.text)
    if o.sub:
        _face(ctx, theme)
        ctx.set_font_size(sub_size)
        ctx.set_source_rgb(*hex_rgb(theme["muted"]))
        ctx.move_to(bar + pad if o.kind != "title" else (pw - sw) / 2, pad * 0.5 + size + sub_size * 1.45)
        ctx.show_text(o.sub)
    rgba = surface_rgba(surf)
    if o.kind == "lower-third":
        x, y = round(w * 0.05), round(h * 0.8 - ph)
    elif o.kind == "title":
        x, y = (w - pw) // 2, (h - ph) // 2
    else:
        x, y = round(o.pos[0] * scale), round(o.pos[1] * scale)
    return x, y, rgba


def fade_level(t: float, at: float, until: float | None, fade: float) -> float:
    """1 inside a layer's span, sloping in and out over `fade` seconds at its ends."""
    if fade <= 0:
        return 1.0
    k = min(1.0, (t - at) / fade)
    if until is not None:
        k = min(k, (until - t) / fade)
    return max(0.0, min(1.0, k))


def ceil_even(v: float) -> int:
    return max(2, 2 * math.ceil(v / 2))
