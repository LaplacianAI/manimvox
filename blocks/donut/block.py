"""A donut chart: up to six slices of a whole, each with a leader line, a name and a percentage outside the ring,
and the total in the hole."""
from manimvox.kit import *

_PALETTE = [ACCENT, BLUE, TEAL, ORANGE, VIOLET, PINK]


def _spread(ys, gap, limit):
    """Move label heights `ys` (any order) so neighbours keep `gap` between centres: one pass downward from the
    top, then the stack is lifted back if it ran below `-limit` (and never above `limit`). Returns the new heights
    in the order given."""
    order = sorted(range(len(ys)), key=lambda i: -ys[i])
    out = [0.0] * len(ys)
    prev = None
    for i in order:
        out[i] = ys[i] if prev is None else min(ys[i], prev - gap)
        prev = out[i]
    if order:
        low, top = out[order[-1]], out[order[0]]
        lift = min(max(0.0, -limit - low), max(0.0, limit - top))
        out = [y + lift for y in out]
    return out


def donut(parts, total_label=None, radius=1.5, thickness=0.55, size=18):
    """A donut chart of `parts`, a list of (label, value) with 1 to 6 items and every value above 0 (an "Other"
    slice is for the author to add). Slices run clockwise from 12 o'clock, biggest first, in the colours ACCENT,
    BLUE, TEAL, ORANGE, VIOLET, PINK. Each label, a name over a percentage, sits outside the ring on the left or
    right, pushed apart so none overlap, joined to its slice by a leader line. Percentages are rounded to whole
    numbers, so they may add up to 99 or 101. The centre shows the total, with `total_label` under it if given,
    shrunk to fit the hole. `radius` is the outer radius of the ring in scene units, `thickness` its width (above 0
    and below `radius`), `size` the font size of the labels; long names shrink to fit the stage.
    Returns a VGroup with .slices (one VGroup(sector, leader, label) per slice, biggest first), .centre (the total
    text) and .centre_point (a hidden point at the centre). Reveal it with `grow(chart)`.
    Raises ValueError for empty `parts`, more than 6 parts, a value that is not above 0, a label that is not a
    string, or a `radius` or `thickness` that leaves no ring."""
    parts = list(parts)
    if not parts:
        raise ValueError("parts must not be empty")
    if len(parts) > 6:
        raise ValueError(f"parts holds {len(parts)} items; a donut takes at most 6 (merge the small ones into 'Other')")
    for p in parts:
        if not isinstance(p, (tuple, list)) or len(p) != 2:
            raise ValueError("each part must be a (label, value) pair")
        if not isinstance(p[0], str):
            raise ValueError(f"every label must be a string, got {p[0]!r}")
        if isinstance(p[1], bool) or not isinstance(p[1], (int, float)) or not p[1] > 0:
            raise ValueError(f"every value must be a number above 0, got {p[1]!r} for {p[0]!r}")
    if not radius > 0 or not 0 < thickness < radius:
        raise ValueError("radius must be above 0 and thickness above 0 and below radius")
    parts = sorted(parts, key=lambda p: p[1], reverse=True)
    total = sum(v for _, v in parts)
    inner = radius - thickness

    cells = []  # (sector, mid angle, name, percentage)
    start = PI / 2
    for i, (name, v) in enumerate(parts):
        ang = TAU * v / total
        sec = AnnularSector(inner_radius=inner, outer_radius=radius, angle=-ang, start_angle=start)
        sec.set_fill(_PALETTE[i], 1).set_stroke(BG, 2)
        cells.append((sec, start - ang / 2, name, f"{round(100 * v / total)}%"))
        start -= ang

    col = radius + 0.8  # inner edge of the label columns
    max_w = max(1.0, min(3.2, 6.3 - col))
    labels = []
    for _, _, name, pct in cells:
        labels.append(VGroup(T(name, size, INK, BOLD, max_w=max_w), T(pct, size * 0.85, MUTED)))
    gap = 1.4 * max(g.height for g in [VGroup(*lab).arrange(DOWN, buff=0.04) for lab in labels])
    sides = {1: [], -1: []}
    for i, (_, mid, _, _) in enumerate(cells):
        sides[1 if np.cos(mid) >= 0 else -1].append(i)
    ys = {}
    for s, idx in sides.items():
        new = _spread([(radius + 0.35) * np.sin(cells[i][1]) for i in idx], gap, radius + 0.9)
        ys.update(zip(idx, new))

    slices = VGroup()
    for i, (sec, mid, _, _) in enumerate(cells):
        s = 1 if np.cos(mid) >= 0 else -1
        d = np.array([np.cos(mid), np.sin(mid), 0])
        lab = labels[i]
        lab[0].move_to(ORIGIN)
        lab.arrange(DOWN, buff=0.04, aligned_edge=LEFT if s == 1 else RIGHT)
        lab.move_to([s * col + s * lab.width / 2, ys[i], 0])
        line = VMobject().set_points_as_corners([d * radius, d * (radius + 0.25), [s * (col - 0.1), ys[i], 0]])
        line.set_fill(opacity=0).set_stroke(MUTED, 1.5)
        slices.add(VGroup(sec, line, lab))

    centre = VGroup(T(f"{total:,.2f}".rstrip("0").rstrip("."), size * 1.9, INK, BOLD))
    if total_label:
        centre.add(T(total_label, size * 0.85, MUTED))
    centre.arrange(DOWN, buff=0.08)
    fit = min(1.0, 2 * inner * 0.8 / np.hypot(centre.width, centre.height))  # the text's corners stay in the hole
    centre.scale(fit).move_to(ORIGIN)
    point = VectorizedPoint([0, 0, 0])
    g = VGroup(slices, centre, point)
    g.slices, g.centre, g.centre_point = slices, centre, point
    return g


def grow(chart, lag_ratio=0.15):
    """The animation that fades in the centre, then the slices one after another, each with its leader line and label."""
    return AnimationGroup(
        FadeIn(chart.centre),
        LaggedStart(*[AnimationGroup(FadeIn(s[0], scale=0.9), FadeIn(s[1]), FadeIn(s[2])) for s in chart.slices],
                    lag_ratio=lag_ratio))
