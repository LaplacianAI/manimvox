"""Theme roles as the module constants episodes use (ACCENT, BG, …, plus named colours)."""
from __future__ import annotations

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
NAMED = {k.upper(): v for k, v in THEME.named.items() if k.upper() not in globals()}
globals().update(NAMED)
