"""A title that arrives as type, not as a card: word by word, letter by letter, or settling in, with one word picked out."""
from manimvox.kit import *

STYLES = {"words": words_in, "letters": letters_in, "blur": blur_in}


def kinetic_title(text, sub=None, accent=None, size=52, max_w=11.5):
    """A centred title, and a muted line under it when `sub` is given. Returns a VGroup with .title and .sub (or None),
    .enter(style) giving the animation that brings the title in ("words", "letters" or "blur"), .land() giving the
    sub line's fade-in (an empty list without one), and .pick() giving the colour change that picks out the word
    `accent` once the title has landed."""
    title = P(text, size, INK, max_w=max_w, weight=BOLD, align="center")
    line = P(sub, 24, MUTED, max_w=max_w, align="center") if sub else None
    g = VGroup(title, *([line] if line is not None else [])).arrange(DOWN, buff=0.4)
    g.title, g.sub = title, line
    g.enter = lambda style="words": STYLES[style](title)
    g.land = lambda: [FadeIn(line, shift=UP * 0.15)] if line is not None else []
    g.pick = lambda: accent_word(title, accent)
    return g
