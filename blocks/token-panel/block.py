"""A monospace panel of short lines (a token's fields, a config, a request) whose rows can be boxed in turn."""
from manimvox.kit import *


def token_panel(lines, title=None, size=20, pad=0.5):
    """`lines` are shown one per row in the mono font, under `title` in the panel's top-left corner.
    Returns a VGroup with .bg, .title and .rows (one Text per line); `mark(panel, i, j)` boxes rows i..j.
    Limits: `lines` must not be empty (ValueError)."""
    if not lines:
        raise ValueError("lines must not be empty")
    rows = VGroup(*[T(s, size, INK, font=MONO) for s in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    ttl = T(title or "", 15, MUTED, font=MONO)
    head = ttl.height + 0.4 if title else 0.0
    bg = box(max(rows.width, ttl.width) + 2 * pad + 0.2, rows.height + head + 2 * pad, fill=CODE_BG, stroke=LINE)
    if title:
        ttl.move_to(bg.get_corner(UL) + RIGHT * (pad + ttl.width / 2) + DOWN * (pad * 0.6 + ttl.height / 2))
    rows.move_to(bg).shift(DOWN * head / 2).align_to(bg, LEFT).shift(RIGHT * (pad + 0.1))
    g = VGroup(bg, ttl, rows)
    g.bg, g.title, g.rows = bg, ttl, rows
    return g


def mark(panel, i, j=None, color=ACCENT):
    """A box around rows i..j (inclusive; just row i if `j` is None) of a token panel, to Create().
    Limits: i and j must be row indexes of the panel with j >= i (ValueError)."""
    j = i if j is None else j
    if not (0 <= i < len(panel.rows) and 0 <= j < len(panel.rows) and j >= i):
        raise ValueError(f"rows {i}..{j} are not within the panel's {len(panel.rows)} rows (need 0 <= i <= j)")
    return SurroundingRectangle(panel.rows[i:j + 1], color=color, buff=0.08, corner_radius=0.05)
