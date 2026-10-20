"""Theme roles as the module constants episodes use (ACCENT, BG, …, plus named colours)."""
from __future__ import annotations

import manim

from ._context import THEME

BG = THEME["bg"]
PANEL = THEME["panel"]
PANEL2 = THEME["panel2"]
LINE = THEME["line"]
INK = THEME["ink"]
MUTED = THEME["muted"]
ACCENT = THEME["accent"]
OK = THEME["ok"]
WARN = THEME["warn"]
ERROR = THEME["error"]
CODE_BG = THEME["code_bg"]
BLUE = THEME["blue"]
ORANGE = THEME["orange"]
VIOLET = THEME["violet"]
PINK = THEME["pink"]
TEAL = THEME["teal"]
NAMED = {k.upper(): v for k, v in THEME.named.items()
         if k.upper() not in globals() and not hasattr(manim, k.upper())}
globals().update(NAMED)


# The theme colours above are "#RRGGBB" strings; Manim's own versions of these two need ManimColor objects.
def interpolate_color(color1, color2, alpha: float) -> manim.ManimColor:
    """The colour `alpha` of the way from `color1` to `color2` (0 to 1); either may be a hex string."""
    return manim.ManimColor(color1).interpolate(manim.ManimColor(color2), alpha)


def invert_color(color) -> manim.ManimColor:
    """The opposite of `color`, which may be a hex string."""
    return manim.ManimColor(color).invert()
