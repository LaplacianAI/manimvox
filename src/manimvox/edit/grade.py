"""Colour grading: a segment's `Grade` as one lookup table.

Every control maps a colour to a colour, wherever the pixel is, so the whole grade (and a `.cube` LUT after it) is
evaluated once for all 256³ 8-bit colours into a table, and each frame is graded by one lookup.

Order: exposure and white balance (temperature, tint) in linear light; then lift, gamma and gain, contrast about
mid-grey and saturation on the display values; then the LUT, as a look over the rest.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .timeline import Grade

LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)  # Rec. 709
PIVOT = 0.46  # display value of 18% grey: contrast turns about it
WB_STOPS = 0.35  # how far temperature or tint of 1 moves a channel, in stops


class Cube:
    """A 3D `.cube` LUT: `table[r, g, b]` is the output colour, 0..1, at those lattice points of the domain."""

    def __init__(self, table: np.ndarray, lo: np.ndarray, hi: np.ndarray):
        self.table, self.lo, self.hi = table, lo, hi

    def __call__(self, x: np.ndarray) -> np.ndarray:
        """`x` (n, 3) in 0..1, looked up with trilinear interpolation."""
        n = self.table.shape[0]
        p = np.clip((x - self.lo) / (self.hi - self.lo), 0.0, 1.0) * (n - 1)
        i0 = np.minimum(p.astype(np.int32), n - 2)
        f = p - i0
        r, g, b = i0[:, 0], i0[:, 1], i0[:, 2]
        fr, fg, fb = f[:, 0:1], f[:, 1:2], f[:, 2:3]
        t = self.table

        def lerp(a, c, k):
            return a + (c - a) * k

        c00 = lerp(t[r, g, b], t[r + 1, g, b], fr)
        c10 = lerp(t[r, g + 1, b], t[r + 1, g + 1, b], fr)
        c01 = lerp(t[r, g, b + 1], t[r + 1, g, b + 1], fr)
        c11 = lerp(t[r, g + 1, b + 1], t[r + 1, g + 1, b + 1], fr)
        return lerp(lerp(c00, c10, fg), lerp(c01, c11, fg), fb)


def read_cube(path: Path) -> Cube:
    """Read a 3D `.cube` file (Adobe/Resolve format). Raises ValueError saying what is wrong with it."""
    size, lo, hi, rows = None, [0.0, 0.0, 0.0], [1.0, 1.0, 1.0], []
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        raise ValueError(f"cannot read {path}: {e.strerror or e}") from e
    for n, line in enumerate(text.splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        head, *rest = line.split()
        key = head.upper()
        try:
            if key == "LUT_3D_SIZE":
                size = int(rest[0])
            elif key == "LUT_1D_SIZE":
                raise ValueError(f"{Path(path).name} is a 1D LUT; only 3D .cube LUTs are supported")
            elif key == "DOMAIN_MIN":
                lo = [float(v) for v in rest[:3]]
            elif key == "DOMAIN_MAX":
                hi = [float(v) for v in rest[:3]]
            elif key in ("TITLE", "LUT_3D_INPUT_RANGE", "LUT_IN_VIDEO_RANGE", "LUT_OUT_VIDEO_RANGE"):
                continue
            else:
                rows.append([float(head), *map(float, rest)])
        except (IndexError, ValueError) as e:
            if "1D LUT" in str(e):
                raise
            raise ValueError(f"{Path(path).name} line {n}: cannot read {line[:40]!r}") from None
    if size is None or not 2 <= size <= 256:
        raise ValueError(f"{Path(path).name} has no LUT_3D_SIZE from 2 to 256")
    if len(rows) != size ** 3 or any(len(r) != 3 for r in rows):
        raise ValueError(f"{Path(path).name} should have {size ** 3} rows of three numbers for size {size}, "
                         f"has {len(rows)}")
    lo_a, hi_a = np.array(lo, np.float32), np.array(hi, np.float32)
    if not np.all(hi_a > lo_a):
        raise ValueError(f"{Path(path).name}: DOMAIN_MAX must be above DOMAIN_MIN")
    data = np.asarray(rows, np.float32).reshape(size, size, size, 3)  # [b, g, r]: red changes fastest
    return Cube(np.ascontiguousarray(data.transpose(2, 1, 0, 3)), lo_a, hi_a)


def _rgb(v) -> np.ndarray:
    return np.asarray(v if isinstance(v, (tuple, list)) else (v, v, v), np.float32)


def _linear(x: np.ndarray) -> np.ndarray:
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def _display(x: np.ndarray) -> np.ndarray:
    x = np.maximum(x, 0.0)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


def grade_colors(x: np.ndarray, g: Grade, cube: Cube | None = None) -> np.ndarray:
    """`x` (n, 3) display RGB in 0..1, graded; the result is clipped to 0..1."""
    x = x.astype(np.float32, copy=False)
    wb = np.array([2.0 ** (WB_STOPS * g.temperature), 2.0 ** (-WB_STOPS * g.tint), 2.0 ** (-WB_STOPS * g.temperature)],
                  np.float32)
    wb /= float(LUMA @ wb)  # white balance moves the hue, not the brightness
    if g.exposure or g.temperature or g.tint:
        x = _display(_linear(x) * (2.0 ** g.exposure) * wb)
    lift, gamma, gain = _rgb(g.lift), _rgb(g.gamma), _rgb(g.gain)
    x = gain * (x + lift * (1.0 - x))
    x = np.maximum(x, 0.0) ** (1.0 / gamma)
    x = (x - PIVOT) * g.contrast + PIVOT
    if g.saturation != 1.0:
        y = (x @ LUMA)[:, None]
        x = y + (x - y) * g.saturation
    x = np.clip(x, 0.0, 1.0)
    if cube is not None:
        x = np.clip(cube(x), 0.0, 1.0)
    return x


def build_table(g: Grade, cube: Cube | None = None) -> np.ndarray:
    """The grade for every 8-bit colour: a (256³, 3) uint8 table indexed by r << 16 | g << 8 | b."""
    levels = np.arange(256, dtype=np.float32) / 255.0
    gg, bb = np.meshgrid(levels, levels, indexing="ij")
    gb = np.stack([gg.ravel(), bb.ravel()], axis=1)
    out = np.empty((256, 65536, 3), np.uint8)
    for r in range(256):  # 65536 colours at a time keeps the working memory small
        x = np.empty((65536, 3), np.float32)
        x[:, 0] = levels[r]
        x[:, 1:] = gb
        out[r] = np.rint(grade_colors(x, g, cube) * 255.0)
    return out.reshape(-1, 3)


def apply_table(table: np.ndarray, rgb: np.ndarray) -> np.ndarray:
    """An (h, w, 3|4) uint8 picture graded by `table`; an alpha channel is kept as it is."""
    c = rgb[..., :3].astype(np.int32)
    out = table[(c[..., 0] << 16) | (c[..., 1] << 8) | c[..., 2]]
    if rgb.shape[-1] == 4:
        out = np.concatenate([out, rgb[..., 3:]], axis=-1)
    return out
