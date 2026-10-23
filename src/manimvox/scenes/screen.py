"""Overlays for screenshots and screen recordings: a spotlight on a region, a callout, a cursor that points and
clicks, and window chrome. Regions are (x, y, w, h) in the source's pixels, as `Clip.at` takes them, and every
overlay is placed for the clip's current position and zoom: make it after the clip has moved or zoomed."""
from __future__ import annotations

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AnimationGroup,
    Cutout,
    Dot,
    Flash,
    Indicate,
    Polygon,
    Rectangle,
    RoundedRectangle,
    VectorizedPoint,
    VGroup,
)

from ..kit.colours import ACCENT, BG, INK, LINE, MUTED, PANEL, PANEL2
from ..kit.components import arrow, chip
from ..kit.text import STAGE_BOTTOM, STAGE_TOP, T
from .clip import Clip, SceneError

SIDES = {"right": RIGHT, "left": LEFT, "up": UP, "down": DOWN}
STAGE_X = 6.6


def _region(clip: Clip, region) -> tuple[np.ndarray, float, float]:
    """The centre, width and height on the stage of the visible part of `region`."""
    if not isinstance(clip, Clip):
        raise SceneError(f"the overlays mark a Clip (screenshot, from_video), got {type(clip).__name__}")
    if len(region) != 4:
        raise SceneError(f"a region is (x, y, w, h) in the source's pixels, got {region!r}")
    seen = clip.visible(*region)
    if seen is None:
        raise SceneError(f"region {tuple(region)} is outside what the clip shows now (zoomed to {clip.view})")
    x, y, w, h = seen
    a, b = clip.at(x, y), clip.at(x + w, y + h)
    return (a + b) / 2, abs(b[0] - a[0]), abs(b[1] - a[1])


def box_on(clip: Clip, region, color=ACCENT, sw: float = 4, r: float = 0.08, pad: float = 0.06) -> RoundedRectangle:
    """An outline around `region`, a little outside it so it doesn't cover the region's own edge."""
    c, w, h = _region(clip, region)
    return RoundedRectangle(width=w + 2 * pad, height=h + 2 * pad, corner_radius=r).set_stroke(color, sw).move_to(c)


def spotlight(clip: Clip, region, opacity: float = 0.72, color=ACCENT, sw: float = 4) -> VGroup:
    """Dims the clip except `region`, and outlines the region. Returns a VGroup with .mask and .ring:
    `FadeIn` it to focus, `FadeOut` it before the next spotlight or zoom."""
    ring = box_on(clip, region, color, sw)
    c, w, h = _region(clip, region)  # the hole is the region itself, so the mask never passes the clip's edge
    frame = Rectangle(width=clip.width, height=clip.height).move_to(clip.get_center())
    hole = RoundedRectangle(width=w, height=h, corner_radius=min(0.06, w / 2, h / 2)).move_to(c)
    mask = Cutout(frame, hole).set_fill(BG, opacity).set_stroke(width=0)
    g = VGroup(mask, ring)
    g.mask, g.ring = mask, ring
    return g


def callout(clip: Clip, region, text: str, side: str = "right", color=ACCENT, size: int = 18,
            gap: float = 1.0) -> VGroup:
    """A label `gap` scene units off `side` ("right", "left", "up", "down") of `region`, with an arrow to it,
    kept on the stage. Returns a VGroup with .label, .arrow and .ring (the region's outline)."""
    if side not in SIDES:
        raise SceneError(f"side must be one of {', '.join(SIDES)}, got {side!r}")
    ring = box_on(clip, region, color)
    d = SIDES[side]
    label = chip(text, color, size, filled=True)
    edge = ring.get_edge_center(d)
    label.move_to(edge + d * (gap + (label.width if d[0] else label.height) / 2))
    x0, y0 = -STAGE_X + label.width / 2, STAGE_BOTTOM + label.height / 2  # keep the label on the stage
    x1, y1 = STAGE_X - label.width / 2, STAGE_TOP - label.height / 2
    label.move_to([min(max(label.get_x(), x0), x1), min(max(label.get_y(), y0), y1), 0])
    tip = arrow(label.get_edge_center(-d), edge, color=color, buff=0.08)
    g = VGroup(ring, tip, label)
    g.label, g.arrow, g.ring = label, tip, ring
    return g


