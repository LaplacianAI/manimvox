"""Chapter 12, two cameras: two angles of one moment and their sound drawn from the real recordings, edit sync
lines them up, the honest note (these two files share one soundtrack, so they line up at zero), a multicam segment's
cuts, the sound that stays on camera 0, and the mistake of guessing an offset. Script: episodes/tour.md. Terminal
lines and errors are real (build/said.json)."""
import itertools

from bench import *

SHOWN = """\
{
  "multicam": [
    "street-wide.webm",
    "street-close.webm"
  ],
  "start": 8,
  "end": 24,
  "cuts": [[12, 1], [17, 0], [20.5, 1]],
  "sound": 0
}"""

CUTS = [[12, 1], [17, 0], [20.5, 1]]


def next_tag(name):
    """The small "next" tag at the bottom right that introduces the following chapter."""
    tag = VGroup(T("next", 22, MUTED), T(name, 30, INK, weight=BOLD)).arrange(DOWN, aligned_edge=RIGHT, buff=0.1)
    return tag.move_to([6.2 - tag.width / 2, -3.0, 0])

def play_result(ep, name, lead):
    """Bench.show_result, with the lead clip put back by hand: its restore() calls become() on a video, which
    Manim cannot do."""
    a, b = WINDOWS[name]
    clip = from_video(HERE / RESULTS, fps=30, start=a, end=b, width=FW, sound=True).move_to(ORIGIN)
    ground = getattr(ep, "_ground", None)
    others = [m for m in ep.stage() if m is not lead and m is not ground]
    w0, c0 = lead.width, lead.get_center()
    ep.play(full(lead), *[FadeOut(m) for m in others], run_time=0.8)
    ep.play(FadeIn(clip), run_time=0.25)
    ep.remove(lead)
    ep.play(clip.play())
    lead.scale(w0 / lead.width).move_to(c0)
    ep.play(FadeOut(clip), *[FadeIn(m) for m in others], FadeIn(lead), run_time=0.7)



