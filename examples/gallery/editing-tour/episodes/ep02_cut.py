"""Chapter 2, cut by what is said: the transcript (every word with its time), from_words and to_words, the cut moved
to just outside the speech, cut_silences and cut_fillers, the interview before and after, and the mistake of a phrase
said twice. The waveform is the interview's own sound; the words and times are the real transcript
(build/edit/transcripts). Script: episodes/tour.md. Terminal output is real (build/said.json)."""
import json

from bench import *

WORDS = json.loads(next((HERE / "build" / "edit" / "transcripts").glob("*.json")).read_text())["words"]

CUT = """\
{
  "segments": [
    {"clip": "interview.webm",
     "start": 12.5, "end": 23,
     "from_words": "what is your role",
     "to_words": "two institutions together",
     "cut_silences": 0.5,
     "cut_fillers": true}
  ]
}"""

SPAN = 22.0  # seconds of the interview the waveform shows
GAPS = [(2.16, 2.79), (11.80, 14.03), (14.99, 15.93)]  # the pauses check edit drops (its own report)


def transcript_src():
    """Every word from the answer's first line on, one line each, with the second it was said."""
    rows = [w for w in WORDS if 12.9 <= w["start"] < 17.7]
    return "\n".join(f"{w['start']:5.2f}   {w['text']}" for w in rows)


def next_tag(name):
    """The small "next" tag at the bottom right: where the playlist goes after this chapter."""
    return VGroup(T("next", 22, MUTED), T(name, 30, INK, weight=BOLD)).arrange(DOWN, aligned_edge=RIGHT, buff=0.08)\
        .move_to([6.2, -3.0, 0], aligned_edge=RIGHT)


def speaker_muted(s=1.0):
    body = Polygon([-0.5, -0.25, 0], [-0.2, -0.25, 0], [0.2, -0.6, 0], [0.2, 0.6, 0], [-0.2, 0.25, 0],
                   [-0.5, 0.25, 0], color=MUTED, fill_color=MUTED, fill_opacity=1, stroke_width=0)
    slash = Line([-0.6, 0.7, 0], [0.7, -0.7, 0], color=MUTED, stroke_width=6)
    return VGroup(body, slash).scale(s)