def cursor(color=INK, outline=BG, size: float = 0.42) -> VGroup:
    """A mouse pointer whose tip is the point it points at (`.tip`). Place it with `point`."""
    shape = Polygon(*[np.array([x, y, 0.0]) * size for x, y in
                      ((0, 0), (0, -1), (0.27, -0.76), (0.45, -1.15), (0.6, -1.08), (0.43, -0.7), (0.75, -0.7))])
    shape.set_fill(color, 1).set_stroke(outline, 2.5)
    tip = VectorizedPoint(np.zeros(3))
    g = VGroup(shape, tip).set_z_index(5)
    g.shape, g.tip = shape, tip
    return g


def point(pointer: VGroup, target, **kwargs):
    """The animation that moves `pointer` (from `cursor`) so its tip lands on `target`, a scene point or a
    mobject's centre; for a spot on a clip, pass `clip.at(x, y)`."""
    goal = target.get_center() if hasattr(target, "get_center") else np.asarray(target, dtype=float)
    return pointer.animate(**kwargs).shift(goal - pointer.tip.get_center()).build()


def click(pointer: VGroup, color=ACCENT, run_time: float = 0.6) -> AnimationGroup:
    """The pointer presses where its tip is now, with a short flash around the spot: play it after the `point`
    that moved it there, not alongside."""
    at = pointer.tip.get_center()
    return AnimationGroup(Indicate(pointer.shape, scale_factor=0.85, color=pointer.shape.get_fill_color(),
                                   run_time=run_time),
                          Flash(at, color=color, flash_radius=0.22, line_length=0.14, num_lines=10,
                                run_time=run_time))


def window(clip: Clip, url: str | None = None, title: str | None = None, bar: float = 0.42) -> VGroup:
    """Browser or app chrome around `clip`: a title bar above it with three dots and the `url` (or `title`),
    and a border. Make it after placing the clip; group them to move both (`Group(window(clip), clip)`).
    Returns a VGroup with .bar, .border and .label (None without a url or title)."""
    left, right, top = clip.get_left()[0], clip.get_right()[0], clip.get_top()[1]
    w = right - left
    top_bar = RoundedRectangle(width=w, height=bar + 0.16, corner_radius=0.14).set_fill(PANEL2, 1).set_stroke(LINE, 1.5)
    top_bar.move_to([(left + right) / 2, top + (bar + 0.16) / 2 - 0.16, 0]).set_z_index(-1)
    border = Rectangle(width=w, height=clip.height).set_stroke(LINE, 1.5).set_fill(opacity=0).move_to(clip)
    dots = VGroup(*[Dot(radius=0.065).set_fill(c, 1).set_stroke(width=0) for c in (MUTED, MUTED, MUTED)])
    dots.arrange(RIGHT, buff=0.1).move_to([left + 0.22 + dots.width / 2, top + bar / 2, 0])
    label = None
    parts = [top_bar, border, dots]
    if url or title:
        text = url or title
        label = T(text, 13, INK if title and not url else MUTED, max_w=w * 0.6)
        if url:
            pill = RoundedRectangle(width=min(w * 0.62, label.width + 0.5), height=bar * 0.66, corner_radius=0.12)
            pill.set_fill(PANEL, 1).set_stroke(LINE, 1).move_to([(left + right) / 2, top + bar / 2, 0])
            parts.append(pill)
        label.move_to([(left + right) / 2, top + bar / 2, 0])
        parts.append(label)
    g = VGroup(*parts)
    g.bar, g.border, g.label = top_bar, border, label
    return g


__all__ = ["box_on", "callout", "click", "cursor", "point", "spotlight", "window"]
