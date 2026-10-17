"""Before and after, side by side: removed lines banded on the left, added lines banded on the right."""
import difflib

from manimvox.kit import *


def _panel(lines, title, size, w):
    char_w = T("M" * 10, size, INK, font=MONO).width / 10
    row_h = T("Ag", size, INK, font=MONO).height * 1.6
    rows = VGroup()
    for k, s in enumerate(lines or [""]):
        t = T(s.strip(), size, INK, font=MONO) if s.strip() else VectorizedPoint()
        t.move_to([(len(s) - len(s.lstrip())) * char_w + t.width / 2, -k * row_h, 0])
        rows.add(t)
    scale = min(1.0, (w - 0.7) / max(rows.width, 0.01))
    rows.scale(scale, about_point=rows.get_corner(UL))
    ttl = T(title, 15, MUTED, font=MONO)
    bg = box(w, rows.height + ttl.height + 1.0, fill=CODE_BG, stroke=LINE).set_z_index(-2)
    ttl.move_to(bg.get_corner(UL) + RIGHT * (0.35 + ttl.width / 2) + DOWN * (0.3 + ttl.height / 2))
    rows.shift(ttl.get_corner(DL) + DOWN * 0.35 - rows.get_corner(UL))
    p = VGroup(bg, ttl, rows)
    p.bg, p.title, p.rows, p.row_h = bg, ttl, rows, row_h * scale
    return p


def _band(panel, k, color):
    band = Rectangle(width=panel.bg.width - 0.2, height=panel.row_h * 0.95).set_fill(color, 0.22).set_stroke(width=0)
    return band.move_to([panel.bg.get_center()[0], panel.rows[k].get_center()[1], 0]).set_z_index(-1)


def code_diff(before, after, title_before="before", title_after="after", size=16, w=6.2):
    """`before` and `after` are source text, compared line by line with difflib: removed lines get an ERROR band
    in the left panel, added lines an OK band in the right one; indentation is kept. Returns a VGroup with .left
    and .right (each with .bg, .title, .rows) and .removed and .added (the bands, to FadeIn after the panels).
    Limits: `before` and `after` must not both be empty (ValueError)."""
    a, b = before.strip("\n").splitlines(), after.strip("\n").splitlines()
    if not a and not b:
        raise ValueError("before and after must not both be empty")
    gone, new = set(), set()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag in ("replace", "delete"):
            gone.update(range(i1, i2))
        if tag in ("replace", "insert"):
            new.update(range(j1, j2))
    left, right = _panel(a, title_before, size, w), _panel(b, title_after, size, w)
    VGroup(left, right).arrange(RIGHT, buff=0.4, aligned_edge=UP)
    removed = VGroup(*[_band(left, i, ERROR) for i in sorted(gone)])
    added = VGroup(*[_band(right, j, OK) for j in sorted(new)])
    g = VGroup(left, right, removed, added)
    g.left, g.right, g.removed, g.added = left, right, removed, added
    return g
