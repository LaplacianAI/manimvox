"""Diagram components. Each returns a VGroup the episode positions."""
from __future__ import annotations

import numpy as np
from manim import (
    BOLD,
    DOWN,
    ITALIC,
    LEFT,
    NORMAL,
    RIGHT,
    UL,
    UP,
    Arrow,
    Circle,
    CurvedArrow,
    DashedLine,
    DashedVMobject,
    Dot,
    Line,
    RoundedRectangle,
    Text,
    VGroup,
)

from .colours import ACCENT, BG, BLUE, CODE_BG, ERROR, INK, LINE, MUTED, OK, PANEL, PANEL2, WARN
from .text import FONT, MONO, SAFE_W, STAGE_BOTTOM, STAGE_TOP, P, T, fit


def box(w, h, fill=PANEL, stroke=LINE, r=0.16, sw=2, op=1.0):
    r = min(r, w / 2 - 0.01, h / 2 - 0.01)
    return RoundedRectangle(corner_radius=r, width=w, height=h).set_fill(fill, op).set_stroke(stroke, sw)


def chip(text, color=ACCENT, size=16, filled=False, weight=BOLD):
    """Small pill label."""
    t = T(text, size, BG if filled else color, weight)
    bg = box(t.width + 0.36, t.height + 0.22, fill=color if filled else BG, stroke=color, r=0.2, sw=1.6)
    return VGroup(bg, t.move_to(bg))


def card(title, body=None, w=3.8, color=BLUE, title_size=24, body_size=17, pad=0.26, fill=PANEL, icon=None):
    """Titled panel with an accent bar. `body` is a string or list of strings."""
    inner = w - 2 * pad - 0.12
    head = T(title, title_size, INK, BOLD, max_w=inner - (0.75 if icon else 0))
    if icon is not None:
        icon.scale_to_fit_height(0.5)
        head = VGroup(icon, head).arrange(RIGHT, buff=0.2)
    parts = VGroup(head)
    if body:
        for b in [body] if isinstance(body, str) else body:
            parts.add(P(b, body_size, MUTED, max_w=inner))
    parts.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    bg = box(w, parts.height + 2 * pad, fill=fill, stroke=LINE)
    bar = box(0.09, bg.height - 0.3, fill=color, stroke=color, r=0.04, sw=0).align_to(bg, LEFT).shift(RIGHT * 0.12)
    parts.align_to(bg, LEFT).shift(RIGHT * (pad + 0.12)).set_y(bg.get_y())
    g = VGroup(bg, bar, parts)
    g.bg = bg
    return g


def node(label, sub=None, w=2.6, h=None, color=BLUE, size=21, sub_size=14, fill=PANEL, label_color=INK):
    """Compact labelled box for diagrams."""
    texts = VGroup(T(label, size, label_color, BOLD, max_w=w - 0.36))
    if sub:
        texts.add(P(sub, sub_size, MUTED, max_w=w - 0.36, align="center"))
    texts.arrange(DOWN, buff=0.09)
    bg = box(w, h or texts.height + 0.46, fill=fill, stroke=color, sw=2.4)
    g = VGroup(bg, texts.move_to(bg))
    g.bg = bg
    return g


def arrow(a, b, color=MUTED, label=None, buff=0.12, sw=3.0, label_size=14, curve=0.0, dashed=False, label_color=None,
          label_above=False):
    """Arrow from the edge of `a` to the edge of `b` (mobjects or points).
    The label sits on the line; `label_above=True` lifts it clear, for arrows too
    short to show both."""
    pa = a if isinstance(a, np.ndarray) else None
    pb = b if isinstance(b, np.ndarray) else None
    ca = pa if pa is not None else a.get_center()
    cb = pb if pb is not None else b.get_center()
    d = cb - ca
    horiz = abs(d[0]) >= abs(d[1])
    if pa is None:
        pa = (a.get_right() if d[0] > 0 else a.get_left()) if horiz else (a.get_top() if d[1] > 0 else a.get_bottom())
    if pb is None:
        pb = (b.get_left() if d[0] > 0 else b.get_right()) if horiz else (b.get_bottom() if d[1] > 0 else b.get_top())
    if curve:
        arr = CurvedArrow(pa, pb, angle=curve, color=color, stroke_width=sw, tip_length=0.2)
    else:
        arr = Arrow(pa, pb, buff=buff, color=color, stroke_width=sw, tip_length=0.2,
                    max_tip_length_to_length_ratio=0.4, max_stroke_width_to_length_ratio=20)
    if dashed:
        tip = arr.tip
        arr = VGroup(DashedVMobject(Line(pa, pb, buff=buff).set_stroke(color, sw), num_dashes=14), tip)
    g = VGroup(arr)
    if label:
        t = T(label, label_size, label_color or color)
        plate = box(t.width + 0.2, t.height + 0.14, fill=BG, stroke=BG, r=0.08, sw=0)
        # On a curve the chord's midpoint is off the line; use the curve's own middle.
        mid = arr.point_from_proportion(0.5) if curve and not dashed else (pa + pb) / 2
        lab = VGroup(plate, t).move_to(mid)
        if label_above:
            lab.shift(UP * (t.height / 2 + 0.16))
        g.add(lab)
    return g


