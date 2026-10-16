"""Text helpers sized for a 1080p stage."""
from __future__ import annotations

import sys
import textwrap

from manim import NORMAL, UP, MarkupText, Paragraph, Text, VectorizedPoint

from ._context import PROJECT, THEME

FONT = THEME.font
MONO = THEME.mono
ARABIC = {"darwin": "Geeza Pro", "win32": "Segoe UI"}.get(sys.platform, "Noto Naskh Arabic")
INK = THEME["ink"]

if THEME.font_files:
    import manimpango

    for _f in THEME.font_files:
        if not manimpango.register_font(str((PROJECT.root / _f).resolve())):
            raise SystemExit(f"font file did not register: {_f}")

# Safe stage: keep content inside x in [-6.6, 6.6], y in [-3.45, 3.15].
SAFE_W = 13.2
SAFE_H = 6.6
STAGE_TOP = 3.15
STAGE_BOTTOM = -3.45
STAGE_CENTER = UP * ((STAGE_TOP + STAGE_BOTTOM) / 2)

# Average glyph width per font-size point, measured once (used for wrapping).
_probe = Text("the quick brown fox jumps over a lazy dog 0123", font=FONT, font_size=48)
_CW = _probe.width / 46 / 48 * 0.92


# -------------------------------------------------------------------- text
def T(s, size=28, color=INK, weight=NORMAL, font=FONT, max_w=None, slant=NORMAL):
    """One line of text. `max_w` shrinks it to fit (never grows)."""
    if not str(s).strip():  # an empty Text has no points and breaks every layout call
        return VectorizedPoint()
    t = Text(str(s), font=font, font_size=size, color=color, weight=weight, slant=slant)
    if max_w and t.width > max_w:
        t.scale_to_fit_width(max_w)
    return t


def P(s, size=22, color=INK, max_w=6.0, weight=NORMAL, align="left", font=FONT):
    """A wrapped paragraph that fits inside `max_w` scene units."""
    chars = max(8, int(max_w / (_CW * size)))
    lines = []
    for raw in str(s).split("\n"):
        lines += textwrap.wrap(raw, chars) or [""]
    if align == "center" and len(lines) > 1:
        t = Paragraph(*lines, alignment="center", font=font, font_size=size, color=color, weight=weight,
                      disable_ligatures=True)
    else:
        t = Text("\n".join(lines), font=font, font_size=size, color=color, weight=weight)
    if t.width > max_w:
        t.scale_to_fit_width(max_w)
    return t


def AR(s, size=28, color=INK, weight=NORMAL, max_w=None):
    """Arabic text (shaped right-to-left by Pango). Uses MarkupText: plain
    `Text` drops every Arabic glyph in this Manim build."""
    safe = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = MarkupText(safe, font=ARABIC, font_size=size, color=color, weight=weight)
    if max_w and t.width > max_w:
        t.scale_to_fit_width(max_w)
    return t


def fit(mob, max_w=SAFE_W, max_h=SAFE_H):
    """Scale a mobject down (never up) so it fits the stage."""
    if mob.width > max_w:
        mob.scale_to_fit_width(max_w)
    if mob.height > max_h:
        mob.scale_to_fit_height(max_h)
    return mob
