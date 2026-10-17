"""Horizontal bars ranked by value, one row per item, each with its value at the bar's end."""
from manimvox.kit import *


def bar_ranking(rows, max_value=None, width=7.4, row_h=0.36, colors=None, size=16, fmt="{:.1f}", label_w=4.2):
    """Bars for `rows`, a list of (label, value), drawn top to bottom in the order given; bar length is value /
    `max_value` (default: the largest value) of `width`. `colors` maps a row index to a colour; other rows are
    MUTED with dimmed text (default: the first row in ACCENT). Returns a VGroup with .rows (each
    VGroup(label, bar, value)) and .axis (hidden points at value 0 and `max_value`, used by `value_x`).
    Raises ValueError for empty `rows`, a negative value, or a `max_value` that is not above 0."""
    if not rows:
        raise ValueError("rows must not be empty")
    if any(v < 0 for _, v in rows):
        raise ValueError("rows must not hold a negative value")
    top = max(v for _, v in rows) if max_value is None else max_value
    if not top > 0:
        raise ValueError("max_value (or the largest value) must be above 0")
    colors = {0: ACCENT} if colors is None else colors
    out = VGroup()
    for i, (name, v) in enumerate(rows):
        y = -i * row_h
        c = colors.get(i)
        lab = T(name, size, INK if c else MUTED, BOLD if c else NORMAL, max_w=label_w)
        lab.move_to([-0.2 - lab.width / 2, y, 0])
        bar = Rectangle(width=max(0.03, width * v / top), height=row_h * 0.66)
        bar.set_fill(c or MUTED, 1 if c else 0.55).set_stroke(width=0).move_to([bar.width / 2, y, 0])
        val = T(fmt.format(v), size, INK, BOLD if c else NORMAL).next_to(bar, RIGHT, buff=0.1)
        out.add(VGroup(lab, bar, val))
    axis = VGroup(VectorizedPoint([0, 0, 0]), VectorizedPoint([width, 0, 0]))
    g = VGroup(out, axis)
    g.rows, g.axis, g.top = out, axis, top
    return g


def grow(chart, lag_ratio=0.08):
    """The animation that brings the rows in one after another, each bar growing from the left."""
    return LaggedStart(*[AnimationGroup(FadeIn(r[0]), GrowFromEdge(r[1], LEFT), FadeIn(r[2])) for r in chart.rows],
                       lag_ratio=lag_ratio)


def value_x(chart, v):
    """The x coordinate of value `v` on the chart as it now stands (for a reference line)."""
    a, b = chart.axis[0].get_center()[0], chart.axis[1].get_center()[0]
    return a + (b - a) * v / chart.top
