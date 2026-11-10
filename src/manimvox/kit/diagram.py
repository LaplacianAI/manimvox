"""Diagrams that explain: labels that point, flows that move, and markers for what comes in and leaves.

Three moves any explanation needs, for any subject: an architecture diagram, a screenshot, the parts of a cell.
Prefer `leaders` over boxed callouts: a dot on the part, a thin line out to the side, the name beside it."""
from __future__ import annotations

import numpy as np
from manim import (
    DOWN,
    LEFT,
    NORMAL,
    RIGHT,
    UP,
    Create,
    Dot,
    FadeIn,
    LaggedStart,
    Succession,
    ValueTracker,
    VGroup,
    VMobject,
)
from scipy.optimize import linear_sum_assignment

from ._context import STROKE
from .colours import ACCENT, INK, LINE, MUTED
from .components import arrow
from .text import SAFE_W, STAGE_BOTTOM, STAGE_TOP, T

_RUN = 0.35  # the short horizontal run into a label
_GAP_TO_LABEL = 0.14


def _point(target) -> np.ndarray:
    if hasattr(target, "get_center"):
        return np.array(target.get_center(), dtype=float)
    p = np.array(target, dtype=float)
    return np.array([p[0], p[1], p[2] if p.size > 2 else 0.0])


def _edge(target, side) -> float:
    """The target's outermost x on `side`: a mobject's edge, or a point's own x."""
    if hasattr(target, "get_right"):
        return float((target.get_right() if side == "right" else target.get_left())[0])
    return float(_point(target)[0])


def _grow(self, run_time: float = 1.0):
    return Succession(FadeIn(self.dot, run_time=run_time * 0.2), Create(self.line, run_time=run_time * 0.45),
                      FadeIn(self.label, run_time=run_time * 0.35))


def _build(p, text, color, size, side, x, label_y, weight=NORMAL):
    """One leader whose label column starts at `x` (its inner edge) and whose label sits at height `label_y`."""
    sign = 1 if side == "right" else -1
    label = T(text, size, color or INK, weight)
    label.move_to([x + sign * label.width / 2, label_y, 0])
    edge = np.array([x - sign * _GAP_TO_LABEL, label_y, 0])
    elbow = edge - np.array([sign * _RUN, 0, 0])
    dot = Dot(p, radius=0.06, color=color or ACCENT)
    line = VMobject().set_points_as_corners([p, elbow, edge]).set_stroke(LINE, 2 * STROKE)
    g = VGroup(line, dot, label)
    g.dot, g.line, g.label = dot, line, label
    g.grow = lambda run_time=1.0: _grow(g, run_time)
    return g


_REACH = 1.0  # how far past the outermost target's edge the label column starts, by default


def _column_x(side, x, width, reach):
    """The label column's inner edge: `x` if given, else `_REACH` past the outermost target x (`reach`) on
    that side, pulled in so the label never runs past the safe stage edge."""
    sign = 1 if side == "right" else -1
    if x is None:
        x = min(reach + _REACH, SAFE_W / 2 - width) if side == "right" else max(reach - _REACH, -SAFE_W / 2 + width)
    need = reach + sign * (_GAP_TO_LABEL + _RUN)  # the bend must sit outside every target, or lines double back
    if sign * (x - need) < -1e-9:
        raise ValueError(
            f"leaders: the {side} label column at x={x:.2f} would sit over the picture (a target reaches "
            f"x={reach:.2f}; the column must start at x {'>=' if sign > 0 else '<='} {need:.2f}). Move the picture "
            f"away from that side, shorten the labels, or put them on the other side.")
    return x


def leader(target, text, side="right", x=None, color=None, size=22, weight=NORMAL):
    """A dot on `target`, a thin leader line and the label `text` beside it, at the height of the target.

    `target` is a mobject (its centre is used) or a point (np array or 3-tuple). For a clip (a screenshot or
    a recording) pass `clip.at(px, py)`, which returns a point in the scene. `side` is "right" or "left";
    `x` is the column where the label starts (its inner edge): by default it starts a short way past the
    target, never letting the label run past the safe stage edge. `color` tints the dot and the label; `weight=BOLD` sets bold labels. Returns a VGroup with `.dot`, `.line`
    and `.label`, and `.grow()` for an animation that fades in the dot, draws the line, then fades in the label,
    so `self.say("...", g.grow())` works."""
    if side not in ("right", "left"):
        raise ValueError(f"leader: side must be 'right' or 'left', got {side!r}")
    p = _point(target)
    probe = T(text, size, weight=weight)
    return _build(p, text, color, size, side, _column_x(side, x, probe.width, _edge(target, side)), p[1], weight)