class Ep02(Bench):
    EP = 2
    TITLE = "Cut by what is said"

    def build(self):
        _title, enter = self.heading("Cut by what is said", "blur")
        clip = footage(INTERVIEW, 0.0, 23.0).move_to(CLIP_AT)
        self.add(clip)

        # ---- the transcript
        words = EditPanel(transcript_src(), "transcript", size=19, w=4.4).move_to(PANEL_AT + RIGHT * 0.5)
        self.say("Last chapter, you met the edit file and check edit. Now we use them on the interview.", enter,
                 run_time=1.2)
        self.say("To cut an interview by hand, you scrub back and forth to find each word. Instead, manimvox can "
                 "write down every word with its time, using speech-to-text that runs on your computer.",
                 FadeIn(words), run_time=1.0)

        term = Terminal("manimvox edit probe interview.webm --transcribe",
                        [SAID["transcribe"][0], *SAID["transcribe"][2:]], w=5.6, size=16, keep=7)
        term.move_to(PANEL_AT + UP * 0.2)
        filled = EditPanel(transcript_src(), "transcript", size=19, w=4.4).move_to(PANEL_AT + RIGHT * 0.5)
        filled.hide()
        clip.clip.loop()
        self.steps("Run probe with the transcribe option, and you get the transcript, every word with the second "
                   "it was said.",
                   [[FadeOut(words), *term.run()],
                    [FadeOut(term), FadeIn(filled.bg), FadeIn(filled.head),
                     LaggedStart(*[r.animate.set_opacity(1) for r in filled.rows], lag_ratio=0.12)]],
                   run_time=1.6)
        self.beat(0.3)

        # ---- from_words, to_words
        ed = EditPanel(CUT, "edits/interview.json", size=19).move_to(PANEL_AT)
        self.steps("Now a clip can start and end at words. From words is the phrase it starts on, and to words the "
                   "phrase it ends on, copied from the transcript.",
                   [[FadeOut(filled), FadeIn(ed), *ed.light("from_words")], ed.light("to_words")], run_time=0.9)

        # ---- the cut lands just outside the speech
        wx0, wy = -6.6, -2.15
        def x_at(t):
            return wx0 + t / SPAN * CLIP_W
        wv = wave(loudness(INTERVIEW, 0, SPAN, 110), CLIP_W, 1.3, MUTED, 3).move_to([-3.0, wy, 0])
        axis = Line([wx0, wy - 0.8, 0], [wx0 + CLIP_W, wy - 0.8, 0], color=LINE, stroke_width=2)
        marks = VGroup(*[Line([x_at(t), wy - 0.8, 0], [x_at(t), wy + 0.8, 0], color=ACCENT, stroke_width=5)
                         for t in (0.0, 11.74)])
        self.steps("Speech-to-text gets the words right but the times a little wrong, so manimvox moves each cut to "
                   "just outside the speech it hears, and never cuts inside a word.",
                   [[clip.animate.scale(5.6 / CLIP_W).move_to([-3.0, 0.9, 0]), FadeIn(wv), FadeIn(axis),
                     *ed.light('"start"')],
                    [Create(marks)],
                    [marks[0].animate.move_to([x_at(0.56), wy, 0]), marks[1].animate.move_to([x_at(11.80), wy, 0])]],
                   run_time=1.1)
        self.beat(0.3)

        # ---- cut_silences
        shades = VGroup(*[Rectangle(width=(b - a) / SPAN * CLIP_W, height=1.6, stroke_width=0, fill_color=ACCENT,
                                    fill_opacity=0.28).move_to([x_at((a + b) / 2), wy, 0]) for a, b in GAPS])
        gone = VGroup(*[bar for k, bar in enumerate(wv)
                        if any(a <= (k + 0.5) / len(wv) * SPAN <= b for a, b in GAPS)])
        self.steps("Cut silences removes every pause longer than the number you give, here half a second.",
                   [[FadeOut(marks), *ed.light("cut_silences")], [FadeIn(shades)], [FadeOut(gone), FadeOut(shades)]],
                   run_time=0.8)

        # ---- cut_fillers
        phrase = [T(w, 26, INK) for w in ["what", "is", "your", "role,", "um,", "today", "at", "UNESCO", "IT?"]]
        line = VGroup(*phrase).arrange(RIGHT, buff=0.16).scale_to_fit_width(6.8).move_to([-3.0, wy, 0])
        strike = Line(phrase[4].get_left() + LEFT * 0.05, phrase[4].get_right() + RIGHT * 0.05, color=MUTED,
                      stroke_width=4)
        self.steps("And cut fillers removes the ums and uhs. Each clip with cuts plays as several pieces, joined by "
                   "cuts.",
                   [[FadeOut(VGroup(wv, axis)), *ed.light("cut_fillers")], FadeIn(line),
                    [phrase[4].animate.set_color(ACCENT), Create(strike)],
                    [phrase[4].animate.set_opacity(0.3), strike.animate.set_opacity(0.3)]],
                   run_time=0.8)
        self.beat(0.3)

        # ---- the result, played full frame with her own voice
        self.say("Here is the interview, cut by its own words, with the pauses and the um taken out.", run_time=0.5)
        self.show_result("r02", lead=clip)

        # ---- before and after: the same seconds of the file
        clip.clip.clear_updaters()
        pair, tags = before_after(footage(INTERVIEW, 0.56, 21.64), footage(RESULTS, WINDOWS["question"][0],
                                                                         WINDOWS["answer"][1]),
                                  labels=("21 seconds of recording", "17 seconds, cut"))
        before, after = pair
        for m in (before, after):
            m.clip.loop()
        raw_len, cut_len = 21.08, 17.28
        strip_w = before.width
        strip_a = wave(loudness(INTERVIEW, 0.56, 21.64, 100), strip_w, 0.5, MUTED, 2)
        strip_b = wave(loudness(RESULTS, WINDOWS["question"][0], WINDOWS["answer"][1], 82), strip_w * cut_len / raw_len,
                       0.5, MUTED, 2)
        strip_a.next_to(before, DOWN, buff=0.3)
        strip_b.next_to(after, DOWN, buff=0.3).align_to(after, LEFT)
        gaps = VGroup(*[Rectangle(width=(b - a) / raw_len * strip_w, height=0.6, stroke_width=0, fill_color=ACCENT,
                                  fill_opacity=0.3).move_to([strip_a.get_left()[0] + ((a + b) / 2 - 0.56) / raw_len
                                                             * strip_w, strip_a.get_center()[1], 0])
                        for a, b in GAPS if b < 21.64 and a > 0.56])
        self.say("Twenty-one seconds of recording became seventeen, and every word she said is still there.",
                 FadeOut(clip), FadeOut(ed), FadeOut(line), FadeOut(strike),
                 FadeIn(pair), FadeIn(tags), FadeIn(strip_a), FadeIn(strip_b), FadeIn(gaps), run_time=1.4)
        self.beat(1.2)

        # ---- the mistake
        for m in (before, after):
            m.clip.clear_updaters()
        clip = footage(INTERVIEW, 12.5, 23.0).move_to(CLIP_AT)
        clip.clip.loop()
        mistake = Mistake('"from_words": "UNESCO"', '"from_words": "today at UNESCO"', SAID["twice"][0], w=5.4,
                          size=20).move_to(PANEL_AT + RIGHT * 0.25)
        self.say("The mistake is a phrase said twice between start and end.",
                 FadeOut(pair), FadeOut(tags), FadeOut(strip_a), FadeOut(strip_b), FadeOut(gaps), FadeIn(clip),
                 *mistake.wrong_in(), run_time=1.0)
        self.say("Check edit refuses it and says where each one is, so make the phrase longer or the window "
                 "shorter.", *mistake.struck(), *mistake.fixed(), run_time=1.8)
        self.beat(1.0)

        # ---- takeaway and bridge
        ed2 = EditPanel(CUT, "edits/interview.json", size=19).move_to(PANEL_AT)
        self.say("So you cut speech by what is said, not by scrubbing.", FadeOut(mistake), FadeIn(ed2),
                 *ed2.light("from_words", "to_words", "cut_silences", "cut_fillers"), run_time=0.9)
        mute = speaker_muted(1.4).move_to(PANEL_AT)
        self.say("But now you can't see what she says without sound.", FadeOut(ed2), FadeIn(mute), run_time=0.8)
        self.beat(0.4)

        # ---- the next chapter
        nxt = next_tag("Captions and spellings")
        self.say("Next, captions and spellings.", FadeOut(mute), blur_in(nxt), run_time=0.9)
        self.play(*[FadeOut(m) for m in self.stage()], run_time=0.8)
        self.beat(0.4)
