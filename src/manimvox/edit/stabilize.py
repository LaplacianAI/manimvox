"""Stabilisation: shaky footage held steady, in two passes.

1. **Measure** (`measure`): each frame is compared with the one before on a small grey copy. A grid of patches is
   matched by phase correlation, and a shift and a turn are fitted to the patches' movements, ignoring patches
   that disagree (something moving in the scene). Summed, these give the camera's path. The path is cached in
   build/edit/stab/, keyed by the file and the span, so later renders and drafts skip this pass.
2. **Correct** (`Steady`): the path is smoothed over `smooth` seconds, which keeps slow, intended moves such as a
   pan, and each frame is moved and turned by the difference between the smoothed path and the real one. It is
   zoomed in just enough that the moving edges stay outside the frame.

Moves are kept as fractions of the frame's width (shifts) and radians (turns), so one measurement serves any
output size, crop or draft.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import av
import numpy as np
from PIL import Image as PILImage

from ..post.encode import decode_video
from .timeline import Stabilize

WIDTH = 480  # px: frames are measured at this width
PATCH = 64  # px: the side of each matched patch
GRID = (5, 3)  # patches across and down
VERSION = 1  # of the cached measurements: bump when measuring changes
MAX_ZOOM = 1.5


@dataclass(frozen=True)
class CameraPath:
    """The camera's path through a span of a file: at `times` (seconds of the file), the summed shift `x`, `y`
    (fractions of the frame's width) and turn `a` (radians), and the frame's `aspect` (height over width)."""
    times: np.ndarray
    x: np.ndarray
    y: np.ndarray
    a: np.ndarray
    aspect: float


# ---------------------------------------------------------------- measuring

def _window() -> np.ndarray:
    w = np.hanning(PATCH)
    return np.outer(w, w).astype(np.float32)


def _patches(grey: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The grid's patches of a grey frame, windowed, and their centres (x, y) in its pixels."""
    h, w = grey.shape
    xs = np.linspace(PATCH / 2, w - PATCH / 2, GRID[0] + 2)[1:-1]
    ys = np.linspace(PATCH / 2, h - PATCH / 2, GRID[1] + 2)[1:-1]
    win, out, centres = _window(), [], []
    for cy in ys:
        for cx in xs:
            x0, y0 = round(cx - PATCH / 2), round(cy - PATCH / 2)
            p = grey[y0:y0 + PATCH, x0:x0 + PATCH]
            out.append((p - p.mean()) * win)
            centres.append((x0 + PATCH / 2, y0 + PATCH / 2))
    return np.fft.rfft2(np.stack(out)), np.array(centres)


def _peak(r: np.ndarray) -> tuple[float, float, float]:
    """The sub-pixel position (dx, dy) of a correlation surface's peak, wrapped to ±half, and its height."""
    n = r.shape[0]
    iy, ix = np.unravel_index(int(np.argmax(r)), r.shape)

    def sub(m1, m0, p1):
        d = m1 - 2 * m0 + p1
        return 0.0 if abs(d) < 1e-12 else 0.5 * (m1 - p1) / d

    dx = ix + sub(r[iy, ix - 1], r[iy, ix], r[iy, (ix + 1) % n])
    dy = iy + sub(r[iy - 1, ix], r[iy, ix], r[(iy + 1) % n, ix])
    dx = dx - n if dx > n / 2 else dx
    dy = dy - n if dy > n / 2 else dy
    return dx, dy, float(r[iy, ix])


def _fit(d: np.ndarray, c: np.ndarray, w: np.ndarray, centre: np.ndarray) -> tuple[float, float, float]:
    """The shift (tx, ty) and small turn `a` that best explain patch moves `d` at centres `c` (weights `w`):
    d ≈ t + a · (-(y - cy), x - cx). Patches far from the consensus are dropped and the fit made again."""
    rel = c - centre
    rows = np.zeros((2 * len(d), 3))
    rows[0::2, 0], rows[1::2, 1] = 1.0, 1.0
    rows[0::2, 2], rows[1::2, 2] = -rel[:, 1], rel[:, 0]
    rhs = d.reshape(-1)
    keep = w > 0
    sol = np.zeros(3)
    for _ in range(2):
        if keep.sum() < 3:
            break
        k2 = np.repeat(keep, 2)
        ww = np.repeat(np.sqrt(w), 2)[k2]
        sol = np.linalg.lstsq(rows[k2] * ww[:, None], rhs[k2] * ww, rcond=None)[0]
        err = np.hypot(*(rows @ sol - rhs).reshape(-1, 2).T)
        keep = keep & (err <= max(0.5, 3 * float(np.median(err[keep]))))
    return float(sol[0]), float(sol[1]), float(sol[2])


def _cache_file(root: Path, path: Path, start: float, end: float) -> Path:
    st = path.stat()
    key = f"{VERSION}|{path.resolve()}|{st.st_size}|{st.st_mtime_ns}|{start:.3f}|{end:.3f}"
    return root / "build" / "edit" / "stab" / f"{hashlib.sha1(key.encode()).hexdigest()[:16]}.json"


def measure(root: Path, path: Path, start: float, end: float, say=lambda line: None) -> CameraPath:
    """The camera's path from `start` to `end` seconds of `path`, measured once and cached."""
    cache = _cache_file(root, path, start, end)
    if cache.is_file():
        d = json.loads(cache.read_text())
        return CameraPath(*(np.array(d[k]) for k in ("times", "x", "y", "a")), d["aspect"])
    say(f"stabilise: measuring the shake in {path.name} ({end - start:.1f} s) ...")
    times, moves = [], []
    with av.open(str(path)) as c:
        s = c.streams.video[0]
        s.thread_type = "AUTO"
        W, H = s.codec_context.width, s.codec_context.height
        h = max(PATCH * 2, round(WIDTH * H / W / 2) * 2)
        c.seek(max(0, int(max(0.0, start - 1.0) / s.time_base)), stream=s, backward=True, any_frame=False)
        prev = None
        for f in decode_video(c, s):
            t = float(f.pts * s.time_base) if f.pts is not None else 0.0
            if t < start - 1e-6:
                continue
            if t > end + 1e-6:
                break
            grey = f.reformat(width=WIDTH, height=h, format="gray").to_ndarray().astype(np.float32)
            spec, centres = _patches(grey)
            if prev is None:
                move = (0.0, 0.0, 0.0)
            else:
                cross = spec * np.conj(prev)
                r = np.fft.irfft2(cross / np.maximum(np.abs(cross), 1e-9), s=(PATCH, PATCH))
                pk = np.array([_peak(x) for x in r])
                move = _fit(pk[:, :2], centres, np.clip(pk[:, 2], 0, None), np.array([WIDTH / 2, h / 2]))
            prev = spec
            times.append(t)
            moves.append(move)
    if not times:
        raise ValueError(f"{path.name} has no frames from {start:g} s to {end:g} s")
    m = np.array(moves)
    p = CameraPath(np.array(times), np.cumsum(m[:, 0]) / WIDTH, np.cumsum(m[:, 1]) / WIDTH, np.cumsum(m[:, 2]), H / W)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"times": p.times.round(6).tolist(), "x": p.x.round(7).tolist(),
                                 "y": p.y.round(7).tolist(), "a": p.a.round(7).tolist(), "aspect": p.aspect}))
    return p


