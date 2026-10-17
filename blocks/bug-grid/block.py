"""One square per item (bugs, tests, files, requests) in a grid, lit up in turn as they are counted."""
import math

from manimvox.kit import *


def bug_grid(n, cols=16, size=0.36, gap=0.1, fill=PANEL, stroke=LINE):
    """`n` rounded squares in rows of `cols`, `size` scene units wide with `gap` between them.
    Returns a VGroup of the squares in reading order; slice it to light some (`light(grid[:53], ACCENT)`)."""
    squares = VGroup(*[RoundedRectangle(corner_radius=0.05, width=size, height=size).set_fill(fill, 1)
                       .set_stroke(stroke, 1.5) for _ in range(n)])
    squares.arrange_in_grid(rows=math.ceil(n / cols), cols=cols, buff=gap)
    return squares


def light(squares, color=ACCENT, lag_ratio=0.03):
    """The animation that fills `squares` (a slice of the grid) one after another in `color`."""
    return LaggedStart(*[s.animate.set_fill(color, 1).set_stroke(color, 1.5) for s in squares], lag_ratio=lag_ratio)
