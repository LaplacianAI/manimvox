"""The opening and chapter 1, the edit file: four broken recordings, the question, the route; then what an edit file
is, its three lists, the two clocks, probe and check edit, and the mistake of placing an overlay by the raw file's
time. Script: episodes/tour.md. Terminal output is real (build/said.json)."""
from bench import *

CHAPTERS = ["the edit file", "cut by words", "captions", "joining", "frame and speed", "over the picture",
            "your own code", "sound", "colour", "green screen", "steady", "two cameras", "render and share"]

FIRST = """\
{
  "segments": [
    {"title": "An interview", "seconds": 4},
    {"clip": "interview.webm",
     "start": 2.5, "end": 12, "transition": "fade"}
  ],
  "overlays": [
    {"text": "Prof Joyeeta Gupta",
     "sub": "University of Amsterdam and UNESCO-IHE",
     "at": 4.1, "until": 9}
  ],
  "audio": [
    {"music": "build/pad.wav", "volume": -26}
  ]
}"""


def tile(mob, text):
    """A label laid on the bottom left of a grid tile, on a dark band so it reads over any footage."""
    t = T(text, 22, INK)
    band = BackgroundRectangle(t, color=BG, fill_opacity=0.82, buff=0.12)
    g = VGroup(band, t)
    g.move_to(mob.get_corner(DL) + UR * 0.1, aligned_edge=DL)
    return g


