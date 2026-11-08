"""Motion for titles and transitions: plain functions that return Manim animations for self.play / self.say.

Title entrances take the Text or Paragraph that T() or P() built. Transitions are for chapter(transition=...)
or for self.play directly; the ones that move the old picture (zoom_through, whip) animate what you give them,
so pass VGroup(*self.stage()) to take the whole stage."""
from __future__ import annotations

import itertools
import math

import numpy as np
from manim import (
    LEFT,
    UP,
    AnimationGroup,
    Circle,
    FadeIn,
    FadeOut,
    Paragraph,
    Rectangle,
    ReplacementTransform,
    Succession,
    UpdateFromAlphaFunc,
    config,
    linear,
    rush_into,
    smooth,
)

from .colours import ACCENT, BG, MUTED, interpolate_color

COVER = 100  # z-index of a full-frame cover: above everything on the stage


def _tag(obj, kind):
    """Remember which helper made `obj`, so the layout snapshot can name the transition."""
    obj.mv_kind = kind
    return obj


def _units(mob):
    """The words of a Text or Paragraph as [(word, glyphs)]. Manim keeps an invisible zero-size mark for each
    space, which ends a word; where it keeps none, a line break or a wide gap does."""
    lines = [list(line.submobjects) for line in mob.submobjects] if isinstance(mob, Paragraph) else [list(mob.submobjects)]
    groups = []
    for glyphs in lines:
        marked = any(g.width < 1e-6 for g in glyphs)
        gap = 0.22 * max((g.height for g in glyphs), default=0)
        group, prev = [], None
        for g in glyphs:
            blank = g.width < 1e-6
            wrapped = prev is not None and g.get_left()[0] < prev.get_left()[0]  # a new line of a wrapped Text
            if group and (blank or wrapped or (not marked and prev is not None and g.get_left()[0] - prev.get_right()[0] > gap)):
                groups.append(group)
                group = []
            if not blank:
                group.append(g)
            prev = g
        if group:
            groups.append(group)
    # .text has the spaces stripped; original_text keeps them
    src = mob.lines_text if isinstance(mob, Paragraph) else mob
    text = getattr(src, "original_text", None) or getattr(src, "text", "")
    words = text.split()
    if len(words) != len(groups):
        words = [""] * len(groups)  # accent_word cannot name them, the entrances still work
    return list(zip(words, groups))


def _stagger(mob, units, start, lift, run_time):
    """Reveal `units` (lists of glyphs) one after another, each from `start` colour to its own, from
    transparent to opaque, rising `lift` scene units as it lands."""
    final = [[(g.get_fill_color(), g.get_fill_opacity()) for g in u] for u in units]
    n = len(units)
    win = 1 / (1 + (n - 1) * 0.4)  # each unit's share of the run; the next starts 40% into it
    lifted = [0.0] * n

    def at(m, alpha):
        for i, u in enumerate(units):
            a = min(1.0, max(0.0, (alpha - i * 0.4 * win) / win))
            for g, (col, op) in zip(u, final[i]):
                g.set_fill(interpolate_color(start, col, a), op * a)
            if lift:
                d = lift * (1 - a)
                for g in u:
                    g.shift(UP * (lifted[i] - d))
                lifted[i] = d

    return UpdateFromAlphaFunc(mob, at, introducer=True, rate_func=linear, run_time=run_time)


def words_in(text_mob, color=MUTED, run_time=None):
    """Each word fades from `color` (muted) to its ink, one after another, with no movement."""
    units = [g for _w, g in _units(text_mob)]
    if not units:
        return FadeIn(text_mob)
    return _tag(_stagger(text_mob, units, color, 0.0, run_time or 0.25 * len(units) + 0.4), "words_in")


def letters_in(text_mob, color=MUTED, run_time=None):
    """Each letter fades from muted to ink in turn, rising a hair as it lands."""
    units = [[g] for _w, glyphs in _units(text_mob) for g in glyphs]
    if not units:
        return FadeIn(text_mob)
    return _tag(_stagger(text_mob, units, color, 0.08, run_time or 0.05 * len(units) + 0.5), "letters_in")


def blur_in(mob, run_time=0.8):
    """Fade in while settling from 1.04 times its size: a blur-in without the blur."""
    return _tag(FadeIn(mob, scale=1.04, run_time=run_time), "blur_in")


def slot(options, final, step=0.12):
    """Roll through the `options` (mobjects) in one place, each flicking past the last, and land on `final`."""
    shown = [*options, final]
    for m in shown:
        m.move_to(final)
    seq = [FadeIn(shown[0], shift=UP * 0.25, run_time=step if options else 0.3)]
    for out, into in itertools.pairwise(shown):
        t = step * 2 if into is final else step
        seq.append(AnimationGroup(FadeOut(out, shift=UP * 0.25, run_time=t), FadeIn(into, shift=UP * 0.25, run_time=t)))
    return _tag(Succession(*seq), "slot")