def gnode(name, color=BLUE, shape="circle", r=0.32, size=17, mono=True):
    """A node drawn the way a product's graph view draws one: a filled shape
    with the name beneath. `shape` is "circle" or "square". `.shape` is the
    shape, `.label` the name; edges should meet `.shape`, not the group."""
    if shape == "square":
        sh = RoundedRectangle(corner_radius=r * 0.35, width=r * 1.7, height=r * 1.7)
    else:
        sh = Circle(radius=r)
    sh.set_fill(color, 1).set_stroke(BG, 3)
    lab = T(name, size, INK, font=MONO if mono else FONT).next_to(sh, DOWN, buff=0.1)
    g = VGroup(sh, lab)
    g.shape, g.label = sh, lab
    return g


def gedge(a, b, label=None, color=LINE, size=13):
    """Directed edge between two `gnode`s, rim to rim, label above its middle."""
    sa, sb = a.shape, b.shape
    d = sb.get_center() - sa.get_center()
    u = d / (np.linalg.norm(d) or 1)
    pa = sa.get_center() + u * (sa.width / 2 + 0.06)
    pb = sb.get_center() - u * (sb.width / 2 + 0.1)
    arr = Arrow(pa, pb, buff=0, color=color, stroke_width=2.5, tip_length=0.16,
                max_tip_length_to_length_ratio=0.25)
    g = VGroup(arr)
    if label:
        t = T(label, size, MUTED)
        t.move_to((pa + pb) / 2 + np.array([-u[1], u[0], 0]) * 0.18)
        g.add(t)
    return g


def bullets(items, size=24, color=INK, gap=0.26, max_w=9.5, dot=ACCENT):
    """Bulleted list. Returns a VGroup of rows (reveal them one by one)."""
    rows = VGroup()
    line_h = T("Ag", size).height
    for it in items:
        t = P(it, size, color, max_w=max_w - 0.4)
        d = Dot(radius=0.065, color=dot)
        d.move_to(t.get_corner(UL) + LEFT * 0.3 + DOWN * line_h * 0.5)
        rows.add(VGroup(d, t))
    rows.arrange(DOWN, aligned_edge=LEFT, buff=gap)
    return rows


def stat(value, label, color=ACCENT, w=3.0, vsize=52, lsize=16, fill=PANEL):
    """Big number over a caption."""
    v = T(value, vsize, color, BOLD, max_w=w - 0.4)
    l = P(label, lsize, MUTED, max_w=w - 0.4, align="center")
    inner = VGroup(v, l).arrange(DOWN, buff=0.14)
    bg = box(w, inner.height + 0.6, fill=fill)
    g = VGroup(bg, inner.move_to(bg))
    g.value = v
    return g


def table(rows, col_w, size=18, row_h=0.6, header=True, header_color=ACCENT, colors=None, mono_cols=()):
    """Simple table. Returns VGroup of rows; each row = VGroup(bg, *cells)."""
    total = sum(col_w)
    out = VGroup()
    for r, row in enumerate(rows):
        is_head = header and r == 0
        bg = box(total, row_h, fill=PANEL2 if is_head else (PANEL if r % 2 else BG), stroke=LINE, r=0.06, sw=1)
        cells = VGroup()
        x = -total / 2
        for c, (txt, w) in enumerate(zip(row, col_w)):
            col = header_color if is_head else (colors[c] if colors and colors[c] else INK)
            t = T(txt, size, col, BOLD if is_head else NORMAL, font=MONO if (c in mono_cols and not is_head) else FONT,
                  max_w=w - 0.3)
            t.move_to(bg).set_x(x + 0.15 + t.width / 2)
            cells.add(t)
            x += w
        out.add(VGroup(bg, *cells))
    out.arrange(DOWN, buff=0.04)
    return out


