"""Chapter 8, sound: the audio list's three kinds (say, music, sound), the footage's own sound under the voice,
and the mistake of two say lines that overlap. The tracks are drawn from the real audio (a narration line of the project's voice,
build/pad.wav, build/whoosh.wav, the demolition's crowd). Script: episodes/tour.md. Ends the 0.8.0 half."""
from bench import *

AUDIO = """\
{
  "duck_db": -14,
  "audio": [
    {"say": "Next, handheld footage.", "at": 1.2},
    {"music": "build/pad.wav", "volume": -20},
    {"sound": "build/whoosh.wav", "at": 6, "volume": -6}
  ]
}"""

SEC = 0.64  # scene units per second of the sketch film
X0 = -6.5  # where 0 s is
SPAN = 10  # seconds drawn
ROWS = {"say": 1.45, "music": 0.3, "sound": -0.85, "footage": -2.0}


class Ep08(Bench):
    EP = 8
    TITLE = "Sound"

    def build(self):
        title, enter = self.heading("Sound", "letters")
        panel = EditPanel(AUDIO, "edits/tour.json", size=19, w=6.0).move_to(PANEL_AT + UP * 0.1)
        panel.hide()

        def track(name, values, row, colour, start=0.0, seconds=SPAN, h=0.7, scale=1.0):
            """A labelled row of loudness: `values` span `seconds`, starting at `start` on the sketch film."""
            w = seconds * SEC
            wv = wave(values * scale, w, h, colour, 3).move_to([X0 + (start + seconds / 2) * SEC, ROWS[row], 0])
            lab = T(name, 22, MUTED).move_to([X0, ROWS[row] + 0.55, 0], aligned_edge=LEFT)
            base = Line([X0, ROWS[row], 0], [X0 + SPAN * SEC, ROWS[row], 0], color=LINE, stroke_width=1.5)
            return VGroup(base, lab, wv)

        # real loudness for every track
        # the voice: one of the project's own narration lines (the levelled cache of the voice)
        line = ".manimvox/tts/250f4cfc8f2d49c8_-16LUFS_-1.5dBTP.wav"
        voice = loudness(line if (HERE / line).exists() else INTERVIEW, 0.0 if (HERE / line).exists() else 14.0,
                         3.4 if (HERE / line).exists() else 17.4, 54)
        bed = 0.55 + 0.45 * loudness("build/pad.wav", 20, 30, 160)
        whoosh = loudness("build/whoosh.wav", 0, 1.2, 20)
        crowd = loudness(DEMOLITION, 29, 40, 160)

        said_at, said_len = 1.2, 3.4
        n_dip = range(int(said_at / SPAN * 160), int((said_at + said_len) / SPAN * 160))
        ducked = bed.copy()
        for k in n_dip:
            ducked[k] *= 0.3

        t_say = track("say", voice, "say", ACCENT, said_at, said_len)
        t_music = track("music", bed, "music", MUTED)
        t_sound = track("sound", whoosh, "sound", MUTED, 6.0, 1.2)
        t_foot = track("the clip's own sound", crowd, "footage", MUTED)
        t_foot_low = track("the clip's own sound", crowd, "footage", MUTED, scale=0.4)

        # ---- the audio list
        self.say("Everything so far has been picture. Now, everything you hear.", enter, FadeIn(panel.bg),
                 FadeIn(panel.head), run_time=1.0)
        self.say("The audio list holds three kinds of sound.", run_time=0.4)
        for r in panel.rows:
            r.set_opacity(1)
        self.play(*panel.light(3, 4, 5), run_time=0.6)

        # ---- say: the voice appears at its time
        self.say("A say line is narration, spoken in your project's voice at a time you give. That's how every "
                 "word you're hearing was made.", *panel.light(3),
                 FadeIn(t_say[0]), FadeIn(t_say[1]), LaggedStart(*[Create(s) for s in t_say[2]], lag_ratio=0.04),
                 run_time=2.4)

        # ---- music: a bed that dips where a voice is
        dipped = track("music", ducked, "music", ACCENT)
        self.say("A music bed plays under the film, looped, faded in and out, and it dips whenever anyone speaks, "
                 "by duck decibels.", *panel.light(4, 1),
                 FadeIn(t_music[0]), FadeIn(t_music[1]), FadeIn(t_music[2]),
                 run_time=1.2)
        self.play(Transform(t_music[2], dipped[2]), t_say[2].animate.set_color(MUTED), run_time=1.2)
        self.beat(0.3)

        # ---- sound: a file placed once
        self.say("And a sound places a file once: an effect, or a voice-over you recorded.", *panel.light(5),
                 t_music[2].animate.set_color(MUTED),
                 FadeIn(t_sound[0]), FadeIn(t_sound[1]), LaggedStart(*[Create(s) for s in t_sound[2]], lag_ratio=0.05),
                 run_time=1.6)
        self.play(t_sound[2].animate.set_color(ACCENT), run_time=0.5)

        # ---- the clip's own sound, well under the voice
        self.say("Each clip keeps its own sound too, levelled, and pushed down under narration so the voice is "
                 "always clear.", *panel.plain(), t_sound[2].animate.set_color(MUTED),
                 FadeIn(t_foot[0]), FadeIn(t_foot[1]), FadeIn(t_foot[2]), run_time=1.4)
        t_foot_low[2].set_color(ACCENT)
        self.play(Transform(t_foot[2], t_foot_low[2]), run_time=1.0)
        self.beat(0.5)
        self.show_result("r08")

        # ---- the mistake: two say lines overlapping, struck
        mistake = Mistake('{"say": "A second line, too soon.", "at": 2}', '"at": 4.1', SAID["overlap"][0],
                          w=6.0, size=20)
        mistake.move_to(LEFT * 3.4 + DOWN * 0.1)
        self.say("The mistake is two lines that overlap.", FadeOut(VGroup(t_say, t_music, t_sound, t_foot)),
                 *mistake.wrong_in(), *panel.light(3), run_time=1.4)
        self.say("The render refuses, and tells you the earliest time the second can start.", *mistake.struck(),
                 run_time=1.4)
        self.play(*mistake.fixed(), run_time=0.8)
        self.beat(1.0)

        self.say("So you write sound like everything else: what, and when.", *panel.plain(), FadeOut(mistake),
                 run_time=0.8)

        # ---- the seam: 0.8.0 ends, 0.8.5 is next
        clip = footage(DEMOLITION, 29, 40, CLIP_W).move_to(CLIP_AT)
        clip.clip.loop()
        tag = T("0.8.0", 40, MUTED, weight=BOLD).next_to(clip, DOWN, buff=0.3).align_to(clip, LEFT)
        newtag = T("0.8.5", 40, ACCENT, weight=BOLD).move_to(tag, aligned_edge=LEFT)
        self.say("That's every tool from version zero point eight.", FadeOut(panel), FadeOut(title), FadeIn(clip),
                 FadeIn(tag), run_time=1.0)
        self.play(Transform(tag, newtag), run_time=0.8)
        self.beat(0.3)
        nxt_tag = VGroup(T("next", 22, MUTED), T("Colour", 30, INK, weight=BOLD)).arrange(DOWN, aligned_edge=RIGHT, buff=0.08)
        nxt_tag.move_to([6.2, -3.0, 0], aligned_edge=RIGHT)
        self.say("Next, colour, the first of the new tools.", blur_in(nxt_tag), run_time=0.8)
        self.beat(0.6)
        clip.clip.clear_updaters()
        self.play(*[FadeOut(m) for m in self.stage()], run_time=0.8)
        self.beat(0.4)
