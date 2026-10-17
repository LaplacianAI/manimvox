"""Pixels out of pycairo, colours into it, and words wrapped to a width. Used by scenes and post."""
from __future__ import annotations

import sys

import cairo
import numpy as np


def surface_rgba(surf: cairo.ImageSurface) -> np.ndarray:
    """An ARGB32 surface as straight (not premultiplied) RGBA, shape (h, w, 4), uint8."""
    surf.flush()
    w, h, stride = surf.get_width(), surf.get_height(), surf.get_stride()
    raw = np.frombuffer(surf.get_data(), np.uint8).reshape(h, stride // 4, 4)[:, :w]
    bgra = raw if sys.byteorder == "little" else raw[..., ::-1]  # one native-endian 32-bit ARGB word per pixel
    px = bgra[..., [2, 1, 0, 3]].astype(np.float32)
    a = px[..., 3:4]
    rgb = np.where(a > 0, px[..., :3] * 255.0 / np.maximum(a, 1.0), 0.0)
    return np.concatenate([np.clip(rgb + 0.5, 0, 255), a], axis=2).astype(np.uint8)


def hex_rgb(colour: str) -> tuple[float, float, float]:
    """'#RRGGBB' or '#RGB' as cairo's 0..1 floats; anything unreadable is mid grey."""
    v = str(colour).strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    try:
        return tuple(int(v[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]
    except ValueError:
        return (0.5, 0.5, 0.5)


def wrap(ctx: cairo.Context, text: str, max_w: float) -> list[str]:
    """The words of `text` in lines no wider than `max_w` at the context's font; a word wider than that stays whole."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and ctx.text_extents(trial).x_advance > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines
