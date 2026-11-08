"""An end card that is built, not shown: lines carried in word by word, then a rule wiped in under them."""
from manimvox.kit import *


def end_card(lines, rule=True):
    """Up to three centred lines, the first large, the rest muted. Returns a VGroup with .lines (one text per line)
    and .rule (or None), and .build() giving the steps for self.steps: the lines carried in together, then the
    rule wiped in from its centre."""
    lines = [lines] if isinstance(lines, str) else list(lines)
    if not 1 <= len(lines) <= 3:
        raise ValueError(f"end_card takes up to 3 lines, got {len(lines)}")
    texts = VGroup(*[P(s, 40 if i == 0 else 28, INK if i == 0 else MUTED, max_w=11.5,
                       weight=BOLD if i == 0 else NORMAL, align="center") for i, s in enumerate(lines)])
    texts.arrange(DOWN, buff=0.35)
    bar = Line(LEFT * 1.2, RIGHT * 1.2).set_stroke(ACCENT, 6) if rule else None
    g = VGroup(texts, *([bar] if bar is not None else [])).arrange(DOWN, buff=0.45)
    g.lines, g.rule = list(texts), bar
    g.build = lambda: [[words_in(t) for t in texts]] + ([GrowFromCenter(bar)] if bar is not None else [])
    return g