def accent_word(text_mob, word, colour=ACCENT, run_time=0.5):
    """Recolour one word of the text to `colour`."""
    want = word.strip().lower().strip(".,;:!?\"'")
    hit = [g for w, g in _units(text_mob) if w.lower().strip(".,;:!?\"'") == want]
    if not hit:
        raise ValueError(f"accent_word: {word!r} is not a word of that text")
    glyphs = [g for u in hit for g in u]
    start = [g.get_fill_color() for g in glyphs]

    def at(m, alpha):
        for g, c in zip(glyphs, start):
            g.set_fill(interpolate_color(c, colour, alpha))

    return _tag(UpdateFromAlphaFunc(text_mob, at, rate_func=smooth, run_time=run_time), "accent_word")


# ------------------------------------------------------------ transitions
def _frame():
    return config.frame_width + 0.2, config.frame_height + 0.2


def _cover(colour, opacity=1.0):
    w, h = _frame()
    return Rectangle(width=w, height=h, fill_color=colour, fill_opacity=opacity, stroke_width=0).set_z_index(COVER)


def zoom_through(mob, run_time=0.9):
    """Dive into `mob`: scale it about its own centre until it fills the frame, then fade to the background.
    Pass VGroup(*self.stage()) to dive with the whole stage."""
    centre = mob.get_center()
    big = 3 * max(config.frame_width / max(mob.width, 1e-3), config.frame_height / max(mob.height, 1e-3))
    start = mob.copy()
    cover = _cover(BG, 0.0)

    def grow(m, alpha):
        m.become(start).scale(big ** alpha, about_point=centre)

    def fade(m, alpha):
        m.set_fill(BG, min(1.0, max(0.0, (alpha - 0.5) * 2)))

    return _tag(AnimationGroup(UpdateFromAlphaFunc(mob, grow, rate_func=rush_into, run_time=run_time),
                               UpdateFromAlphaFunc(cover, fade, introducer=True, rate_func=linear, run_time=run_time)),
                "zoom_through")


def flood(mob, colour, run_time=0.7):
    """A rectangle of `colour` grows from `mob` until it fills the frame."""
    w, h = _frame()
    c0, w0, h0 = mob.get_center(), max(mob.width, 0.05), max(mob.height, 0.05)
    rect = _cover(colour)

    def grow(m, alpha):
        m.stretch_to_fit_width(w0 + (w - w0) * alpha).stretch_to_fit_height(h0 + (h - h0) * alpha)
        m.move_to(c0 * (1 - alpha))

    return _tag(UpdateFromAlphaFunc(rect, grow, introducer=True, rate_func=smooth, run_time=run_time), "flood")


def iris(point, colour=BG, run_time=0.8):
    """A circle grows from `point` (a position or a mobject) until it covers the frame."""
    p = np.array(point.get_center() if hasattr(point, "get_center") else point, dtype=float)
    reach = 2 * (math.hypot(abs(p[0]) + config.frame_width / 2, abs(p[1]) + config.frame_height / 2) + 0.2)
    disc = Circle(radius=1, fill_color=colour, fill_opacity=1, stroke_width=0).set_z_index(COVER)

    def grow(m, alpha):
        m.set_width(max(0.02, reach * alpha)).move_to(p)

    return _tag(UpdateFromAlphaFunc(disc, grow, introducer=True, rate_func=smooth, run_time=run_time), "iris")


def whip(direction=LEFT, mobs=None, run_time=0.25):
    """Throw the picture out of the frame in `direction` in a quarter of a second, accelerating.
    With `mobs` it returns the animation. Without, it returns a function of the stage's mobjects
    that chapter(transition=...) calls for you."""
    def build(items):
        anims = [m.animate.shift(direction * (config.frame_width + 2)).build().set_rate_func(rush_into)
                 for m in items]
        return _tag(AnimationGroup(*anims, run_time=run_time), "whip")

    if mobs is not None:
        return build(mobs)
    return _tag(build, "whip")


def morph(a, b):
    """`a` becomes `b` where they are."""
    return _tag(ReplacementTransform(a, b), "morph")


def dip(run_time=0.5):
    """A brief dip to black: the frame darkens to 40% and comes back."""
    shade = _cover("#000000", 0.0)

    def at(m, alpha):
        m.set_fill("#000000", 0.4 * math.sin(math.pi * alpha))

    return _tag(UpdateFromAlphaFunc(shade, at, introducer=True, remover=True, rate_func=linear, run_time=run_time),
                "dip")


def carry(mob, to, run_time=0.8):
    """Move `mob` onto `to` (a point or a mobject), scaling to its size when it is a mobject."""
    if hasattr(to, "get_center"):
        k = to.width / mob.width if mob.width > 1e-6 else 1.0
        target = mob.animate.scale(k).move_to(to)
    else:
        target = mob.animate.move_to(to)
    return _tag(target.build().set_run_time(run_time), "carry")


__all__ = ["accent_word", "blur_in", "carry", "dip", "flood", "iris", "letters_in", "morph", "slot", "whip",
           "words_in", "zoom_through"]
