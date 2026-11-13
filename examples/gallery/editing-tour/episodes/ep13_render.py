"""Chapter 13, render and share: a draft at 480 lines, --from and --to for one stretch, the final render and its
captions, --copy on the explainer alone and on this film, export to an OpenTimelineIO file, and the mistake of
expecting copy on a graded clip. Script: episodes/tour.md. Output lines come from build/said.json where capture.py
kept them (copy, copy_tour, copy_graded, export); the others are written in the same shape render prints."""
from bench import *


def said(key, default):
    """What manimvox printed for `key`, as a list of lines without progress counters; `default` if not captured."""
    v = SAID.get(key, default)
    v = [v] if isinstance(v, str) else list(v)
    v = [line for line in v if line.strip() and not line.startswith("  ")]
    return v or default


COPY_JSON = """\
{
  "segments": [
    {"episode": "ep01"}
  ],
  "audio": [
    {"music": "build/pad.wav",
     "volume": -26}
  ]
}"""

DRAFT = ["render: draft at 854x480, 30 fps ...", "video: build/edit/tour/draft.mp4  (854x480)"]
WINDOW = ["render: 21.0 s at 854x480, 30 fps (draft) ...", "video: build/edit/tour/draft.mp4  (21 s, 854x480)"]
FINAL = ["render: 1920x1080, 30 fps ...", "video: out/tour.mp4", "captions: out/tour.srt"]
COPY = ["render: copying the picture of ep01_bench.mp4, mixing the sound ...",
        "copy: the picture is ep01_bench.mp4's own, not re-encoded", "video: out/copy.mp4"]
COPY_TOUR = ["copy: not copied, because the film is more than one clip; encoded instead"]
COPY_GRADED = ["copy: not copied, because the picture is changed (a grade); encoded instead"]
EXPORT = ["otio: drawing segments[6] ...", "otio: drawing overlays[0] ...", "otio: out/results.otio"]

LEFT_AT = np.array([-3.15, 0.6, 0])
RIGHT_AT = np.array([3.55, 0.3, 0])
TW = 6.6


def pill(text, w=2.2, color=LINE, size=19, fill=PANEL):
    r = RoundedRectangle(corner_radius=0.1, width=w, height=0.5, fill_color=fill, fill_opacity=1, stroke_color=color,
                         stroke_width=1.5)
    return VGroup(r, T(text, size, INK, font=MONO if "/" in text or "." in text else FONT).move_to(r))


def next_tag(name):
    """The small "next" tag at the bottom right that introduces the following chapter."""
    tag = VGroup(T("next", 22, MUTED), T(name, 30, INK, weight=BOLD)).arrange(DOWN, aligned_edge=RIGHT, buff=0.1)
    return tag.move_to([6.2 - tag.width / 2, -3.0, 0])


