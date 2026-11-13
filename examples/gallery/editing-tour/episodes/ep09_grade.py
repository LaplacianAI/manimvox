"""Chapter 9, colour: the 0.8.5 half opens after a dip. The demolition looks flat; grade's controls one by one
beside small swatches (exposure, temperature, tint; lift, gamma, gain, contrast, saturation), a LUT (looks/film.cube,
17 x 17 x 17, its real colours sampled), before and after, and the letterbox worry (only the picture is graded).
Script: episodes/tour.md. The values on the panel are make_edit.GRADE."""
from bench import *

GRADE_SRC = """\
{"clip": "demolition.webm",
 "start": 3, "end": 13,
 "grade": {
   "exposure": 0.15,
   "temperature": 0.1,
   "contrast": 1.15,
   "saturation": 1.2,
   "lut": "looks/film.cube"
 }}"""

DARK, LIGHT = "#2B3640", "#E6EEF2"


def strip(colors, w=1.2, h=0.26):
    """A small swatch: a row of cells running through `colors`."""
    n = 10
    cells = VGroup(*[Rectangle(width=w / n, height=h, stroke_width=0, fill_opacity=1,
                               fill_color=interpolate_color(ManimColor(colors[0]), ManimColor(colors[-1]), k / (n - 1)))
                     for k in range(n)]).arrange(RIGHT, buff=0)
    return VGroup(cells, SurroundingRectangle(cells, color=LINE, buff=0, stroke_width=1.2))


def chip(name, colors, mark=None):
    """A control's name over its swatch; `mark` (0, 1 or 2) rings the shadows, mid-tones or highlights."""
    s = strip(colors)
    if mark is not None:
        third = s.width / 3
        ring = Rectangle(width=third, height=s.height + 0.08, color=ACCENT, stroke_width=2.5)
        ring.move_to(s.get_left() + RIGHT * (third * (mark + 0.5)))
        s.add(ring)
    label = T(name, 18, MUTED)
    return VGroup(label, s).arrange(DOWN, buff=0.1)


def film_cube(n=4, cell=0.19):
    """A slice of looks/film.cube's real colours: `n` x `n` samples of its 17 x 17 x 17 table."""
    rows = [ln.split() for ln in (HERE / "looks" / "film.cube").read_text().splitlines()
            if ln and (ln[0].isdigit() or ln[0] == "-")]
    cells = []
    for g in reversed(range(n)):
        for r in range(n):
            ri, gi, bi = round(r * 16 / (n - 1)), round(g * 16 / (n - 1)), 11
            c = [min(1.0, max(0.0, float(v))) for v in rows[ri + 17 * gi + 289 * bi]]
            cells.append(Square(cell, stroke_width=0, fill_opacity=1, fill_color=rgb_to_color(c)))
    return VGroup(*cells).arrange_in_grid(n, n, buff=0.03)


