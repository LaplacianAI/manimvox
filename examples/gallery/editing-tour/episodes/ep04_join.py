"""Chapter 4, joining pieces: a segment begins with a cut, a fade or a dip (drawn to scale as two blocks on a
timeline, the overlap measured), a title card, an image with a move, an episode segment, from_video inside an
explainer, and the mistake of a fade on the first segment. The chapter plays its own result (the countdown,
a dip, a title card and the towers still) full frame. Script: episodes/tour.md."""
from bench import *

U = 1.2  # scene units a second on the timeline
X0 = -6.4  # where 0 s is
TOP, LOW = 0.7, -0.3  # the two rows of the timeline


def seg_src(kind):
    return f"""\
{{
  "segments": [
    {{"clip": "interview.webm",
     "start": 2.5, "end": 5}},
    {{"clip": "demolition.webm",
     "start": 12, "end": 14.5,
     "transition": "{kind}"}}
  ]
}}"""


TITLE_SRC = """\
{"title": "An interview",
 "lines": ["Prof Joyeeta Gupta",
           "UNESCO-IHE, 2013"],
 "seconds": 4}"""

IMAGE_SRC = """\
{"image": "build/towers.png",
 "seconds": 5,
 "move": "push"}"""

EPISODE_SRC = """\
{"episode": "ep01",
 "transition": "dip"}"""

CODE_SRC = """\
clip = from_video("demolition.webm",
                  start=12, end=20,
                  sound=True)"""


def next_tag(name):
    """The small "next" tag at the bottom right: where the playlist goes after this chapter."""
    return VGroup(T("next", 22, MUTED), T(name, 30, INK, weight=BOLD)).arrange(DOWN, aligned_edge=RIGHT, buff=0.08)\
        .move_to([6.2, -3.0, 0], aligned_edge=RIGHT)


def block(a, b, y, colour, text, h=0.8):
    r = RoundedRectangle(corner_radius=0.06, width=(b - a) * U, height=h, fill_color=colour, fill_opacity=0.35,
                         stroke_color=colour, stroke_width=1.5)
    r.move_to([X0 + (a + b) / 2 * U, y, 0])
    return VGroup(r, T(text, 18, INK).move_to(r))


def curves(kind):
    """Opacity of picture A (blue) and picture B (violet) across the overlap, in a small frame."""
    w, h = 2.6, 1.0
    box_ = Rectangle(width=w + 0.4, height=h + 0.5, stroke_color=LINE, stroke_width=1.5, fill_color=PANEL,
                     fill_opacity=1)
    ptsA = [(0, 1), (1, 0)] if kind == "fade" else [(0, 1), (0.5, 0), (1, 0)]
    ptsB = [(0, 0), (1, 1)] if kind == "fade" else [(0, 0), (0.5, 0), (1, 1)]
    o = box_.get_center() + np.array([-w / 2, -h / 2, 0])

    def line(pts, colour):
        return VMobject(color=colour, stroke_width=4).set_points_as_corners([o + np.array([x * w, y * h, 0])
                                                                           for x, y in pts])
    return VGroup(box_, line(ptsA, BLUE), line(ptsB, VIOLET))