class Ep13(Bench):
    EP = 13
    TITLE = "Render and share"

    def build(self):
        _title, enter = self.heading("Render and share", "write")

        # ---- a draft
        t1 = Terminal("manimvox edit render tour --draft", DRAFT, w=TW, size=17).move_to(LEFT_AT)
        film = result("cameras", w=4.8).move_to(RIGHT_AT)
        film.clip.loop()
        size = T("854 x 480", 24, INK)
        size.next_to(film, DOWN, buff=0.25)
        self.say("Every fix is now in the edit file. Last, getting the film out of it.", enter, run_time=1.2)
        self.say("To see your edit, render a draft first. It's small and quick, at four hundred and eighty lines.",
                 *t1.run(), FadeIn(film), FadeIn(size), run_time=2.0)
        self.beat(1.0)

        # ---- from and to: one stretch
        film.clip.clear_updaters()
        t2 = Terminal("manimvox edit render tour --from 42 --to 63", WINDOW, w=TW, size=17).move_to(LEFT_AT)
        bar_w = 5.4
        bar = Rectangle(width=bar_w, height=0.36, fill_color=PANEL, fill_opacity=1, stroke_color=LINE,
                        stroke_width=1.5)
        win = Rectangle(width=bar_w * 0.14, height=0.36, fill_color=ACCENT, fill_opacity=0.5, stroke_color=ACCENT,
                        stroke_width=2)
        bar_g = VGroup(bar, win)
        win.move_to(bar.get_left() + RIGHT * bar_w * 0.42, aligned_edge=LEFT)
        bar_g.move_to(RIGHT_AT + UP * 1.3)
        blabel = T("the film", 18, MUTED).next_to(bar, UP, buff=0.15).align_to(bar, LEFT)
        wlabel = T("42 s to 63 s", 18, ACCENT).next_to(win, DOWN, buff=0.15)
        fall = footage(DEMOLITION, 29, 40, 4.4).move_to(RIGHT_AT + DOWN * 0.95)
        fall.clip.loop()
        self.say("From and to render one stretch of the film, so you can check a fix in seconds.",
                 FadeOut(t1), FadeOut(film), FadeOut(size), *t2.run(), FadeIn(bar_g), FadeIn(blabel), FadeIn(wlabel),
                 FadeIn(fall), run_time=2.0)
        self.beat(1.0)

        # ---- the final render
        fall.clip.clear_updaters()
        t3 = Terminal("manimvox edit render tour", FINAL, w=TW, size=17).move_to(LEFT_AT)
        mp4 = pill("out/tour.mp4", 2.6, ACCENT)
        srt = pill("out/tour.srt", 2.6, ACCENT)
        files = VGroup(mp4, srt).arrange(DOWN, buff=0.35).move_to(RIGHT_AT)
        self.say("The final render writes the film and its captions.",
                 FadeOut(t2), FadeOut(bar_g), FadeOut(blabel), FadeOut(wlabel), FadeOut(fall), *t3.run(),
                 FadeIn(mp4), FadeIn(srt), run_time=2.0)
        self.beat(1.0)

        # ---- copy, on the explainer alone
        t4 = Terminal("manimvox edit render copy --copy", said("copy", COPY), w=TW, size=17).move_to(LEFT_AT)
        panel = EditPanel(COPY_JSON, "edits/copy.json", size=20, w=5.2).move_to(RIGHT_AT)
        hit = [r for r in t4.out if "copy:" in getattr(r, "text", "")] or [t4.out[-1]]
        note4 = SurroundingRectangle(VGroup(*hit), color=ACCENT, buff=0.07, stroke_width=2)
        secs = T("5 seconds", 26, INK).next_to(panel, DOWN, buff=0.3)
        self.say("When the whole edit is one untouched clip with new sound, copy uses the clip's picture as it is: "
                 "no loss, and done in seconds.", FadeOut(t3), FadeOut(files), *t4.run(), FadeIn(panel),
                 run_time=2.4)
        self.play(Create(note4), FadeIn(secs), run_time=0.6)
        self.beat(1.0)

        # ---- copy, on this film
        t5 = Terminal("manimvox edit render results --copy", said("copy_tour", COPY_TOUR), w=TW, size=17).move_to(LEFT_AT)
        names = ["title", "interview", "bench", "towers", "street"]
        blocks = VGroup(*[pill(n, 1.45, BLUE, 17, fill=PANEL2) for n in names])
        blocks.arrange_in_grid(2, 3, buff=0.2).move_to(RIGHT_AT)
        many = T("more than one clip", 24, INK).next_to(blocks, DOWN, buff=0.35)
        self.say("On any other edit it encodes as usual, and the note says why.",
                 FadeOut(t4), FadeOut(note4), FadeOut(panel), FadeOut(secs), *t5.run(),
                 LaggedStart(*[FadeIn(b) for b in blocks], lag_ratio=0.15), FadeIn(many), run_time=2.0)
        self.beat(1.0)

        # ---- export
        t6 = Terminal("manimvox edit export results", said("export", EXPORT)[-3:], w=TW, size=17).move_to(LEFT_AT)
        rows = ["main track", "overlay 1", "overlay 2", "overlay 3", "overlay 4", "footage", "narration", "music",
                "sounds"]
        kinds = [BLUE] + [VIOLET] * 4 + [ORANGE] + [ACCENT, MUTED, MUTED]
        spans = [[(0, 9)], [(1, 2)], [(3, 4)], [(5, 7)], [(2, 3), (6, 8)], [(0, 9)], [(1, 3), (4, 6), (7, 8.6)],
                 [(0, 9)], [(2, 2.5), (5, 5.5), (8, 8.5)]]
        tw, th = 3.6, 0.3
        x0 = RIGHT_AT[0] - 0.1
        grid = VGroup()
        top = RIGHT_AT[1] + 1.75
        for k, (name, col, sp) in enumerate(zip(rows, kinds, spans, strict=True)):
            y = top - k * 0.43
            lab = T(name, 16, MUTED).move_to([x0 - tw / 2 - 0.15 - 0.62, y, 0])
            lab.align_to([x0 - tw / 2 - 1.6, y, 0], LEFT)
            lane = Rectangle(width=tw, height=th, stroke_color=LINE, stroke_width=1, fill_color=PANEL, fill_opacity=1)
            lane.move_to([x0 + 0.55, y, 0])
            grid.add(lab, lane)
            for a, b in sp:
                blk = Rectangle(width=(b - a) / 9 * tw, height=th - 0.08, stroke_width=0, fill_color=col,
                                fill_opacity=0.55)
                blk.move_to([lane.get_left()[0] + (a + b) / 18 * tw, y, 0])
                grid.add(blk)
        grid.move_to(RIGHT_AT + RIGHT * 0.1)
        otio = T("out/results.otio", 22, ACCENT, font=MONO).next_to(grid, DOWN, buff=0.3)
        self.say("And export writes the edit as an Open Timeline file, which Kdenlive or DaVinci Resolve can open, "
                 "to adjust by hand.", FadeOut(t5), FadeOut(blocks), FadeOut(many), *t6.run(),
                 LaggedStart(*[FadeIn(g) for g in grid], lag_ratio=0.02), FadeIn(otio), run_time=2.6)
        self.beat(1.0)

        # ---- the mistake
        mistake = Mistake("manimvox edit render graded --copy", "manimvox edit render graded",
                          said("copy_graded", COPY_GRADED)[0], w=9.5, size=24)
        mistake.move_to(DOWN * 0.1)
        self.say("The mistake is expecting copy on a changed clip.", FadeOut(t6), FadeOut(grid), FadeOut(otio),
                 *mistake.wrong_in(), run_time=1.4)
        self.say("A grade, a crop or any change to the picture means it has to be encoded.", *mistake.struck(),
                 *mistake.fixed(), run_time=2.0)
        self.beat(1.0)

        self.say("So drafts and windows let you check fast, and copy and export carry the film further.",
                 FadeOut(mistake), run_time=1.0)
        tag = next_tag("Back to the four recordings")
        self.say("Next, back to where we started.", blur_in(tag), run_time=1.0)
        self.beat(0.5)
        self.play(*[FadeOut(m) for m in self.stage()], run_time=0.8)
        self.beat(0.4)
        self.beat(0.6)