def code(src, size=17, title=None, w=None, colors=None, line_spacing=-1):
    """Monospace panel. `colors` maps substrings to colours (t2c).
    `line_spacing` above 0 opens the lines up (try 0.8) for code read aloud line by line."""
    txt = Text(src.strip("\n"), font=MONO, font_size=size, color=INK, t2c=colors or {}, disable_ligatures=True,
               line_spacing=line_spacing)
    ttl = T(title, 14, MUTED, font=MONO) if title else None
    w = w or max(txt.width + 0.7, (ttl.width + 1.3) if ttl else 0)
    if txt.width > w - 0.6:
        txt.scale_to_fit_width(w - 0.6)
    head_h = 0.42
    bg = box(w, txt.height + 0.6 + head_h, fill=CODE_BG, stroke=LINE)
    dots = VGroup(*[Dot(radius=0.055, color=c) for c in (ERROR, WARN, OK)]).arrange(RIGHT, buff=0.1)
    dots.move_to(bg.get_corner(UL) + RIGHT * 0.42 + DOWN * 0.25)
    g = VGroup(bg, dots)
    if ttl:
        g.add(ttl.next_to(dots, RIGHT, buff=0.25))
    txt.move_to(bg).shift(DOWN * head_h / 2).align_to(bg, LEFT).shift(RIGHT * 0.32)
    g.add(txt)
    g.text = txt
    return g


def flow(labels, w=2.2, color=BLUE, gap=0.55, size=19, subs=None, max_w=SAFE_W):
    """Horizontal chain of nodes joined by arrows. Returns (nodes, arrows)."""
    nodes = VGroup(*[node(l, subs[i] if subs else None, w=w, color=color, size=size) for i, l in enumerate(labels)])
    nodes.arrange(RIGHT, buff=gap)
    fit(nodes, max_w)
    arrows = VGroup(*[arrow(nodes[i], nodes[i + 1], buff=0.06) for i in range(len(nodes) - 1)])
    return nodes, arrows


def heading(text, size=38, color=INK, sub=None, sub_size=20):
    """Scene heading for the top of the stage (already positioned)."""
    g = VGroup(T(text, size, color, BOLD, max_w=12.4))
    if sub:
        g.add(T(sub, sub_size, MUTED, max_w=12.4))
    g.arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    g.to_corner(UL, buff=0).move_to([-6.6 + g.width / 2, STAGE_TOP - g.height / 2, 0])
    return g


def note(text, color=MUTED, size=15):
    """Small source / caveat line pinned to the bottom of the stage."""
    return T(text, size, color, slant=ITALIC, max_w=12.8).move_to([0, STAGE_BOTTOM + 0.12, 0])


def lifeline(label, x, top=2.2, bottom=-3.2, color=BLUE, w=2.3, size=18):
    """Sequence-diagram column: a header box at `top` and a dashed line down to
    `bottom`. Returns VGroup(head, line); `.x` is the column's x."""
    head = node(label, w=w, color=color, size=size).move_to([x, top, 0])
    line = DashedLine(head.get_bottom(), [x, bottom, 0], dash_length=0.12).set_stroke(LINE, 2)
    g = VGroup(head, line)
    g.x = x
    return g


def message(a, b, y, label=None, color=MUTED, dashed=False, size=15):
    """Horizontal sequence-diagram message from lifeline `a` to lifeline `b` at
    height `y`. A reply is usually `dashed=True`. Label sits above the arrow."""
    pa, pb = np.array([a.x, y, 0]), np.array([b.x, y, 0])
    d = 1 if b.x > a.x else -1
    pa, pb = pa + RIGHT * d * 0.08, pb - RIGHT * d * 0.08
    if dashed:
        line = DashedLine(pa, pb, dash_length=0.1).set_stroke(color, 2.5)
        tip = Arrow(pb - RIGHT * d * 0.3, pb, buff=0, color=color, stroke_width=2.5, tip_length=0.18).tip
        arr = VGroup(line, tip)
    else:
        arr = Arrow(pa, pb, buff=0, color=color, stroke_width=3, tip_length=0.18,
                    max_tip_length_to_length_ratio=0.3)
    g = VGroup(arr)
    if label:
        g.add(T(label, size, color if color != MUTED else INK, max_w=abs(b.x - a.x) - 0.2).next_to(arr, UP, buff=0.06))
    return g
