"""A surface z = f(x, y) over 3D axes, shaded by height: a loss landscape, a density, a field. For an Episode3D."""
import math

import numpy as np

from manimvox.kit import *


def surface_plot(f, x_range=(-3, 3), y_range=(-3, 3), z_range=None, size=5.0, height=2.5,
                 colors=(TEAL, BLUE, VIOLET), resolution=24):
    """The surface z = f(x, y) for x in `x_range` and y in `y_range`, each a (low, high) pair, over 3D axes
    `size` scene units across and `height` tall. `z_range` is (low, high); by default it fits the surface.
    The surface is shaded by height through `colors`, low to high. `resolution` is the number of patches
    along each side, from 4 to 64: more is smoother and slower to render.
    Draw it in an Episode3D and tilt the camera to show its depth. Returns a VGroup with .axes and .surface
    (reveal the axes, then Create the surface) and .f; surface_point, surface_path and downhill place things
    on it. Raises ValueError for a range whose low is not below its high, a resolution outside 4 to 64,
    or an f that is not a finite number everywhere in the ranges."""
    for name, rng in (("x_range", x_range), ("y_range", y_range), ("z_range", z_range)):
        if rng is not None and not rng[0] < rng[1]:
            raise ValueError(f"{name} must be (low, high) with low below high, got {rng!r}")
    if not 4 <= resolution <= 64:
        raise ValueError(f"resolution must be from 4 to 64, got {resolution}")
    xs = np.linspace(*x_range, resolution + 1)
    ys = np.linspace(*y_range, resolution + 1)
    zs = np.array([[f(x, y) for x in xs] for y in ys], dtype=float)
    if not np.isfinite(zs).all():
        raise ValueError("f must give a finite number at every (x, y) in the ranges")
    if z_range is None:
        lo, hi = float(zs.min()), float(zs.max())
        z_range = (lo, hi) if hi > lo else (lo - 1, hi + 1)
    axes = ThreeDAxes(x_range=list(x_range), y_range=list(y_range), z_range=list(z_range),
                      x_length=size, y_length=size, z_length=height,
                      axis_config={"include_tip": False, "include_ticks": False, "color": MUTED, "stroke_width": 2})
    surface = Surface(lambda u, v: axes.c2p(u, v, f(u, v)), u_range=list(x_range), v_range=list(y_range),
                      resolution=(resolution, resolution), fill_opacity=0.9, stroke_color=BG, stroke_width=0.5)
    steps = len(colors) - 1
    surface.set_fill_by_value(axes=axes, colorscale=[
        (c, z_range[0] + (z_range[1] - z_range[0]) * i / max(1, steps)) for i, c in enumerate(colors)])
    g = VGroup(axes, surface)
    g.axes, g.surface, g.f = axes, surface, f
    return g


def surface_point(plot, x, y, lift=0.0):
    """The scene point on `plot` above (x, y), raised `lift` scene units: where to put a ball of radius `lift`."""
    return plot.axes.c2p(x, y, plot.f(x, y)) + OUT * lift


def surface_path(plot, points, color=WARN, width=5, lift=0.03):
    """A line over the surface through the (x, y) `points`, drawn `lift` scene units above it."""
    path = VMobject().set_points_as_corners([surface_point(plot, x, y, lift) for x, y in points])
    return path.set_stroke(color, width)


def downhill(plot, x, y, rate=0.3, steps=40):
    """The (x, y) points of `steps` steps of gradient descent on the plot's f from (x, y), each `rate` times the
    slope: the route a ball rolling downhill takes. Stops early where the ground is flat."""
    h = 1e-4
    pts = [(x, y)]
    for _ in range(steps):
        gx = (plot.f(x + h, y) - plot.f(x - h, y)) / (2 * h)
        gy = (plot.f(x, y + h) - plot.f(x, y - h)) / (2 * h)
        if math.hypot(gx, gy) < 1e-3:
            break
        x, y = x - rate * gx, y - rate * gy
        pts.append((x, y))
    return pts
