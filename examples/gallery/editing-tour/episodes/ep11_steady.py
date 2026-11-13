"""Chapter 11, steady: how stabilize measures the camera's path, smooths it and moves each frame by the difference,
the render's note, before and after, and the mistake of smoothing over too long a time. The path drawn is the real
cached measurement of the demolition (build/edit/stab/). Script: episodes/tour.md. The notes are real
(build/results.log)."""
import json

import numpy as np
from bench import *

STAB = [json.loads(p.read_text()) for p in sorted((HERE / "build" / "edit" / "stab").glob("*.json"))]
PATH = next(d for d in STAB if abs(d["times"][0] - 12.0) < 0.1 and abs(d["times"][-1] - 28.0) < 0.1)

SHOWN = """\
{
  "clip": "demolition.webm",
  "start": 12,
  "end": 28,
  "stabilize": {"smooth": 2}
}"""

NOTE = "segments[0]: stabilised, correcting up to 0.8% of the width, zoomed 1.03x"
NOTE_BAD = "segments[0]: stabilised, correcting up to 3.6% of the width, zoomed 1.12x"


def smooth(v, times, seconds):
    """The path averaged with a Gaussian `seconds` wide, as stabilize does (ends held)."""
    step = float(np.median(np.diff(times)))
    sigma = max(1e-6, seconds / 4 / step)
    r = int(np.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    return np.convolve(np.pad(v, r, mode="edge"), k / k.sum(), mode="valid")


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



class Ep11(Bench):
    EP = 11
    TITLE = "Steady"

    def build(self):
        times = np.array(PATH["times"])
        x = np.array(PATH["x"]) * 100  # percent of the frame's width
        np.array(PATH["y"]) * 100
        a = np.array(PATH["a"])
        sx, sy, sa = (smooth(v, times, 2) for v in (np.array(PATH["x"]), np.array(PATH["y"]), a))

        _title, enter = self.heading("Steady", "letters")
        clip = footage(DEMOLITION, 12, 28, CLIP_W).move_to(CLIP_AT)
        clip.clip.loop()

        # the camera's path: sideways, as measured on this very clip
        box = RoundedRectangle(corner_radius=0.14, width=PANEL_W, height=3.6, fill_color=PANEL, fill_opacity=1,
                               stroke_color=LINE, stroke_width=1.5).move_to(PANEL_AT + UP * 0.1)
        heading = T("the camera's path, sideways", 19, MUTED).move_to(box.get_top() + DOWN * 0.38)
        pw, ph = 4.6, 2.0
        lo, hi = x.min(), x.max()

        def pt(t, v):
            return box.get_center() + np.array([(t - 12) / 16 * pw - pw / 2, (v - lo) / (hi - lo) * ph - ph / 2 - 0.1, 0])

        def line(values, color, width):
            m = VMobject(stroke_color=color, stroke_width=width)
            m.set_points_as_corners([pt(t, v) for t, v in zip(times[::2], values[::2])])
            return m
        raw = line(x, INK, 2.5)
        axis = Line(pt(12, lo) + DOWN * 0.1, pt(28, lo) + DOWN * 0.1, color=LINE, stroke_width=2)
        foot = T("12 to 28 s of the file, measured from this clip", 16, MUTED).move_to(box.get_bottom() + UP * 0.3)

        self.say("We've fixed the demolition's colour and its speed. What's left is the shake.", enter,
                 FadeIn(clip), FadeIn(box), FadeIn(heading), FadeIn(axis), FadeIn(foot), run_time=1.2)
        self.steps("Stabilize holds shaky footage steady. First it measures how each frame moved and turned "
                   "against the one before.", [[Create(raw, run_time=2.2)]], run_time=2.2)
        steady = line(sx * 100, ACCENT, 5)
        tag = T("smoothed over 2 seconds", 18, ACCENT).move_to(box.get_top() + DOWN * 0.38)
        self.steps("Then it smooths that path over a number of seconds. Slow moves, like a pan, stay. The shake "
                   "is taken out.",
                   [[Create(steady, run_time=2.0), FadeOut(heading), FadeIn(tag)],
                    [raw.animate.set_stroke(opacity=0.4)]], run_time=1.0)
        self.beat(0.3)

        # the frame moved by the difference, and zoomed so its edges stay out
        t = ValueTracker(12.0)
        AMP, Z, FW_, FH_ = 6.0, 1.1, 3.4, 3.4 * 0.5625

        def moved():
            v = t.get_value()
            dx = (np.interp(v, times, sx) - np.interp(v, times, np.array(PATH["x"]))) * AMP
            dy = (np.interp(v, times, sy) - np.interp(v, times, np.array(PATH["y"]))) * AMP
            da = (np.interp(v, times, sa) - np.interp(v, times, a)) * AMP
            r = Rectangle(width=FW_ * Z, height=FH_ * Z, stroke_color=INK, stroke_width=2.5, fill_color=PANEL2,
                          fill_opacity=0.8)
            r.rotate(da).move_to(c + np.array([dx * FW_, dy * FW_, 0]))
            return r
        c = PANEL_AT + UP * 0.35
        window = Rectangle(width=FW_, height=FH_, stroke_color=ACCENT, stroke_width=4).move_to(c)
        pic = always_redraw(moved)
        note = T("the correction, drawn 6 times larger", 17, MUTED).move_to(box.get_bottom() + UP * 0.3)
        wnote = T("what you see", 17, ACCENT).next_to(window, UP, buff=0.25)
        self.steps("It moves each frame by the difference, and zooms in just enough that the moving edges stay "
                   "out of view.",
                   [[FadeOut(raw), FadeOut(steady), FadeOut(tag), FadeOut(foot), FadeOut(axis), FadeIn(pic),
                     Create(window), FadeIn(note)],
                    [FadeIn(wnote), t.animate.set_value(20.0).set_rate_func(linear)]], run_time=2.2)
        self.beat(0.3)

        term = Terminal("manimvox edit render steady", ["stabilise: measuring the shake in demolition.webm (16.0 s) ...",
                                                        NOTE], w=PANEL_W + 0.9, size=16)
        term.move_to(PANEL_AT + UP * 0.6)
        ring = SurroundingRectangle(term.out[2:] if len(term.out) > 3 else term.out[-1], color=ACCENT, buff=0.08,
                                    stroke_width=2)
        saved = T("measured once, saved in build/edit/stab/", 19, MUTED).next_to(term, DOWN, buff=0.4)
        pic.clear_updaters()
        self.say("The render tells you how much it corrected, and how far it zoomed.",
                 FadeOut(pic), FadeOut(window), FadeOut(note), FadeOut(wnote), FadeOut(box), *term.run(),
                 run_time=1.6)
        self.say("The measurement is saved, so the next render is quick.", Create(ring), FadeIn(saved), run_time=0.8)
        self.beat(0.5)

        play_result(self, "r11", lead=clip)

        # before, and after
        clip.clip.clear_updaters()
        raw_clip = footage(DEMOLITION, 12, 28)
        done = result("steady")
        pair, tags = before_after(raw_clip, done)
        for m in (raw_clip, done):
            m.clip.loop()
        self.say("Before, and after.", FadeOut(clip), FadeOut(term), FadeOut(ring), FadeOut(saved), FadeIn(pair),
                 FadeIn(tags), run_time=1.0)
        self.beat(2.0)

        # the mistake
        raw_clip.clip.clear_updaters()
        done.clip.clear_updaters()
        bad = result("steady_bad", w=5.4).move_to([-3.4, 0.0, 0])
        bad.clip.loop()
        bad_tag = caption("smooth 10", bad, 22, MUTED)
        mistake = Mistake('"stabilize": {"smooth": 10}', '"stabilize": {"smooth": 2}', NOTE_BAD, w=6.0, size=22)
        mistake.move_to([3.55, 0.0, 0])
        good = P("stabilised, correcting up to 0.8% of the width, zoomed 1.03x", 19, OK, max_w=6.0, font=MONO)
        good.next_to(mistake, DOWN, buff=0.3).align_to(mistake, LEFT)
        mistake.shift(UP * 0.35)
        good.next_to(mistake, DOWN, buff=0.3).align_to(mistake, LEFT)
        self.say("The mistake is smoothing over too long a time.", FadeOut(pair), FadeOut(tags), FadeIn(bad),
                 FadeIn(bad_tag), *mistake.wrong_in(), run_time=1.4)
        self.say("Slow moves flatten, and it needs more zoom: ten seconds here zooms in 1.12 times, against 1.03 "
                 "for two.", *mistake.struck(), run_time=1.2)
        self.say("If the edges would show, the note says so: lower smooth.", *mistake.fixed(), FadeIn(good),
                 run_time=1.6)
        self.beat(1.0)

        nxt = footage(DEMOLITION, 12, 28, CLIP_W).move_to(CLIP_AT)
        nxt.clip.loop()
        self.say("So stabilize keeps the camera's moves and takes out its shake.", FadeOut(mistake), FadeOut(good),
                 FadeOut(bad), FadeOut(bad_tag), FadeIn(nxt), run_time=1.0)
        tag = next_tag("Two cameras")
        self.say("Next, two cameras.", blur_in(tag), run_time=1.0)
        self.beat(0.5)
        nxt.clip.clear_updaters()
        self.play(*[FadeOut(m) for m in self.stage()], run_time=0.8)
        self.beat(0.4)
