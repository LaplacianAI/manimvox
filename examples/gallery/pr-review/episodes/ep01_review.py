from manimvox.kit import *

# The real check run on this video's own narration (filled in after the final render, then verified).
FINAL_PACE = 171
PAD = 0.35


def term(lines, title="terminal", size=22, w=12.4, colors=None, **kw):
    return code("\n".join(lines), size=size, title=title, w=w, colors=colors or {}, dots=False, line_spacing=0.9, **kw)


class Ep01(Episode):
    EP = 1
    TITLE = "A pull request, reviewed and fixed"
    TAGLINE = "manimvox#63 closes issue #21: the audio check reports narration pace"
    NCHAP = 4
    CHROME = ()

    def line(self, text, *anims, **kw):
        self.say(text, *anims, pad=PAD, **kw)

    def hand(self, red=True):
        return code(
            "words in the .srt cues\n"
            "──────────────────────  × 60\n"
            "seconds of all the cues\n"
            "\n"
            "= 215 words a minute",
            size=26, title="by hand (issue #21, Sarvam)", dots=False, line_spacing=1.0,
            colors={"215 words a minute": ERROR} if red else {})

    def build(self):
        # ---- cold open: the by-hand sum
        hand = self.hand(red=False).scale(1.2).move_to([0, -0.7, 0])
        self.add(hand)
        self.line("To check how fast a narration is, you count the words in the subtitle file, add up how long "
                  "every cue lasts, and divide.", Wait(0.1))
        hand_red = self.hand(red=True).scale(1.2).move_to(hand)
        nowarn = chip("nothing warned", MUTED, 20).next_to(hand, DOWN, buff=0.2)
        self.line("With Sarvam, that came to two hundred fifteen words a minute. Nothing warned anyone.",
                  FadeOut(hand), FadeIn(hand_red), FadeIn(nowarn))
        self.intro("Pull request sixty-three makes the audio check do that sum. Here is the change, what the "
                   "review found, and the fix.", question="Can the check do the sum for you?", card=False)

        # ---- 1 The change
        self.chapter("The change", number=False, card=False)
        t1 = term(["$ manimvox check audio ep01", "pace: 168 words a minute", "audio check: ok  (4 lines, all audible)"],
                  title="issue #21: done when", size=32, colors={"pace: 168 words a minute": ACCENT}).move_to([0, 0.6, 0])
        self.line("Issue twenty-one asked the check to print the pace itself, from the subtitle file.",
                  FadeIn(t1))
        t2 = term(["pace: 215 words a minute",
                   "warning: faster than 175 words a minute; lower speed in series.json to 0.77",
                   "audio check: ok  (4 lines, all audible)"],
                  title="PR #63, first version (the issue's Sarvam case)", size=19,
                  colors={"warning: faster than 175 words a minute; lower speed in series.json to 0.77": WARN,
                          "pace: 215 words a minute": ACCENT, "audio check: ok  (4 lines, all audible)": OK}
                  ).move_to([0, 0.9, 0])
        f = T("speed × 165 ÷ pace  =  1.0 × 165 ÷ 215  =  0.77", 34, INK).move_to([0, -0.9, 0])
        ok = chip("the check still passes", OK, 24).move_to([0, -2.1, 0])
        self.steps("Above one seventy-five it warns, and suggests a speed: the current speed, times one sixty-five, "
                   "over the pace. The check still passes.",
                   [[FadeOut(t1), FadeIn(t2)], [FadeIn(f)], [FadeIn(ok)]], pad=PAD)

        # ---- 2 The review
        self.chapter("The review", transition="dip", number=False, card=False, bridge="But the review found a trap.")
        X0, X1, S0, S1 = -5.4, 5.4, 0.70, 1.20
        px = lambda s: X0 + (s - S0) / (S1 - S0) * (X1 - X0)
        axis = Line([X0, 1.3, 0], [X1, 1.3, 0]).set_stroke(LINE, 4)
        band = Line([px(0.85), 1.3, 0], [px(1.15), 1.3, 0]).set_stroke(OK, 14)
        lab_band = T("gnani:Kaveri accepts 0.85 to 1.15", 22, OK).next_to(band, UP, buff=0.35)
        ticks = VGroup(*[T(f"{s:.2f}", 18, MUTED).move_to([px(s), 0.8, 0]) for s in (0.85, 1.15)])
        mark = Dot([px(0.82), 1.3, 0], radius=0.17, color=ERROR)
        lab_mark = T("suggested 0.82", 22, ERROR).next_to(mark, DOWN, buff=0.7).shift(LEFT * 0.4)
        lead = Line(lab_mark.get_top(), mark.get_bottom()).set_stroke(ERROR, 2)
        sub = T("200 words a minute, speed 1.0", 20, MUTED).move_to([0, 2.45, 0])
        self.steps("Gnani only accepts speeds from point eight five to one point one five. At two hundred words a "
                   "minute, the check suggested point eight two.",
                   [[Create(axis), FadeIn(sub)], [Create(band), FadeIn(lab_band), FadeIn(ticks)],
                    [FadeIn(mark), FadeIn(lab_mark), Create(lead)]], pad=PAD)
        err = term(["Gnani speaks at speed 0.85–1.15; series.json has 0.82"], title="the next render", size=26,
                   colors={"Gnani speaks at speed 0.85–1.15; series.json has 0.82": ERROR}).move_to([0, -1.6, 0])
        self.line("Follow that advice, and the next render fails.", FadeIn(err))
        rows = VGroup()
        items = [("medium", ERROR, "suggested speed outside the voice's range"),
                 ("low", WARN, "render shows no pace"),
                 ("low", WARN, "docs said “0.9 first”"),
                 ("nit", MUTED, "165 was a bare number")]
        for i, (sev, col, txt) in enumerate(items):
            r = VGroup(T(str(i + 1), 28, ACCENT, BOLD), chip(sev, col, 18), T(txt, 28, INK))
            r.arrange(RIGHT, buff=0.35, aligned_edge=ORIGIN)
            rows.add(r)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([0, 0.1, 0])
        self.clear()
        self.steps("Three smaller notes: render shows no pace, the docs still said to try point nine first, "
                   "and one sixty-five was a bare number.",
                   [[FadeIn(rows[0])], [FadeIn(rows[1])], [FadeIn(rows[2])], [FadeIn(rows[3])]], pad=PAD)

        # ---- 3 The fix
        self.chapter("The fix", transition="blur", number=False, card=False, bridge="How was it fixed?")
        c1 = term(["    def speed_range(self, voice: str) -> tuple[float, float]:", "        return SPEED_RANGE"],
                  title="gnani.py:117", size=24, colors={"SPEED_RANGE": ACCENT}).move_to([0, 0.6, 0])
        rng = chip("SPEED_RANGE = (0.85, 1.15)", OK, 22).move_to([0, -1.1, 0])
        self.line("Each voice engine now reports the speeds it accepts.", FadeIn(c1), FadeIn(rng))
        c2 = term(["    want = suggested_speed(speed, pace)",
                   "    lowest = allowed[0] if allowed else 0.0",
                   "    if want >= lowest:",
                   "    if lowest < speed:"],
                  title="checks/audio.py:80-84 (lines between left out)", size=24, w=12.0,
                  colors={"lowest": ACCENT}).move_to([0, 0.5, 0])
        b = c2.row(3)
        cap1 = T("below the minimum: say the slowest the voice allows", 24, MUTED).move_to([0, -1.5, 0])
        cap2 = T("already at the minimum: shorten the narration, or use another voice", 24, MUTED).move_to([0, -1.5, 0])
        self.steps("The warning stops at the voice's lowest speed. If the speed is already that low, it says to "
                   "shorten the narration or use another voice.",
                   [[FadeOut(c1), FadeOut(rng), FadeIn(c2), FadeIn(b), FadeIn(cap1)],
                    [FadeIn(cap2), FadeOut(cap1)]], pad=PAD)
        self.clear()
        c3 = term(["PACE_MAX = 175  # words a minute; above this, narration sounds rushed",
                   "PACE_TARGET = 165  # words a minute the suggested speed aims for"],
                  title="checks/audio.py:13-14", size=20, colors={"PACE_TARGET": ACCENT}).move_to([0, 1.0, 0])
        chips = VGroup(chip("docs: use the suggested speed", OK, 24), chip("pace in render: a follow-up PR", MUTED, 24)
                       ).arrange(DOWN, buff=0.4, aligned_edge=LEFT).move_to([0, -1.2, 0])
        self.steps("One sixty-five is a named target beside the limit, and the docs say to use the suggested speed. "
                   "Pace in render waits for a follow-up, at the author's request.",
                   [[FadeIn(c3)], [FadeIn(chips[0])], [FadeIn(chips[1])]], pad=PAD)

        # ---- 4 The proof
        self.chapter("The proof", transition=whip(LEFT), number=False, card=False,
                     bridge="Does it hold up in real runs?")
        W = 12.9
        r1 = term(["pace: 277 words a minute",
                   "warning: faster than 175 words a minute; lower speed in series.json to 0.81",
                   "audio check: ok  (4 lines, all audible)"],
                  title="Kokoro af_heart, speed 1.35", size=19, w=W,
                  colors={"warning: faster than 175 words a minute; lower speed in series.json to 0.81": WARN,
                          "pace: 277 words a minute": ACCENT, "audio check: ok  (4 lines, all audible)": OK}
                  ).move_to([0, 1.5, 0])
        r2 = term(["pace: 164 words a minute", "audio check: ok  (4 lines, all audible)"],
                  title="speed 0.81, rendered again", size=19, w=W,
                  colors={"pace: 164 words a minute": ACCENT, "audio check: ok  (4 lines, all audible)": OK}
                  ).move_to([0, -1.2, 0])
        self.line("Kokoro at speed one point three five: two hundred seventy-seven words a minute, and a warning "
                  "to use point eight one.", FadeIn(r1))
        self.line("Set point eight one, render again: one sixty-four, and no warning.", FadeIn(r2))
        self.clear()
        g1 = term(["warning: faster than 175 words a minute; lower speed in series.json to 0.85,",
                   "  the slowest gnani:Kaveri allows (0.82 would reach 165)"],
                  title="Gnani, 200 words a minute, speed 1.0 (line wrapped)", size=19, w=W,
                  colors={"warning: faster than 175 words a minute; lower speed in series.json to 0.85,": WARN,
                          "  the slowest gnani:Kaveri allows (0.82 would reach 165)": WARN}).move_to([0, 1.6, 0])
        g2 = term(["warning: faster than 175 words a minute; speed is already 0.85, the slowest",
                   "  gnani:Kaveri allows; shorten the narration or use another voice"],
                  title="Gnani, speed 0.85 (line wrapped)", size=19, w=W,
                  colors={"warning: faster than 175 words a minute; speed is already 0.85, the slowest": WARN,
                          "  gnani:Kaveri allows; shorten the narration or use another voice": WARN}
                  ).move_to([0, -0.9, 0])
        self.line("Gnani at two hundred words a minute: the advice stops at point eight five, the slowest it "
                  "allows.", FadeIn(g1))
        self.line("Already at point eight five, it says to shorten the narration, or use another voice.", FadeIn(g2))
        self.clear()
        s = stat("1274", "tests passed on the PR head", OK, w=4.2)
        rf = chip("ruff clean", OK, 26)
        VGroup(s, rf).arrange(RIGHT, buff=0.9).move_to([0, 0.2, 0])
        self.line("The suite passes, twelve seventy-four tests, and ruff is clean.", FadeIn(s), FadeIn(rf))

        # ---- ending: the sum again, and the check run on this video
        self.clear()
        h = self.hand(red=False).scale(0.75).move_to([-3.45, 0.7, 0])
        final = term(["$ manimvox check audio ep01", f"pace: {FINAL_PACE} words a minute",
                      "audio check: ok  (21 lines, all audible)"],
                     title="this video's narration", size=17, w=6.4,
                     colors={f"pace: {FINAL_PACE} words a minute": ACCENT,
                             "audio check: ok  (21 lines, all audible)": OK}).move_to([3.4, 0.7, 0])
        self.play(FadeIn(h), FadeIn(final), run_time=0.6)
        self.outro([], "Run on this video's own narration, the check prints its pace, and no warning.",
                   answer="Yes, and its advice always fits the voice.", keep=[h, final],
                   end=["Pull request sixty-three", "closes issue twenty-one"])
