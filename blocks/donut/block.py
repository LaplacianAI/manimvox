"""A donut chart: up to six slices of a whole, each with a leader line, a name and a percentage outside the ring,
and the total in the hole."""
import math
import numbers

from manimvox.kit import *

_PALETTE = [ACCENT, BLUE, TEAL, ORANGE, VIOLET, PINK]


def _share(v, total):
    """The slice's share as text: whole percent, or "<1%" for a slice that would round to 0%."""
    pct = round(100 * v / total)
    return f"{pct}%" if pct >= 1 else "<1%"


def _total_text(total):
    """The centre number: up to 2 decimals, or 2 significant digits for a total below 0.005."""
    text = f"{total:,.2f}".rstrip("0").rstrip(".")
    return text if text != "0" else f"{total:.2g}"


def donut(parts, total_label=None, radius=1.5, thickness=0.55, size=18):
    """A donut chart of `parts`, a list of (label, value) with 1 to 6 items and every value above 0 (an "Other"
    slice is for the author to add). Values may be ints, floats or numpy numbers. Slices run clockwise from
    12 o'clock, biggest first, in the colours ACCENT, BLUE, TEAL, ORANGE, VIOLET, PINK. Each label, a name over a
    percentage, sits outside the ring on the left or right, joined to its slice by a leader line; the labels are
    placed by the kit's `leaders`, so none overlap and no two lines cross, however close the small slices sit.
    Percentages are rounded to whole numbers, so they may add up to 99 or 101; a slice under 0.5% reads "<1%"
    (it is shown, but is a sliver barely wider than the line between slices; merge such slices into an "Other"
    one if they matter). The centre shows the total, with `total_label` under it if given, shrunk to fit the
    hole. `radius` is the outer radius of the ring in scene units, `thickness` its width (above 0 and below
    `radius`), `size` the font size of the labels; long names shrink to fit the stage. Build the chart where it
    will stay (the labels are laid out for its place on the stage), then move it as one group.
    Returns a VGroup with .slices (one VGroup(sector, leader, label) per slice, biggest first; the leader is a
    VGroup(line, dot) with .line and .dot), .centre (the total text) and .centre_point (a hidden point at the
    centre). Reveal it with `grow(chart)`.
    Raises ValueError for empty `parts`, more than 6 parts, a value that is not a finite number above 0, a label
    that is not a string, or a `radius`, `thickness` or `size` that leaves no ring or no text."""
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
        if isinstance(p[1], bool) or not isinstance(p[1], numbers.Real):
            raise ValueError(f"every value must be a number above 0, got {p[1]!r} for {p[0]!r}")
        if not math.isfinite(p[1]):
            raise ValueError(f"every value must be finite, got {p[1]!r} for {p[0]!r}")
        if not p[1] > 0:
            raise ValueError(f"every value must be a number above 0, got {p[1]!r} for {p[0]!r}")
    if not all(isinstance(x, numbers.Real) and math.isfinite(x) for x in (radius, thickness, size)):
        raise ValueError("radius, thickness and size must be finite numbers")
    if not radius > 0 or not 0 < thickness < radius or not size > 0:
        raise ValueError("radius must be above 0, thickness above 0 and below radius, and size above 0")
    parts = sorted(((name, float(v)) for name, v in parts), key=lambda p: p[1], reverse=True)
    total = sum(v for _, v in parts)
    inner = radius - thickness

    cells = []  # (sector, mid angle, name, percentage text)
    start = PI / 2
    for i, (name, v) in enumerate(parts):
        ang = TAU * v / total
        sec = AnnularSector(inner_radius=inner, outer_radius=radius, angle=-ang, start_angle=start)
        sec.set_fill(_PALETTE[i], 1).set_stroke(BG, 2)
        cells.append((sec, start - ang / 2, name, _share(v, total)))
        start -= ang

    col = radius + 0.8  # inner edge of the label columns
    max_w = max(1.0, min(3.2, 6.3 - col))
    texts = []  # the name over the percentage, as the two-tone label
    for _, _, name, pct in cells:
        texts.append(VGroup(T(name, size, INK, BOLD, max_w=max_w), T(pct, size * 0.85, MUTED)))
    gap = 0
    for t in texts:
        t.arrange(DOWN, buff=0.04)
        gap = max(gap, t.height)
    gap += 0.2

    # `leaders` places the labels, one column per side: it keeps them apart and inside the stage, and gives each
    # target the slot that stops any two lines crossing. It is given two-line text only to measure; the label it
    # returns is swapped for the two-tone one at the same place.
    leaders_by_index = {}
    for s, side in ((1, "right"), (-1, "left")):
        idx = [i for i, c in enumerate(cells) if (np.cos(c[1]) >= 0) == (s == 1)]
        if not idx:
            continue
        items = [(np.array([np.cos(cells[i][1]), np.sin(cells[i][1]), 0]) * radius,
                  f"{cells[i][2]}\n{cells[i][3]}", _PALETTE[i]) for i in idx]
        group = leaders(items, side=side, x=s * col, gap=gap, size=size, weight=BOLD)
        leaders_by_index.update(zip(idx, group))

    slices = VGroup()
    for i, (sec, mid, _, _) in enumerate(cells):
        s = 1 if np.cos(mid) >= 0 else -1
        ldr = leaders_by_index[i]
        old = ldr.label
        lab = texts[i]
        lab[0].move_to(ORIGIN)
        lab.arrange(DOWN, buff=0.04, aligned_edge=LEFT if s == 1 else RIGHT)
        near = old.get_left()[0] if s == 1 else old.get_right()[0]
        lab.move_to([near + s * lab.width / 2, old.get_center()[1], 0])
        lead = VGroup(ldr.line, ldr.dot)
        lead.line, lead.dot = ldr.line, ldr.dot
        slices.add(VGroup(sec, lead, lab))

    centre = VGroup(T(_total_text(total), size * 1.9, INK, BOLD))
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