def _spread(desired, gap, lo, hi):
    """Heights nearest `desired` (listed from the top down) that are `gap` apart and inside [lo, hi]."""
    n = len(desired)
    if n > 1 and gap * (n - 1) > hi - lo:
        gap = (hi - lo) / (n - 1)
    # Isotonic regression: closest non-increasing sequence to d_i + i*gap, then take i*gap back off.
    blocks = []  # [sum, count]
    for i, d in enumerate(desired):
        blocks.append([d + i * gap, 1])
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] < blocks[-1][0] / blocks[-1][1]:
            s, c = blocks.pop()
            blocks[-1][0] += s
            blocks[-1][1] += c
    z = [b[0] / b[1] for b in blocks for _ in range(b[1])]
    ys = [zi - i * gap for i, zi in enumerate(z)]
    ys[0] = min(ys[0], hi)
    for i in range(1, n):
        ys[i] = min(ys[i], ys[i - 1] - gap)
    ys[-1] = max(ys[-1], lo)
    for i in range(n - 2, -1, -1):
        ys[i] = max(ys[i], ys[i + 1] + gap)
    return ys


def _column(entries, side, x, gap, size, weight=NORMAL):
    """entries: [(index, point, text, color, target)]. Returns {index: leader}."""
    if not entries:
        return {}
    order = sorted(entries, key=lambda e: (-e[1][1], e[0]))
    probes = [T(e[2], size, weight=weight) for e in order]
    h = max(pr.height for pr in probes)
    gap = gap if gap is not None else h + 0.2
    reach = (max if side == "right" else min)(_edge(e[4], side) for e in entries)
    col = _column_x(side, x, max(pr.width for pr in probes), reach)
    ys = _spread([e[1][1] for e in order], gap, STAGE_BOTTOM + h / 2, STAGE_TOP - h / 2)
    # Give each target the slot that keeps the total length of all leaders least: no two such straight
    # lines can cross, and with targets sorted by height it is the same order unless a crossing would result.
    sign = 1 if side == "right" else -1
    elbow_x = col - sign * (_GAP_TO_LABEL + _RUN)
    cost = [[float(np.hypot(e[1][0] - elbow_x, e[1][1] - y)) for y in ys] for e in order]
    rows, cols = linear_sum_assignment(cost)
    return {order[r][0]: _build(order[r][1], order[r][2], order[r][3], size, side, col, ys[c], weight)
            for r, c in zip(rows, cols)}


def leaders(items, side="right", x=None, gap=None, size=22, weight=NORMAL):
    """One column of pointing labels. `items` are `(target, text)` or `(target, text, color)`.

    Label heights start at the targets' heights, then are pushed apart so they keep a vertical `gap` (default: a
    line of text and a little more) and stay inside the stage. Targets take the slots that make the lines shortest
    overall, which is the targets' top-to-bottom order unless that would make two lines cross, and each leader
    bends in a short horizontal run before its label, so the lines never cross. `side="both"` puts the
    targets left of their mean x on the left, the rest on the right. `x` is the column's inner edge (see `leader`).
    Returns a VGroup of leaders, in the order given, each with `.dot`, `.line` and `.label`; `.grow(lag=0.3)` on
    the group animates them one after another, and `.grow()` on a member animates just that one."""
    if side not in ("right", "left", "both"):
        raise ValueError(f"leaders: side must be 'right', 'left' or 'both', got {side!r}")
    entries = []
    for i, it in enumerate(items):
        target, text, *rest = it
        entries.append((i, _point(target), text, rest[0] if rest else None, target))
    if side == "both":
        mean = float(np.mean([e[1][0] for e in entries])) if entries else 0.0
        left = [e for e in entries if e[1][0] < mean]
        right = [e for e in entries if e[1][0] >= mean]
        placed = {**_column(left, "left", x if x is None else -abs(x), gap, size, weight),
                  **_column(right, "right", x if x is None else abs(x), gap, size, weight)}
    else:
        placed = _column(entries, side, x, gap, size, weight)
    g = VGroup(*[placed[i] for i in range(len(entries))])
    g.grow = lambda lag=0.3, run_time=1.0: LaggedStart(*[m.grow(run_time) for m in g], lag_ratio=lag)
    return g


