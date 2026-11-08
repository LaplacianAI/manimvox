"""One sample tile per chapter transition, and the call that plays each: zoom, flood, iris, whip, dip."""
from manimvox.kit import *

KINDS = ("zoom", "flood", "iris", "whip", "dip")


def transition_tile(kind, color=ACCENT):
    """A small labelled tile for the transition `kind` (zoom, flood, iris, whip or dip), to leave the stage through."""
    return node(kind.upper(), "chapter seam", w=2.2, color=color)


def seam(kind, tile, color=ACCENT):
    """The transition `kind` for chapter(transition=...), taking off from `tile`: the animation to hand to chapter()."""
    if kind == "zoom":
        return zoom_through(tile)
    if kind == "flood":
        return flood(tile, color)
    if kind == "iris":
        return iris(tile.get_center())
    if kind == "whip":
        return whip(LEFT)
    if kind == "dip":
        return dip()
    raise ValueError(f"seam: kind must be one of {', '.join(KINDS)}, got {kind!r}")
