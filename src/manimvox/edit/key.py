"""Green screen: an inset's backing colour made transparent.

A pixel's distance from the key colour is measured in the colour-difference plane (Cb, Cr), as FFmpeg's
chromakey does, so the subject's brightness matters less than its hue. Within `similarity` of the key it is transparent; over the next `softness`
it turns opaque, which keeps hair and motion blur soft. Spill, the backing's colour reflected onto the subject,
is pulled out of the key's main channel down to the level of the other two.
"""
from __future__ import annotations

import numpy as np

from .timeline import Key

CB = np.array([-0.168736, -0.331264, 0.5], np.float32)  # BT.601, as FFmpeg's chromakey measures
CR = np.array([0.5, -0.418688, -0.081312], np.float32)
BORDER = 4  # px: "auto" samples the backing from a ring this deep round the frame


def key_color(k: Key, rgb: np.ndarray) -> np.ndarray:
    """The key colour as RGB in 0..1: given, or for "auto" the median of the frame's border."""
    if k.color != "auto":
        h = k.color.lstrip("#")
        return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0
    b, rgb = BORDER, rgb[..., :3]
    ring = np.concatenate([rgb[:b].reshape(-1, 3), rgb[-b:].reshape(-1, 3), rgb[:, :b].reshape(-1, 3),
                           rgb[:, -b:].reshape(-1, 3)])
    return np.median(ring, axis=0).astype(np.float32) / 255.0


def keyed(rgb: np.ndarray, k: Key, color: np.ndarray) -> np.ndarray:
    """An (h, w, 3|4) uint8 picture as RGBA with the key colour transparent and its spill removed; an alpha it
    already had is kept where it is lower."""
    x = rgb[..., :3].astype(np.float32) / 255.0
    d = np.hypot(x @ CB - float(color @ CB), x @ CR - float(color @ CR))
    alpha = np.clip((d - k.similarity) / k.softness, 0.0, 1.0) if k.softness > 0 else (d > k.similarity) * 1.0
    if k.spill > 0:
        main = int(np.argmax(color))
        others = [c for c in range(3) if c != main]
        cap = np.maximum(x[..., others[0]], x[..., others[1]])
        x[..., main] -= k.spill * np.maximum(0.0, x[..., main] - cap)
    if rgb.shape[-1] == 4:
        alpha = np.minimum(alpha, rgb[..., 3] / 255.0)
    out = np.empty((*rgb.shape[:2], 4), np.uint8)
    out[..., :3] = np.rint(x * 255.0)
    out[..., 3] = np.rint(alpha * 255.0)
    return out