# ------------------------------------------------------------------ flows
class _Flow(VGroup):
    """The handle `stream` returns: `.trail`, `.dots`, `.level` and the animations below. (Manim already uses
    `.dim` on every mobject for the number of dimensions, so dimming is `fade_to`.)"""

    def fade_to(self, level: float = 0.25, run_time: float = 0.6):
        """An animation that fades the whole stream to `level` (0 to 1) of its brightness."""
        anim = self.level.animate.set_value(level).build()
        anim.run_time = run_time
        return anim

    def brighten(self, run_time: float = 0.6):
        """An animation that brings the stream back to full brightness."""
        return self.fade_to(1.0, run_time)

    def stop(self):
        """Remove the updater: the dots stay where they are. Returns the handle."""
        self.remove_updater(self._flow)
        return self


def stream(path, color=ACCENT, n=40, speed=0.16, glow=True, trail=True, size=0.042):
    """Dots travelling along `path` to show what moves and which way.

    `path` is a VMobject or a list of points (smoothed into a curve). `n` dots travel at `speed` (the share of the
    path covered per second), fading in over the first 8% and out over the last 12%, so they appear where the
    flow enters and vanish where it leaves. `glow` puts a larger faint dot behind each; `trail` draws a faint wide
    line along the path. The dots move by an updater, so they keep moving through `self.say` and `self.wait`.
    Add the returned handle to the scene. It has `.fade_to(level=0.25)` and `.brighten()` (animations: play them
    as the narration moves between flows) and `.stop()`. The motion is the same on every render."""
    if isinstance(path, VMobject):
        route = path
    else:
        route = VMobject().set_points_smoothly([_point(p) for p in path])
    # The route is part of the handle (drawn only as the trail), so moving or scaling the handle moves the flow.
    tr = route.copy().set_fill(opacity=0).set_stroke(color, 9 * STROKE, opacity=0.14 if trail else 0)
    parts = [tr]
    dots = VGroup(*[VGroup(Dot(radius=size * 2, color=color), Dot(radius=size, color=color)) if glow
                    else VGroup(Dot(radius=size, color=color)) for _ in range(n)])
    parts.append(dots)
    g = _Flow(*parts)
    g.route, g.trail, g.dots, g.level = tr, tr if trail else None, dots, ValueTracker(1.0)
    g.phase = 0.0

    def move(m, dt):
        m.phase = (m.phase + dt * speed) % 1
        level = m.level.get_value()
        for i, d in enumerate(m.dots):
            s = (m.phase + i / n) % 1
            d.move_to(m.route.point_from_proportion(s))
            a = level * max(0.0, min(1.0, s / 0.08, (1 - s) / 0.12))
            d[-1].set_opacity(a)
            if glow:
                d[0].set_opacity(0.22 * a)
        if m.trail is not None:
            m.trail.set_stroke(opacity=0.14 * level)

    g._flow = move
    move(g, 0)
    g.add_updater(move)
    return g


# ------------------------------------------------------------------ entry and exit
def _marker(a, b, text, color, label_at, side):
    arr = arrow(a, b, color=color, dashed=True, buff=0)
    g = VGroup(arr)
    g.arrow = arr
    g.label = None
    if text:
        d = (b - a) / (np.linalg.norm(b - a) or 1)
        lab = T(text, 20, color)
        horiz = abs(d[0]) >= abs(d[1])
        if horiz:
            lab.next_to(label_at, RIGHT if side[0] > 0 else LEFT, buff=0.15)
        else:
            lab.next_to(label_at, UP if side[1] > 0 else DOWN, buff=0.15)
        g.add(lab)
        g.label = lab
    return g


def _unit(direction):
    d = np.array(direction, dtype=float)
    return d / (np.linalg.norm(d) or 1.0)


def enters(point, direction=RIGHT, text=None, length=1.2, color=MUTED):
    """A dashed arrow that ends at `point`, travelling along `direction` (so it comes in from the opposite side).
    The optional `text` sits at the far end, beyond where the arrow starts. Returns a VGroup with `.arrow` and
    `.label` (None without text)."""
    d, p = _unit(direction), _point(point)
    a = p - d * length
    return _marker(a, p, text, color, a, -d)


def leaves(point, direction=RIGHT, text=None, length=1.2, color=MUTED):
    """A dashed arrow that starts at `point` and travels along `direction`, off the picture. The optional `text`
    sits at the far end, beyond the arrowhead. Returns a VGroup with `.arrow` and `.label` (None without text)."""
    d, p = _unit(direction), _point(point)
    b = p + d * length
    return _marker(p, b, text, color, b, d)


__all__ = ["enters", "leader", "leaders", "leaves", "stream"]