# ---------------------------------------------------------------- correcting

def _smooth(v: np.ndarray, times: np.ndarray, seconds: float) -> np.ndarray:
    """`v` averaged with a Gaussian `seconds` wide (two standard deviations either side), ends held."""
    if len(v) < 3:
        return v.copy()
    step = float(np.median(np.diff(times))) or 1 / 30
    sigma = max(1e-6, seconds / 4 / step)
    r = math.ceil(3 * sigma)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    return np.convolve(np.pad(v, r, mode="edge"), k, mode="valid")


class Steady:
    """The correction for each moment of a clip: `at(s)` is the (shift x, shift y, turn) that holds the frame
    shown at `s` seconds of the file steady, and `zoom` the scale that keeps the moved edges out of view."""

    def __init__(self, path: CameraPath, opts: Stabilize, span: float = 1.0):
        """`span`: the file's width over the width shown (above 1 for a crop), so shifts scale to the picture."""
        self.path, self.span = path, span
        self.cx = _smooth(path.x, path.times, opts.smooth) - path.x
        self.cy = _smooth(path.y, path.times, opts.smooth) - path.y
        self.ca = _smooth(path.a, path.times, opts.smooth) - path.a
        if opts.zoom == "auto":
            asp = path.aspect
            need = (np.cos(self.ca) + np.abs(np.sin(self.ca)) / asp
                    + 2 * span * np.maximum(np.abs(self.cx), np.abs(self.cy) / asp))
            self.wanted = float(need.max(initial=1.0))
            self.zoom = min(MAX_ZOOM, self.wanted)
        else:
            self.wanted = self.zoom = float(opts.zoom)

    @property
    def largest(self) -> float:
        """The largest shift corrected, as a fraction of the frame's width."""
        return float(np.hypot(self.cx, self.cy).max(initial=0.0))

    def at(self, s: float) -> tuple[float, float, float]:
        i = int(np.clip(np.searchsorted(self.path.times, s + 1e-6) - 1, 0, len(self.path.times) - 1))
        return float(self.cx[i]), float(self.cy[i]), float(self.ca[i])

    def warp(self, a: np.ndarray, s: float, bg) -> np.ndarray:
        """Picture `a` (the frame as fitted, before it is placed) moved, turned and zoomed to hold it steady."""
        h, w = a.shape[:2]
        dx, dy, ang = self.at(s)
        tx, ty = dx * w * self.span, dy * w * self.span
        z = self.zoom
        cx, cy = w / 2, h / 2
        cos, sin = math.cos(ang), math.sin(ang)
        # PIL maps each output pixel back to the picture: the inverse of zoom and turn about the centre, then shift
        coeffs = (cos / z, sin / z, cx - (cos * (cx + tx) + sin * (cy + ty)) / z,
                  -sin / z, cos / z, cy - (-sin * (cx + tx) + cos * (cy + ty)) / z)
        mode = "RGBA" if a.shape[2] == 4 else "RGB"
        fill = (*bg, 255) if mode == "RGBA" else tuple(bg)
        img = PILImage.fromarray(a, mode).transform((w, h), PILImage.Transform.AFFINE, coeffs,
                                                     PILImage.Resampling.BILINEAR, fillcolor=fill)
        return np.asarray(img)
