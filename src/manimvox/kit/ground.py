"""The theme's ground: a seeded, deterministic full-frame texture drawn once behind everything."""
from __future__ import annotations

import numpy as np
from manim import ImageMobject, config

from ._context import THEME

SIZE = (1920, 1080)  # texture pixels: enough for a 1080p frame, scaled to whatever quality is rendered
SEED = 7


def _rgb(hx):
    return np.array([int(hx[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32)


def ground_pixels(kind, amount, bg, ink):
    """An (h, w, 3) uint8 picture: `bg` with a texture of `kind` in `ink`, as strong as `amount` (0..1)."""
    w, h = SIZE
    rng = np.random.default_rng(SEED)
    base, tint = _rgb(bg), _rgb(ink)
    mix = np.zeros((h, w), dtype=np.float32)  # how far each pixel moves from bg towards ink
    if kind == "grain":
        mix = rng.random((h, w), dtype=np.float32) * 0.10 * amount
    elif kind == "grid":
        step = 60
        mix[::step, :] = 0.16 * amount
        mix[:, ::step] = 0.16 * amount
    elif kind == "paper":
        blotch = np.kron(rng.random((h // 24 + 1, w // 24 + 1), dtype=np.float32), np.ones((24, 24), np.float32))[:h, :w]
        mix = (blotch * 0.05 + rng.random((h, w), dtype=np.float32) * 0.05) * amount
    return (base + (tint - base) * mix[..., None] + 0.5).astype(np.uint8)


def ground_mobject():
    """The ground as a background ImageMobject, or None for no ground or a plain one (`solid`)."""
    g = THEME.ground
    if not g or g["kind"] == "solid":
        return None
    img = ImageMobject(ground_pixels(g["kind"], g["amount"], THEME["bg"], THEME["ink"]))
    img.scale_to_fit_height(config.frame_height).move_to([0, 0, 0]).set_z_index(-1000)
    return img