class Ep12(Bench):
    EP = 12
    TITLE = "Two cameras"

    def build(self):
        _title, enter = self.heading("Two cameras", "blur")
        w = 5.6
        wide = footage(CAMERAS[0], 8, 24, w)
        close = footage(CAMERAS[1], 8, 24, w)
        pair = Group(wide, close).arrange(RIGHT, buff=0.3).move_to(UP * 0.75)
        for m in (wide, close):
            m.clip.loop()
        tags = VGroup(caption("wide", wide, 24, BLUE), caption("close", close, 24, ORANGE))

        # the real sound of each angle, 8 to 24 s, drawn as it is
        ww = 11.5
        wa = wave(loudness(CAMERAS[0], 8, 24), ww, 0.6, BLUE, 3).move_to([0, -1.95, 0])
        wb = wave(loudness(CAMERAS[1], 8, 24), ww, 0.6, ORANGE, 3).move_to([0, -2.65, 0])
        wb.shift(RIGHT * 0.8)
        aside = T("drawn apart, as if the cameras had started at different times", 18, MUTED).move_to([0, -3.15, 0])

        self.say("Every recording so far came from one camera. The street came from two.", enter, FadeIn(pair),
                 FadeIn(tags), run_time=1.2)
        self.say("Two cameras film the same moment, but they started at different times.", run_time=0.5)
        self.say("To cut between them, they have to be lined up.", FadeIn(wa), FadeIn(wb), FadeIn(aside),
                 run_time=1.4)
        self.beat(0.3)

        term = Terminal("manimvox edit sync street-wide.webm street-close.webm", SAID["sync"], w=ww, size=17)
        term.move_to([0, 1.45, 0])
        mark = Line([-ww / 2 - 0.1, -1.4, 0], [-ww / 2 - 0.1, -3.0, 0], color=ACCENT, stroke_width=3)
        ring = SurroundingRectangle(term.out[1], color=ACCENT, buff=0.06, stroke_width=2)
        for m in (wide, close):
            m.clip.clear_updaters()
        self.say("Edit sync lines them up by their sound, and says where each starts on the first one's clock, and "
                 "how sure it is.", FadeOut(pair), FadeOut(tags), FadeOut(aside), *term.run(),
                 wb.animate.shift(LEFT * 0.8), run_time=2.4)
        self.play(Create(ring), FadeIn(mark), run_time=0.6)

        note = VGroup(Rectangle(width=0.08, height=1.0, stroke_width=0, fill_color=ACCENT, fill_opacity=1),
                      P("An honest note: these two files share one soundtrack, so they line up at exactly zero. "
                        "On separate recordings, sync finds the real offset to within a hundredth of a second.",
                        22, INK, max_w=10.8)).arrange(RIGHT, buff=0.25)
        note.move_to([0, -0.4, 0])
        self.say("These two files carry the same soundtrack, so they line up at exactly zero. On separate "
                 "recordings, sync finds the real offset to within a hundredth of a second.", FadeIn(note),
                 run_time=1.0)
        self.beat(1.0)

        # a multicam segment
        clip = footage(CAMERAS[0], 8, 24, CLIP_W).move_to(CLIP_AT + UP * 0.65)
        clip.clip.loop()
        edit = EditPanel(SHOWN, "edits/street.json", w=PANEL_W).move_to(PANEL_AT + UP * 0.3)
        edit.hide()
        # the picture's strip and camera 0's sound under the clip
        sx0, sw = CLIP_AT[0] - CLIP_W / 2, CLIP_W
        edges = [8, 12, 17, 20.5, 24]
        cams = [0, 1, 0, 1]
        strip = VGroup()
        for (a, b), cam in zip(itertools.pairwise(edges), cams, strict=True):
            col = BLUE if cam == 0 else ORANGE
            r = Rectangle(width=(b - a) / 16 * sw, height=0.34, fill_color=col, fill_opacity=0.35, stroke_color=col,
                          stroke_width=1.5)
            r.move_to([sx0 + ((a + b) / 2 - 8) / 16 * sw, -1.95, 0])
            strip.add(VGroup(r, T("wide" if cam == 0 else "close", 16, INK).move_to(r)))
        sound = wave(loudness(CAMERAS[0], 8, 24), sw, 0.6, BLUE, 2).move_to([CLIP_AT[0], -2.6, 0])
        stag = T("camera 0's sound", 16, BLUE).move_to([CLIP_AT[0], -3.1, 0])
        self.say("A multicam segment then cuts between them.",
                 FadeOut(term), FadeOut(ring), FadeOut(note), FadeOut(wa), FadeOut(wb), FadeOut(mark),
                 FadeIn(clip), FadeIn(edit.bg), FadeIn(edit.head), run_time=1.0)
        self.play(*edit.light(0, 1, 2, 3, 4, 5), run_time=0.6)
        self.steps("Cuts are times on the first camera's clock, each with the camera to show.",
                   [edit.light("\"cuts\""), LaggedStart(*[FadeIn(s) for s in strip], lag_ratio=0.3, run_time=1.6)],
                   run_time=1.2)
        self.beat(0.3)
        self.steps("The sound stays on one camera throughout, so it never jumps when the picture does.",
                   [edit.light("\"sound\""), [FadeIn(sound), FadeIn(stag)]], run_time=1.2)
        self.beat(1.0)

        play_result(self, "r12", lead=clip)

        # the mistake
        mistake = Mistake('"offsets": [0, 1.37]', 'no "offsets" at all', SAID["offsets"][0], w=6.0, size=22)
        mistake.move_to([3.55, 0.0, 0])
        self.say("The mistake is guessing an offset.", FadeOut(edit), FadeOut(strip), FadeOut(sound), FadeOut(stag),
                 *mistake.wrong_in(), clip.animate.scale(5.4 / CLIP_W).move_to([-3.4, 0.2, 0]), run_time=1.2)
        self.say("Leave offsets out, and check edit finds them from the sound.", *mistake.struck(),
                 run_time=1.0)
        self.say("If it isn't sure, it says so instead of guessing.", *mistake.fixed(), run_time=1.2)
        self.beat(1.0)

        self.say("So sync lines cameras up, and multicam cuts between them.", FadeOut(mistake), run_time=0.6)
        tag = next_tag("Render and share")
        self.say("Next, rendering and sharing the film.", blur_in(tag), run_time=1.0)
        self.beat(0.5)
        clip.clip.clear_updaters()
        self.play(*[FadeOut(m) for m in self.stage()], run_time=0.8)
        self.beat(0.4)