class Ep01(Bench):
    EP = 1
    TITLE = "The edit file"

    def build(self):
        # ---- the opening: four broken recordings, on frame 0
        w = 5.6
        talk = footage(INTERVIEW, 12.5, 23.0, w)
        shake = footage(DEMOLITION, 12.0, 28.0, w)
        green = footage(CHROMA, 72.0, 77.0, w)
        wide = footage(CAMERAS[0], 8.0, 16.0, w / 2 - 0.05)
        close = footage(CAMERAS[1], 8.0, 16.0, w / 2 - 0.05)
        street = Group(wide, close).arrange(RIGHT, buff=0.1)
        grid = Group(talk, shake, green, street).arrange_in_grid(2, 2, buff=(0.3, 0.3)).move_to(UP * 0.05)
        street.match_y(green)
        for m in (talk, shake, green, wide, close):
            m.clip.loop()
        self.add(grid)
        labels = [tile(talk, "long pauses, and an “um”"), tile(shake, "a shaking hand"),
                  tile(green, "a green sheet, no mountain"), tile(street, "two cameras, one moment")]

        self.say("Here are four real recordings, and each one has a problem. The interview has long pauses, "
                 "and the interviewer says um in the middle of a question.", FadeIn(labels[0]), run_time=1.0)
        self.steps("The demolition was filmed by a hand that shakes. The green-screen shoot has a bright green "
                   "sheet where a mountain should be.", [FadeIn(labels[1]), FadeIn(labels[2])])
        self.say("And the street was filmed by two cameras, which have to be lined up before you can cut between "
                 "them.", FadeIn(labels[3]))
        self.beat(0.6)

        q = T("How do you fix all four, with one text file?", 40, INK, weight=BOLD)
        band = Rectangle(width=FW, height=q.height + 0.7, stroke_width=0, fill_color=BG, fill_opacity=0.9)
        ask = VGroup(band, q)
        self.say("How do you fix all four, and make one film of them, with nothing but a text file? By the end "
                 "you'll be able to write that file yourself.", FadeIn(band), AddTextLetterByLetter(q, time_per_char=0.035),
                 run_time=1.8)

        chips = VGroup(*[VGroup(RoundedRectangle(corner_radius=0.08, width=1.72, height=0.5, fill_color=PANEL,
                                                 fill_opacity=1, stroke_color=LINE, stroke_width=1.2),
                                T(name, 16, MUTED, max_w=1.6)) for name in CHAPTERS])
        for c in chips:
            c[1].move_to(c[0])
        route = VGroup(VGroup(*chips[:7]).arrange(RIGHT, buff=0.12),
                       VGroup(*chips[7:]).arrange(RIGHT, buff=0.12)).arrange(DOWN, buff=0.14)
        route.to_edge(DOWN, buff=0.45)
        self.say("We'll go one tool at a time: what it does, the line you write, the result, and the mistake "
                 "people make with it.",
                 FadeOut(ask), FadeOut(VGroup(*labels)), grid.animate.scale(0.72).shift(UP * 0.95),
                 LaggedStart(*[FadeIn(c) for c in chips], lag_ratio=0.08), run_time=2.0)
        self.beat(0.5)

        # ---- chapter 1: the edit file
        title, enter = self.heading("The edit file", "words")
        edit = EditPanel(FIRST, "edits/first.json", size=19, w=6.4).move_to(RIGHT * 3.3 + DOWN * 0.25)
        edit.hide()
        for m in (talk, shake, green, wide, close):
            m.clip.clear_updaters()
        self.play(chips[0][0].animate.set_stroke(ACCENT, 2.5), chips[0][1].animate.set_color(INK), run_time=0.6)
        self.say("Everything starts with an edit file, a plain text file in your project's edits folder. You can "
                 "write it in JSON, or in Python if you'd rather.",
                 FadeOut(route), FadeOut(grid), enter, FadeIn(edit.bg), FadeIn(edit.head), run_time=1.2)

        segs, overs, auds = range(1, 6), range(6, 11), range(11, 14)
        self.play(*edit.light(0, 14), run_time=0.6)
        self.steps("It has three lists. Segments play one after another, like clips on a timeline. Overlays sit on "
                   "top of the picture, and audio is everything you hear.",
                   [edit.light(*segs), edit.light(*overs), edit.light(*auds)], run_time=0.9)

        # the two clocks, drawn as a timeline under nothing but seconds of the film
        x0, sec = -6.5, 0.46  # where 0 s is, and scene units a second
        def span(a, b, y, colour, text, h=0.5):
            r = RoundedRectangle(corner_radius=0.06, width=(b - a) * sec, height=h, fill_color=colour,
                                 fill_opacity=0.35, stroke_color=colour, stroke_width=1.5)
            r.move_to([x0 + (a + b) / 2 * sec, y, 0])
            return VGroup(r, T(text, 18, INK).move_to(r))
        card = span(0, 4, 0.2, ORANGE, "title")
        clip = span(3.5, 13, 0.2, BLUE, "clip: file 2.5 s to 12 s")
        name = span(4.1, 9, 1.0, VIOLET, "her name", h=0.42)
        music = span(0, 13, -0.6, MUTED, "music", h=0.32)
        axis = VGroup(Line([x0, -1.15, 0], [x0 + 13 * sec, -1.15, 0], color=LINE, stroke_width=2))
        for s in (0, 4, 8, 12):
            axis.add(T(f"{s}", 16, MUTED).move_to([x0 + s * sec, -1.42, 0]))
        axis.add(T("seconds of the film", 18, MUTED).next_to(axis[0], DOWN, buff=0.45).align_to(axis[0], LEFT))
        timeline = VGroup(music, card, clip, name, axis)
        self.say("Times for overlays and sound are seconds of the finished film. Times inside a clip are seconds "
                 "of its own file.", *edit.light("\"at\": 4.1", "\"start\": 2.5"),
                 LaggedStart(Create(axis), FadeIn(card), FadeIn(clip), FadeIn(name), FadeIn(music), lag_ratio=0.2),
                 run_time=2.0)
        self.beat(0.4)

        # probe, then check edit: real output
        probe = Terminal("manimvox edit probe interview.webm", SAID["probe"][:1] + ["sheets: sheets/probe/…/s_01.png"],
                         w=6.2, size=16).move_to(LEFT * 3.4 + UP * 1.6)
        sheet = screenshot(HERE / "sheets/probe/Interview_Prof_Joyeeta_Gupta_on_strengthening_water_governance_"
                                  "education_and_research/s_01.png", width=4.4)
        sheet.next_to(probe, DOWN, buff=0.3).align_to(probe, LEFT)
        self.play(FadeOut(timeline), *edit.plain(), run_time=0.5)
        self.say("Before you cut anything, you look. The probe command tells you a file's length, size and sound, "
                 "and writes contact sheets, grids of frames so you can see where things happen.",
                 *probe.run(), FadeIn(sheet), run_time=2.4)

        check = Terminal("manimvox check edit first", SAID["check_first"], w=6.2, size=16)
        check.move_to(LEFT * 3.4 + DOWN * 0.2)
        self.say("Then check edit reads your file against the real footage, and says where every piece lands on the "
                 "finished film, before anything is rendered.",
                 FadeOut(sheet), probe.animate.shift(UP * 0.2).set_opacity(0.35), *check.run(), run_time=2.2)
        landing = SurroundingRectangle(check.out[1], color=ACCENT, buff=0.06, stroke_width=2)
        self.play(Create(landing), run_time=0.5)

        mistake = Mistake('"at": 3.1    her name, 3.1 s into the file', '"at": 4.1    3.5 + (3.1 − 2.5) on the film',
                          SAID["check_first"][1], w=6.2, size=20)
        mistake.next_to(check, DOWN, buff=0.45).align_to(check, LEFT)
        self.play(FadeOut(probe), Group(check, landing).animate.shift(UP * 1.8), run_time=0.6)
        mistake.next_to(check, DOWN, buff=0.45).align_to(check, LEFT)
        self.say("The mistake here is placing an overlay by a time in the raw file.", *mistake.wrong_in(),
                 *edit.light("\"at\": 4.1"), run_time=1.2)
        self.say("Overlays use the film's clock, so read their times from check edit.", *mistake.struck(),
                 *mistake.fixed(), run_time=1.6)
        self.beat(1.0)

        self.say("So the file says what plays, what sits on top, and what you hear, and check edit tells you where "
                 "it all lands.", *edit.plain(), FadeOut(mistake), FadeOut(landing), check.animate.set_opacity(0.4),
                 run_time=0.8)
        nxt = footage(INTERVIEW, 12.5, 23.0, CLIP_W).move_to(CLIP_AT)
        self.play(FadeOut(check), FadeOut(edit), FadeOut(title), FadeIn(nxt), run_time=1.0)
        tag = VGroup(T("next", 22, MUTED), T("Cut by what is said", 30, INK, weight=BOLD)).arrange(DOWN, aligned_edge=RIGHT,
                                                                                                   buff=0.1)
        tag.move_to([6.2, -3.0, 0], aligned_edge=RIGHT)
        self.say("Next, cutting by what is said.", blur_in(tag))
        self.beat(0.6)
        self.play(*[FadeOut(m) for m in self.stage()], run_time=0.8)
        self.beat(0.4)
