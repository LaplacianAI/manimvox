"""The manimvox logo animation and the social preview card, drawn with Manim from docs/assets/logo.svg.

Rendered by build.py, which sets MANIMVOX_BRAND_TILES to the montage frames the card shows.
"""

import os
from pathlib import Path

from manim import *

from manimvox.kit import ACCENT, INK, MUTED, TEAL, T

ROOT = Path(__file__).resolve().parents[2]
LOGO = ROOT / "docs" / "assets" / "logo.svg"
BG = "#111417"  # the badge's own colour, so the mark sits on it without an edge

if "MANIMVOX_BRAND_TILES" in os.environ:  # the card: 2:1, laid out on a 16 x 8 frame
    config.frame_width, config.frame_height = 16, 8


def logo(height):
    """The logo at `height` scene units: badge, "m" arches, waveform bars. Manim's SVG import drops stroke
    widths, so the strokes are set again here, 5/64 of the height as in the SVG."""
    m = SVGMobject(str(LOGO)).scale_to_fit_height(height)
    badge, arches, bars = m[0], m[1], m[2]
    width = height * 5 / 64 * 100  # Manim stroke units are 1/100 of a scene unit
    for part, colour in ((arches, ACCENT), (bars, TEAL)):
        part.set_fill(opacity=0).set_stroke(colour, width=width, opacity=1)
        part.cap_style = CapStyleType.ROUND
        part.joint_type = LineJointType.ROUND
    badge.set_stroke(width=0)
    return m


class Intro(Scene):
    """The README GIF's opening: the arches draw, the bars grow and pulse, the name writes in."""

    def construct(self):
        self.camera.background_color = BG
        mark = logo(3.8)
        badge, arches, bars = mark
        name = T("manimvox", 64, INK, weight=BOLD).next_to(mark, RIGHT, buff=0.5).shift(UP * 0.35)
        tag = T("Explainer videos made by your AI agent", 26, ACCENT).next_to(name, DOWN, buff=0.22,
                                                                              aligned_edge=LEFT)
        group = Group(mark, name, tag)
        group.shift(-group.get_center())
        self.play(FadeIn(badge, scale=0.9), run_time=0.4)
        self.play(Create(arches), run_time=0.9, rate_func=smooth)
        self.play(GrowFromCenter(bars), run_time=0.6)
        self.play(Write(name), run_time=0.8)
        self.play(FadeIn(tag, shift=UP * 0.1), run_time=0.5)
        self.play(bars.animate(rate_func=there_and_back).stretch(1.25, 1), run_time=0.8)
        self.wait(0.8)


class Card(Scene):
    """The 1280x640 social preview: the logo and tagline, beside four frames of what manimvox draws."""

    def construct(self):
        self.camera.background_color = BG
        mark = logo(1.9)
        name = T("manimvox", 66, INK, weight=BOLD).next_to(mark, RIGHT, buff=0.25)
        head = Group(mark, name)
        head.move_to([0, 2.0, 0]).to_edge(LEFT, buff=0.55)
        tag = T("Explainer videos made\nby your AI agent", 36, ACCENT, weight=BOLD)
        tag.next_to(head, DOWN, buff=0.45).align_to(head, LEFT).shift(RIGHT * 0.3)
        steps = T("research · cited script · Manim animation\nnarration · checks", 24, MUTED)
        steps.next_to(tag, DOWN, buff=0.4).align_to(tag, LEFT)
        cmd = T("pip install manimvox", 26, INK, font="Consolas").next_to(steps, DOWN, buff=0.55).align_to(tag, LEFT)
        tiles = ImageMobject(os.environ["MANIMVOX_BRAND_TILES"]).scale_to_fit_width(7.3).move_to([4.05, 0.05, 0])
        frame = SurroundingRectangle(tiles, buff=0.0, corner_radius=0.12).set_stroke(MUTED, 1.5, 0.5)
        bar = Rectangle(width=16, height=0.08, fill_color=ACCENT, fill_opacity=1, stroke_width=0).to_edge(DOWN, buff=0)
        self.add(head, tag, steps, cmd, tiles, frame, bar)