class Ep09(Bench):
    EP = 9
    TITLE = "Colour"

    def build(self):
        title, enter = self.heading("Colour", "blur")
        clip = footage(DEMOLITION, 3.0, 13.0, CLIP_W).move_to(CLIP_AT)
        clip.clip.loop()
        panel = EditPanel(GRADE_SRC, "edits/tour.json", size=19, w=5.6).move_to(PANEL_AT + RIGHT * 0.25)
        warm = Rectangle(width=clip.width, height=clip.height, stroke_width=0, fill_color=ORANGE,
                         fill_opacity=0).move_to(clip)

        # ---- the 0.8.5 half opens after a dip in the edit
        self.say("Welcome to the new tools. The first one is colour.", dip(0.6), enter, FadeIn(clip), FadeIn(panel),
                 run_time=1.2)
        self.say("The demolition looks hazy and flat. Grade corrects a segment's colour.", run_time=0.4)
        self.play(*panel.light("\"grade\""), run_time=0.6)
        self.add(warm)

        # ---- the first three controls
        e, tm, ti = (chip("exposure", [DARK, LIGHT]), chip("temperature", [BLUE, ORANGE]),
                     chip("tint", ["#C25FB0", OK]))
        row1 = VGroup(e, tm, ti).arrange(RIGHT, buff=0.6).move_to([CLIP_AT[0], -2.8, 0])
        self.steps("Exposure brightens or darkens in stops. Temperature warms or cools, and tint moves between "
                   "magenta and green.",
                   [[FadeIn(e), *panel.light("\"exposure\"")],
                    [FadeIn(tm), *panel.light("\"temperature\"")],
                    [FadeIn(ti), *panel.light("\"grade\"")]])

        # ---- the next five
        names = [chip("lift", [DARK, LIGHT], 0), chip("gamma", [DARK, LIGHT], 1), chip("gain", [DARK, LIGHT], 2),
                 chip("contrast", ["#3A4650", "#CBD5DB"]), chip("saturation", ["#8A949A", "#F0A24A"])]
        row2 = VGroup(*names).arrange(RIGHT, buff=0.3).move_to([CLIP_AT[0], -2.8, 0])
        self.steps("Lift, gamma and gain move the shadows, the mid-tones and the highlights. Contrast and "
                   "saturation do what they say.",
                   [[FadeOut(row1), FadeIn(VGroup(*names[:3])), *panel.light("\"grade\"")],
                    [FadeIn(names[3]), *panel.light("\"contrast\"")],
                    [FadeIn(names[4]), *panel.light("\"saturation\"")]])

        # ---- the LUT: its real colours, then the picture warmer
        cube = film_cube()
        cube.move_to([CLIP_AT[0] - 2.2, -2.85, 0])
        cube_note = T("looks/film.cube", 20, MUTED, font=MONO).next_to(cube, RIGHT, buff=0.3)
        self.say("And a LUT, a look-up table file that many cameras and colour tools use, adds a look on top, "
                 "applied last.", FadeOut(row2), *panel.light("\"lut\""), FadeIn(cube), FadeIn(cube_note),
                 run_time=1.4)
        sketch = T("sketch of the look", 20, MUTED).next_to(clip, UP, buff=0.12).align_to(clip, RIGHT)
        self.play(warm.animate.set_fill(opacity=0.16), FadeIn(sketch), run_time=1.4)
        self.beat(0.4)
        self.play(FadeOut(warm), FadeOut(sketch), run_time=0.4)
        clip.clip.clear_updaters()
        self.show_result("r09", lead=clip)
        clip.clip.loop()

        # ---- before and after
        clip.clip.clear_updaters()
        pair, tags = before_after(footage(DEMOLITION, 3.0, 13.0), result("graded"))
        for m in pair:
            m.clip.loop()
        self.say("Before, and after.", FadeOut(clip), FadeOut(panel), FadeOut(cube), FadeOut(cube_note),
                 FadeIn(pair), FadeIn(tags), run_time=1.0)
        self.beat(3.0)
        for m in pair:
            m.clip.clear_updaters()

        # ---- the mistake: a worry that the letterbox bars are tinted too
        frame_w, pic_w = 5.6, 5.6
        pic = footage(DEMOLITION, 3.0, 13.0, pic_w)
        bar_h = 0.45
        bars = VGroup(*[Rectangle(width=frame_w, height=bar_h, stroke_width=0, fill_color=PANEL2, fill_opacity=1)
                        for _ in range(2)])
        bars[0].next_to(pic, UP, buff=0)
        bars[1].next_to(pic, DOWN, buff=0)
        letterbox = Group(pic, bars, SurroundingRectangle(Group(pic, bars), color=LINE, buff=0, stroke_width=2))
        letterbox.move_to(LEFT * 3.3 + DOWN * 0.1)
        pic.clip.loop()
        tint = Rectangle(width=pic.width, height=pic.height, stroke_width=0, fill_color=ORANGE,
                         fill_opacity=0).move_to(pic)
        bar_tag = T("bars: the theme's colour", 20, MUTED).next_to(bars[1], DOWN, buff=0.15)
        mistake = Mistake("a grade tints the bars", "a grade touches only the picture", w=5.4, size=22)
        mistake.move_to(RIGHT * 3.4 + UP * 0.2)
        self.say("A common worry is that a grade tints the letterbox bars too.", FadeOut(pair), FadeOut(tags),
                 FadeIn(letterbox), FadeIn(bar_tag), *mistake.wrong_in(), run_time=1.4)
        self.add(tint)
        self.say("It doesn't: only the picture is graded.", *mistake.struck(),
                 tint.animate.set_fill(opacity=0.16), *mistake.fixed(), run_time=1.6)
        self.beat(1.0)

        # ---- takeaway, then the bridge to the green screen
        pic.clip.clear_updaters()
        self.remove(tint)
        panel2 = EditPanel(GRADE_SRC, "edits/tour.json", size=19, w=5.6).move_to(PANEL_AT + RIGHT * 0.25)
        self.say("So grade fixes and styles colour, and a LUT adds a look.", FadeOut(letterbox), FadeOut(bar_tag),
                 FadeOut(mistake), FadeIn(panel2), run_time=1.0)
        self.play(*panel2.light("\"grade\"", "\"exposure\"", "\"temperature\"", "\"contrast\"", "\"saturation\"",
                                "\"lut\""), run_time=0.6)
        nxt = footage(DEMOLITION, 3.0, 13.0).move_to(CLIP_AT)
        nxt.clip.loop()
        green = footage(CHROMA, 72.0, 77.0, 3.0).move_to(RIGHT * 3.55 + UP * 0.9)
        green.clip.loop()
        self.say("But the green-screen shoot needs more than colour.", FadeOut(panel2), FadeOut(title), FadeIn(nxt),
                 FadeIn(green), run_time=1.0)
        self.beat(0.4)
        nxt_tag = VGroup(T("next", 22, MUTED), T("Green screen", 30, INK, weight=BOLD)).arrange(DOWN, aligned_edge=RIGHT, buff=0.08)
        nxt_tag.move_to([6.2, -3.0, 0], aligned_edge=RIGHT)
        self.say("Next, green screen.", blur_in(nxt_tag), run_time=0.8)
        self.beat(0.6)
        nxt.clip.clear_updaters()
        green.clip.clear_updaters()
        self.play(*[FadeOut(m) for m in self.stage()], run_time=0.8)
        self.beat(0.4)
