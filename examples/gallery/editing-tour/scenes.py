"""A Manim scene laid over the footage with a transparent background: "scenes.py:Falling" in edits/tour.json.
It rings the towers as they fall in slow motion and says what is happening, and at what speed."""
from manim import DOWN, UP, BackgroundRectangle, Circle, Create, FadeIn, FadeOut, Scene, Text, VGroup

from manimvox.kit.text import FONT  # the theme's font, as the rest of the film

TEAL, INK = "#4FC3C9", "#E6EEF2"


class Falling(Scene):
    def construct(self):
        ring = Circle(radius=1.55, color=TEAL, stroke_width=6).move_to([0.6, 0.6, 0])
        label = VGroup(Text("four towers come down", font=FONT, font_size=40, color=INK, weight="BOLD"),
                       Text("slowed to 0.3x", font=FONT, font_size=32, color=TEAL)).arrange(DOWN, buff=0.15)
        label.next_to(ring, UP, buff=0.35)
        label = VGroup(BackgroundRectangle(label, color="#0E1822", fill_opacity=0.7, buff=0.2), label)
        self.play(Create(ring), run_time=0.8)
        self.play(FadeIn(label, shift=DOWN * 0.15), run_time=0.6)
        self.wait(4.4)
        self.play(FadeOut(ring), FadeOut(label), run_time=0.6)
