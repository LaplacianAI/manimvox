"""Chapter 3, captions and spellings: captions on a clip, the top-level captions choice (srt, burn, none), a name the
transcript mishears ("I'm Joita Gupta" is real transcript text, 2.9 s into the file), spellings that fix it, the
loudness raised to the project's level, and the mistake of writing the pair backwards.
Script: episodes/tour.md."""
from bench import *

EDIT = """\
{
  "captions": "burn",
  "spellings": {
    "Joita": "Joyeeta",
    "UNESCO IT": "UNESCO-IHE"
  },
  "segments": [
    {"clip": "interview.webm",
     "start": 12.5, "end": 23,
     "from_words": "what is your role",
     "to_words": "two institutions together",
     "captions": true}
  ]
}"""

W = 6.4
AT = np.array([-3.4, -0.2, 0])
EDIT_AT = np.array([3.55, -0.2, 0])


def next_tag(name):
    """The small "next" tag at the bottom right: where the playlist goes after this chapter."""
    return VGroup(T("next", 22, MUTED), T(name, 30, INK, weight=BOLD)).arrange(DOWN, aligned_edge=RIGHT, buff=0.08)\
        .move_to([6.2, -3.0, 0], aligned_edge=RIGHT)


def cap(*words, colours=None):
    """A caption on a dark band, laid on the bottom of a clip: each word its own text so one can be coloured."""
    parts = [T(w, 26, (colours or {}).get(k, INK)) for k, w in enumerate(words)]
    line = VGroup(*parts).arrange(RIGHT, buff=0.14)
    if line.width > W - 0.8:
        line.scale_to_fit_width(W - 0.8)
    band = RoundedRectangle(corner_radius=0.08, width=max(4.6, line.width + 0.4), height=0.62, fill_color=BG,
                            fill_opacity=0.85, stroke_width=0)
    line.move_to(band)
    return VGroup(band, line)


def at_bottom(c, clip):
    return c.move_to(clip.get_bottom() + UP * 0.6)


