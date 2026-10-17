"""A scatter chart with a log-scale x axis (cost, size, time) and a linear y axis, every point labelled."""
import math

import numpy as np

from manimvox.kit import *


def log_scatter(points, x_range, y_range=(0, 100), x_ticks=(), y_ticks=(), width=8.0, height=4.3, size=16):
    """`points` is a list of (label, x, y, colour) with x > 0. `x_range` (low, high) sets the log axis and
    `y_range` the linear one; `x_ticks` and `y_ticks` are lists of (value, text). Each label sits up and to the
    left of its point, or to the right in the left third of the plot. Returns a VGroup with .axes (axis lines and
    tick text), .marks (one VGroup(dot, label) per point, in order) and .frame (hidden corners used by `place`)."""
    lo, hi = math.log10(x_range[0]), math.log10(x_range[1])
    y0, y1 = y_range

    def at(x, y):
        return np.array([width * (math.log10(x) - lo) / (hi - lo), height * (y - y0) / (y1 - y0), 0.0])

    axes = VGroup(Line(at(x_range[0], y0), at(x_range[1], y0)).set_stroke(LINE, 2),
                  Line(at(x_range[0], y0), at(x_range[0], y1)).set_stroke(LINE, 2))
    for v, text in x_ticks:
        axes.add(T(text, size - 1, MUTED).move_to(at(v, y0) + DOWN * 0.3))
    for v, text in y_ticks:
        axes.add(T(text, size - 1, MUTED).next_to(at(x_range[0], v), LEFT, buff=0.12))
    marks = VGroup()
    for label, x, y, col in points:
        d = Dot(at(x, y), radius=0.11, color=col)
        lab = T(label, size, INK if col == MUTED else col, BOLD)
        lab.next_to(d, UR if at(x, y)[0] < width / 3 else UL, buff=0.1)
        marks.add(VGroup(d, lab))
    frame = VGroup(VectorizedPoint(at(x_range[0], y0)), VectorizedPoint(at(x_range[1], y1)))
    g = VGroup(axes, marks, frame)
    g.axes, g.marks, g.frame = axes, marks, frame
    g.x_log, g.y_range = (lo, hi), (y0, y1)
    return g


def place(chart, x, y):
    """Where (x, y) sits on the chart as it now stands."""
    a, b = chart.frame[0].get_center(), chart.frame[1].get_center()
    lo, hi = chart.x_log
    y0, y1 = chart.y_range
    return a + (b - a) * np.array([(math.log10(x) - lo) / (hi - lo), (y - y0) / (y1 - y0), 0.0])