class Ep04(Bench):
    EP = 4
    TITLE = "Joining pieces"

    def build(self):
        title, enter = self.heading("Joining pieces", "letters")

        # ---- the seam: a cut, a fade, a dip
        A = block(0, 2.5, TOP, BLUE, "interview")
        B = block(2.5, 5, LOW, VIOLET, "demolition")
        seam = DashedLine([X0 + 2.5 * U, TOP + 0.6, 0], [X0 + 2.5 * U, LOW - 0.6, 0], color=ACCENT, stroke_width=3)
        ed = EditPanel(seg_src("cut"), "edits/join.json", size=19).move_to(PANEL_AT)
        key = ed.find('"transition"')
        ed_fade = EditPanel(seg_src("fade"), size=19)
        ed_dip = EditPanel(seg_src("dip"), size=19)
        for e in (ed_fade, ed_dip):
            e.move_to(PANEL_AT)

        chips = VGroup()
        for name in ("cut", "fade", "dip"):
            b_ = RoundedRectangle(corner_radius=0.08, width=1.3, height=0.5, fill_color=PANEL, fill_opacity=1,
                                  stroke_color=LINE, stroke_width=1.5)
            chips.add(VGroup(b_, T(name, 20, INK, font=MONO).move_to(b_)))
        chips.arrange(RIGHT, buff=0.2).move_to([-3.4, 2.1, 0])

        def pick(k):
            return [c[0].animate.set_stroke(ACCENT if j == k else LINE, 3 if j == k else 1.5)
                    for j, c in enumerate(chips)]
        self.say("So far, one clip at a time. Now, how the pieces of a film join, and what else a piece can be.",
                 enter, run_time=1.2)
        self.steps("Each segment says how it begins after the one before: with a cut, a fade, or a dip.",
                   [[FadeIn(A), FadeIn(B), FadeIn(seam), FadeIn(ed), FadeIn(chips), *ed.light(key)],
                    pick(0), pick(1), pick(2)], run_time=0.9)
        self.say("A cut is the default.", *pick(0), run_time=0.6)

        length = T("the film: 5 s", 24, MUTED).move_to([X0, 1.5, 0], aligned_edge=LEFT)
        shift = 0.5 * U
        fade_curves = curves("fade").move_to([-3.4, -2.35, 0])
        dip_curves = curves("dip").move_to([-3.4, -2.35, 0])
        legend = VGroup(T("A", 18, BLUE, weight=BOLD), T("B", 18, VIOLET, weight=BOLD)).arrange(RIGHT, buff=0.2)
        legend.next_to(fade_curves, RIGHT, buff=0.2)
        self.say("A fade blends the two pictures and their sound.",
                 B.animate.shift(LEFT * shift), seam.animate.shift(LEFT * shift / 2).set_opacity(0),
                 Transform(ed.rows[key], ed_fade.rows[key]), *pick(1), FadeIn(fade_curves), FadeIn(legend),
                 FadeIn(length), run_time=1.2)
        self.say("And a dip passes through the background colour, a gentle break between parts.",
                 Transform(ed.rows[key], ed_dip.rows[key]), Transform(fade_curves, dip_curves), *pick(2),
                 run_time=1.2)

        # ---- the overlap, measured
        ox = X0 + (2.5 - 0.5) * U
        bracket = VGroup(Line([ox, LOW - 0.55, 0], [ox + shift, LOW - 0.55, 0], color=ACCENT, stroke_width=3),
                         Line([ox, LOW - 0.45, 0], [ox, LOW - 0.65, 0], color=ACCENT, stroke_width=3),
                         Line([ox + shift, LOW - 0.45, 0], [ox + shift, LOW - 0.65, 0], color=ACCENT, stroke_width=3),
                         T("0.5 s", 20, ACCENT).move_to([ox + shift / 2, LOW - 0.9, 0]))
        length2 = T("the film: 4.5 s", 24, INK).move_to(length.get_left(), aligned_edge=LEFT)
        self.steps("A fade or a dip overlaps the two segments by its seconds, half a second unless you say, so the "
                   "film gets that much shorter.",
                   [Create(bracket), [Transform(length, length2)]], run_time=1.0)
        self.beat(0.4)

        # ---- a title segment
        timeline = Group(A, B, seam, chips, fade_curves, legend, length, bracket)
        card = RoundedRectangle(corner_radius=0.1, width=6.4, height=3.6, fill_color=BG, fill_opacity=1,
                                stroke_color=LINE, stroke_width=2).move_to([-3.2, 0.1, 0])
        t_title = T("An interview", 44, INK, weight=BOLD).move_to(card.get_center() + UP * 0.7)
        t_l1 = T("Prof Joyeeta Gupta", 26, INK)
        t_l2 = T("UNESCO-IHE, 2013", 24, MUTED)
        VGroup(t_l1, t_l2).arrange(DOWN, buff=0.18).move_to(card.get_center() + DOWN * 0.6)
        tp = EditPanel(TITLE_SRC, "edits/join.json", size=19).move_to(PANEL_AT)
        self.steps("Not every segment is footage. A title segment is a card in the project's theme, with up to four "
                   "lines under the title.",
                   [[FadeOut(timeline), FadeOut(ed), FadeIn(card), FadeIn(tp), *tp.light('"title"')],
                    AddTextLetterByLetter(t_title, time_per_char=0.04),
                    [AddTextLetterByLetter(t_l1, time_per_char=0.03), AddTextLetterByLetter(t_l2, time_per_char=0.03),
                     *tp.light('"lines"', 2)]], run_time=1.0)
        self.beat(0.3)

        # ---- an image segment with a move
        pic = picture("build/towers.png", 6.4).move_to([-3.2, 0.1, 0])
        view = Rectangle(width=6.4, height=6.4 * 9 / 16, stroke_color=ACCENT, stroke_width=5).move_to(pic)
        ip = EditPanel(IMAGE_SRC, "edits/join.json", size=19).move_to(PANEL_AT)
        self.steps("An image segment is a still, and move makes it push in, pull out, or pan, so a still never sits "
                   "dead.",
                   [[FadeOut(VGroup(card, t_title, t_l1, t_l2)), FadeOut(tp), FadeIn(pic), FadeIn(ip),
                     *ip.light('"move"'), Create(view)],
                    view.animate.scale(0.8), view.animate.scale(1 / 0.8),
                    view.animate.scale(0.8).shift(RIGHT * 0.6)], run_time=1.0)
        self.beat(0.3)

        # ---- an episode segment
        a2 = block(0, 1.8, 0.2, BLUE, "interview", h=1.0)
        e2 = block(1.8, 3.8, 0.2, ACCENT, "ep01", h=1.0)
        e2[0].set_fill(opacity=0.2)
        d2 = block(3.8, 5.4, 0.2, VIOLET, "demolition", h=1.0)
        e2.shift(UP * 1.4)
        ep = EditPanel(EPISODE_SRC, "edits/join.json", size=19).move_to(PANEL_AT)
        lbl = T("an explainer, rendered by manimvox", 20, MUTED).move_to([X0 + 2.8 * U, -1.1, 0])
        self.steps("And an episode segment drops in an explainer you rendered with manimvox, like the ones teaching "
                   "you now.",
                   [[FadeOut(Group(pic, view)), FadeOut(ip), FadeIn(a2), FadeIn(d2), FadeIn(ep),
                     *ep.light('"episode"')],
                    [e2.animate.shift(DOWN * 1.4), FadeIn(lbl)]], run_time=1.0)
        self.beat(0.3)

        # ---- from_video inside an explainer
        frame = RoundedRectangle(corner_radius=0.12, width=6.8, height=4.5, fill_color=PANEL, fill_opacity=1,
                                 stroke_color=LINE, stroke_width=2).move_to([-3.2, 0.0, 0])
        demo = footage(DEMOLITION, 12.0, 20.0, 5.0).move_to(frame.get_center() + UP * 0.45)
        demo.clip.loop()
        snd = wave(loudness(DEMOLITION, 12.0, 20.0, 60), 5.0, 0.5, MUTED, 3).move_to(frame.get_center() + DOWN * 1.8)
        head = Line(snd.get_left() + UP * 0.3, snd.get_left() + DOWN * 0.3, color=ACCENT, stroke_width=4)
        cp = EditPanel(CODE_SRC, "ep01_bench.py", size=19).move_to(PANEL_AT)
        self.steps("Inside an explainer, from video plays a recording with its own sound, levelled to the "
                   "narration.",
                   [[FadeOut(VGroup(a2, d2, e2, lbl)), FadeOut(ep), FadeIn(frame), FadeIn(demo), FadeIn(snd),
                     FadeIn(cp), *cp.light("sound=True")],
                    head.animate(rate_func=linear).shift(RIGHT * 5.0)], run_time=1.0)
        self.beat(0.3)

        # ---- the result, played full frame (narrated inside it)
        self.show_result("r04", lead=demo)

        # ---- the mistake
        demo.clip.clear_updaters()
        first = block(0, 2.5, 0.4, BLUE, "interview")
        first.shift(RIGHT * 2.0 * U)
        empty = DashedVMobject(Rectangle(width=2.0 * U, height=0.8, stroke_color=MUTED, stroke_width=2))
        empty.move_to([X0 + 1.0 * U, 0.4, 0])
        nothing = T("nothing before it", 20, MUTED).next_to(empty, DOWN, buff=0.25)
        mistake = Mistake('"transition": "fade"', '"transition": "cut"', SAID["first_fade"][0], w=6.0,
                          size=22).move_to(PANEL_AT)
        self.say("The mistake is a fade on the very first segment.",
                 FadeOut(Group(frame, demo, snd, head)), FadeOut(cp), FadeIn(first), FadeIn(empty),
                 *mistake.wrong_in(), run_time=1.0)
        self.say("There's nothing before it to fade from, so it must be a cut.", FadeIn(nothing), *mistake.struck(),
                 *mistake.fixed(), run_time=1.6)
        self.beat(1.0)

        # ---- takeaway, bridge
        kinds = VGroup(*[self._chip(t) for t in ("a clip", "a title card", "a still", "an explainer")])
        kinds.arrange(RIGHT, buff=0.3).move_to(DOWN * 0.2)
        joins = T("cut  ·  fade  ·  dip", 34, INK).move_to(UP * 1.3)
        self.say("So segments join with a cut, a fade or a dip, and can be clips, cards, stills or explainers.",
                 FadeOut(VGroup(first, empty, nothing)), FadeOut(mistake), FadeIn(joins), FadeIn(kinds),
                 run_time=1.2)
        small = footage(DEMOLITION, 12.0, 28.0, 3.4).move_to(UP * 0.0)
        small.clip.loop()
        self.say("But the demolition is too small, and too fast.", FadeOut(joins), FadeOut(kinds), FadeOut(title),
                 FadeIn(small), run_time=0.9)
        self.beat(0.8)

        # ---- the next chapter
        small.clip.clear_updaters()
        nxt = next_tag("Frame and speed")
        self.say("Next, frame and speed.", blur_in(nxt), run_time=0.9)
        self.play(*[FadeOut(m) for m in self.stage()], run_time=0.8)
        self.beat(0.4)

    @staticmethod
    def _chip(text):
        b_ = RoundedRectangle(corner_radius=0.1, width=2.5, height=0.8, fill_color=PANEL, fill_opacity=1,
                              stroke_color=LINE, stroke_width=1.5)
        return VGroup(b_, T(text, 24, INK).move_to(b_))