class Ep03(Bench):
    EP = 3
    TITLE = "Captions and spellings"

    def build(self):
        _title, enter = self.heading("Captions and spellings", "write")
        clip = footage(INTERVIEW, 0.56, 11.8, W).move_to(AT)
        clip.clip.loop()
        self.add(clip)
        ed = EditPanel(EDIT, "edits/interview.json", size=18, w=6.0, step=0.34).move_to(EDIT_AT)

        # ---- captions: true on a clip
        c1 = at_bottom(cap("Professor", "of", "Environment", "and", "Development"), clip)
        self.say("Last chapter, the interview was cut by its own words. Now we make those words readable.", enter,
                 run_time=1.2)
        self.say("Captions true on a clip writes what the speaker says as captions, from the same transcript, at "
                 "the times the words land in the cut film.",
                 FadeIn(ed), *ed.light('"captions": true'), FadeIn(c1), run_time=1.4)

        # ---- the top-level choice
        chips = VGroup()
        for name, what in (("srt", "a subtitle file"), ("burn", "burned into the picture"), ("none", "no captions")):
            box_ = RoundedRectangle(corner_radius=0.08, width=2.05, height=0.7, fill_color=PANEL, fill_opacity=1,
                                    stroke_color=LINE, stroke_width=1.5)
            chips.add(VGroup(box_, T(f'"{name}"', 20, INK, font=MONO).move_to(box_.get_center() + UP * 0.12),
                             T(what, 13, MUTED).move_to(box_.get_center() + DOWN * 0.18)))
        chips.arrange(RIGHT, buff=0.12).next_to(clip, DOWN, buff=0.3).align_to(clip, LEFT)

        def pick(k):
            return [c[0].animate.set_stroke(ACCENT if j == k else LINE, 3 if j == k else 1.5) for j, c in
                    enumerate(chips)]
        self.steps("At the top of the file, captions chooses where they go: a subtitle file beside the video, burned "
                   "into the picture as well, or none.",
                   [[FadeIn(chips), *ed.light('"captions": "burn"'), *pick(0)], pick(1), pick(2)], run_time=0.8)

        # ---- the misheard name
        c2 = cap("I'm", "Joita", "Gupta", colours={1: ERROR})
        at_bottom(c2, clip)
        self.say("But speech-to-text mishears names. It hears her name as Joita.",
                 FadeOut(chips), FadeOut(c1), FadeIn(c2), *ed.plain(), run_time=0.9)
        self.beat(0.3)

        # ---- spellings
        c3 = cap("I'm", "Joyeeta", "Gupta", colours={1: OK})
        at_bottom(c3, clip)
        self.steps("Spellings fixes that: each heard form, written as the transcript spells it, with the right "
                   "spelling beside it.",
                   [ed.light('"Joita"'), [Transform(c2, c3)]], run_time=0.9)
        self.beat(0.3)

        # ---- loudness
        track_c = EDIT_AT + RIGHT * -2.3
        y_of = lambda db: track_c[1] - 2.2 + (db + 30) * 0.22
        track = Rectangle(width=0.9, height=4.4, stroke_color=LINE, stroke_width=2, fill_color=PANEL,
                          fill_opacity=1).move_to([track_c[0], track_c[1], 0])
        level = ValueTracker(-26)
        fill = always_redraw(lambda: Rectangle(width=0.9, height=(level.get_value() + 30) * 0.22, stroke_width=0,
                                               fill_color=ACCENT, fill_opacity=0.9)
                             .move_to([track_c[0], track_c[1] - 2.2 + (level.get_value() + 30) * 0.11, 0]))
        def mark(db, text, colour):
            y = y_of(db)
            return VGroup(Line([track_c[0] + 0.45, y, 0], [track_c[0] + 0.8, y, 0], color=colour, stroke_width=3),
                          T(text, 20, colour).move_to([track_c[0] + 0.95, y, 0], aligned_edge=LEFT))
        m_from = mark(-26, "-26 her recording", MUTED)
        m_to = mark(-16, "-16 the project's loudness", INK)
        m_cap = mark(-14, "-14 at most 12 dB up", MUTED)
        self.steps("One more thing happens without asking. Her recording is quiet, so manimvox raises it to the "
                   "project's loudness, but never by more than twelve decibels, so room noise never roars.",
                   [[FadeOut(ed), FadeIn(track), FadeIn(fill), FadeIn(m_from)],
                    [level.animate.set_value(-16), FadeIn(m_to)], FadeIn(m_cap)], run_time=1.4)
        self.beat(0.4)

        # ---- the result, played full frame with her own voice
        self.say("Her captions now spell her name and her institute correctly.", run_time=0.5)
        self.show_result("r03", lead=clip)

        # ---- the mistake
        mistake = Mistake('"Joyeeta": "Joita"', '"Joita": "Joyeeta"', None, w=6.0, size=24).move_to(EDIT_AT)
        self.say("The mistake is writing the pair the wrong way round.",
                 FadeOut(VGroup(track, fill, m_from, m_to, m_cap)), *mistake.wrong_in(), run_time=1.0)
        self.say("The key is what the transcript heard, and the value is what you want shown.", *mistake.struck(),
                 *mistake.fixed(), run_time=1.6)
        self.beat(1.0)

        ed2 = EditPanel(EDIT, "edits/interview.json", size=18, w=6.0, step=0.34).move_to(EDIT_AT)
        self.say("So captions come from the transcript, and spellings fix what it mishears.", FadeOut(mistake),
                 FadeIn(ed2), *ed2.light('"captions"', '"Joita"', '"UNESCO IT"'), run_time=0.9)
        nxt = next_tag("Joining pieces")
        self.say("Next, joining the pieces.", FadeOut(ed2), blur_in(nxt), run_time=0.9)
        self.play(*[FadeOut(m) for m in self.stage()], run_time=0.8)
        self.beat(0.4)
