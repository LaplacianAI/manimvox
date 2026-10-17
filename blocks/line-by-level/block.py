"""A line chart over named steps (effort levels, versions, weeks): one line per series, each point labelled."""
import numpy as np

from manimvox.kit import *


def line_by_level(levels, series, y_max, y_ticks=None, width=7.0, height=4.2, size=16):
    """`levels` names the x steps; `series` is a list of (name, values, colour) with one value per level;
    the y axis runs from 0 to `y_max` with gridlines at `y_ticks` (default: quarters). Returns a VGroup with
    .grid (gridlines and their numbers), .xlabels, .lines (one VGroup(line, dots, value labels) per series),
    .legend (one entry per series) and .frame (hidden corner points used by `point`).
    Raises ValueError for empty `levels`, a series with a value count other than len(levels), or `y_max` not above 0."""
    if not levels:
        raise ValueError("levels must not be empty")
    if not y_max > 0:
        raise ValueError("y_max must be above 0")
    for name, vals, _col in series:
        if len(vals) != len(levels):
            raise ValueError(f"series {name!r} must have one value per level ({len(levels)})")
    ticks = y_ticks or [y_max * k / 4 for k in range(5)]
    n = len(levels)

    def at(i, v):
        return np.array([width * i / max(1, n - 1), height * v / y_max, 0.0])

    grid = VGroup()
    for v in ticks:
        grid.add(Line(at(0, v) + LEFT * 0.3, at(n - 1, v) + RIGHT * 0.3).set_stroke(LINE, 1.5))
        grid.add(T(f"{v:g}", size - 1, MUTED).next_to(at(0, v) + LEFT * 0.3, LEFT, buff=0.12))
    xlabels = VGroup(*[T(name, size + 1, MUTED).move_to(at(i, 0) + DOWN * 0.32) for i, name in enumerate(levels)])
    lines = VGroup()
    for _name, vals, col in series:
        line = VMobject().set_points_as_corners([at(i, v) for i, v in enumerate(vals)]).set_stroke(col, 4)
        dots = VGroup(*[Dot(at(i, v), radius=0.08, color=col) for i, v in enumerate(vals)])
        labels = VGroup(*[T(str(v), size, col, BOLD).next_to(d, UP, buff=0.1) for v, d in zip(vals, dots)])
        lines.add(VGroup(line, dots, labels))
    legend = VGroup(*[VGroup(Line(LEFT * 0.25, RIGHT * 0.25).set_stroke(col, 4), T(name, size + 2, col, BOLD))
                      .arrange(RIGHT, buff=0.15) for name, _vals, col in series])
    legend.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
    legend.next_to(at(n - 1, y_max) + RIGHT * 0.3, RIGHT, buff=0.5).align_to(at(0, y_max), UP)
    frame = VGroup(VectorizedPoint(at(0, 0)), VectorizedPoint(at(n - 1, y_max)))
    g = VGroup(grid, xlabels, lines, legend, frame)
    g.grid, g.xlabels, g.lines, g.legend, g.frame = grid, xlabels, lines, legend, frame
    g.n, g.y_max = n, y_max
    return g


def point(chart, i, v):
    """Where level `i`, value `v` sits on the chart as it now stands (for a callout)."""
    a, b = chart.frame[0].get_center(), chart.frame[1].get_center()
    return a + (b - a) * np.array([i / max(1, chart.n - 1), v / chart.y_max, 0.0])
