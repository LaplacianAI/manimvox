"""Chapter 10, green screen: the green-screen shoot (green-screen.ogv, 72 to 77 s) and the mountain, key on a clip
overlay (auto, then similarity, softness and spill at their defaults 0.12, 0.08, 0.6), a clip overlay with no box
filling the frame over the main track, before and after, and the mistake of a similarity that eats the subject's
edges. Script: episodes/tour.md."""
from bench import *

FILE = """\
{
  "segments": [
    {"image": "build/mountain.png",
     "seconds": 5, "move": "push"}
  ],
  "overlays": [
    {"clip": "green-screen.ogv",
     "start": 72, "at": 0, "until": 5,
     "key": "auto"}
  ]
}"""

KEYED = """\
"overlays": [
  {"clip": "green-screen.ogv",
   "start": 72, "at": 0, "until": 5,
   "key": {
     "color": "auto",
     "similarity": 0.12,
     "softness": 0.08,
     "spill": 0.6
   }}
]"""


def slider(name, value, w=2.0):
    """A control from 0 to 1 with its knob at `value`: (the whole control, the knob, the filled part)."""
    track = Line(LEFT * w / 2, RIGHT * w / 2, color=LINE, stroke_width=5)
    x = -w / 2 + value * w
    fill = Line(LEFT * w / 2, RIGHT * w / 2 * 0 + RIGHT * x, color=ACCENT, stroke_width=5)
    knob = Dot(RIGHT * x, radius=0.1, color=INK)
    label = T(f"{name}  {value:g}", 19, MUTED).next_to(track, UP, buff=0.18).align_to(track, LEFT)
    return VGroup(label, track, fill, knob), knob, fill


class Ep10(Bench):
    EP = 10
    TITLE = "Green screen"

    def build(self):
        title, enter = self.heading("Green screen", "write")
        clip = footage(CHROMA, 72.0, 77.0, CLIP_W).move_to(CLIP_AT)
        clip.clip.loop()
        mountain = picture("build/mountain.png", 5.4).move_to(PANEL_AT + RIGHT * 0.25)
        panel = EditPanel(FILE, "edits/tour.json", size=19, w=5.6).move_to(PANEL_AT + RIGHT * 0.25)
        expanded = EditPanel(KEYED, "edits/tour.json", size=19, w=5.6).move_to(PANEL_AT + RIGHT * 0.25)

        self.say("Last chapter changed a picture's colours. Now we take one colour away entirely.", enter,
                 FadeIn(clip), FadeIn(mountain), run_time=1.4)
        self.say("A green screen is a bright sheet behind the subject, so the sheet can be made see-through and "
                 "something else shown behind.", run_time=0.4)
        self.beat(0.4)

        # ---- key: auto
        self.say("Key on a clip overlay does that. Auto finds the screen's colour from the clearly green or blue "
                 "pixels round the edge of the frame.", FadeOut(mountain), FadeIn(panel), run_time=1.0)
        edge = SurroundingRectangle(clip, color=ACCENT, buff=-0.0, stroke_width=3)
        self.play(*panel.light("\"key\""), Create(edge), run_time=0.8)

        # ---- the three controls
        sim, _sim_knob, _sim_fill = slider("similarity", 0.12)
        soft, _soft_knob, _soft_fill = slider("softness", 0.08)
        spill, _spill_knob, _spill_fill = slider("spill", 0.6)
        sliders = VGroup(sim, soft, spill).arrange(RIGHT, buff=0.35).move_to([CLIP_AT[0], -2.75, 0])
        sliders.set_opacity(0.0)
        self.add(sliders)
        self.play(FadeOut(edge), FadeOut(panel), FadeIn(expanded), run_time=0.8)
        self.steps("Similarity is how close to the screen a pixel must be to vanish. Softness softens the edge, for "
                   "hair and motion. Spill takes the screen's green glow off the subject.",
                   [[sim.animate.set_opacity(1), *expanded.light("\"similarity\"")],
                    [sim.animate.set_opacity(0.45), soft.animate.set_opacity(1), *expanded.light("\"softness\"")],
                    [soft.animate.set_opacity(0.45), spill.animate.set_opacity(1), *expanded.light("\"spill\"")]],
                   run_time=0.8)

        # ---- no box: the overlay fills the frame, the main track shows through
        keyed = result("keyed").move_to(CLIP_AT)
        keyed.clip.loop()
        under = T("the main track shows through where the screen was", 22, MUTED).next_to(keyed, DOWN, buff=0.25)
        under.align_to(keyed, LEFT)
        clip.clip.clear_updaters()
        self.say("With no box, the clip overlay fills the frame, and the main track shows through where the screen "
                 "was.", FadeOut(sliders), FadeOut(clip), FadeIn(keyed), FadeIn(under), *expanded.light("\"key\""),
                 run_time=1.4)
        self.beat(1.0)
        keyed.clip.clear_updaters()
        self.show_result("r10", lead=keyed)

        # ---- before and after
        pair, tags = before_after(footage(CHROMA, 72.0, 77.0), result("keyed"))
        for m in pair:
            m.clip.loop()
        self.say("Before, and after.", FadeOut(keyed), FadeOut(under), FadeOut(expanded), FadeIn(pair),
                 FadeIn(tags), run_time=1.0)
        self.beat(3.0)
        for m in pair:
            m.clip.clear_updaters()

        # ---- the mistake: a similarity that eats the edges
        bad = result("keyed_bad", 6.4).move_to(LEFT * 3.4 + DOWN * 0.2)
        bad.clip.loop()
        mistake = Mistake('"similarity": 0.5', '"similarity": 0.12', w=5.4, size=24).move_to(RIGHT * 3.5 + UP * 0.2)
        self.say("The mistake is a similarity so high it eats the subject's edges.", FadeOut(pair), FadeOut(tags),
                 FadeIn(bad), *mistake.wrong_in(), run_time=1.4)
        self.say("Raise it only until the screen is gone.", *mistake.struck(), *mistake.fixed(), run_time=1.4)
        self.beat(1.0)

        # ---- takeaway, then the bridge back to the demolition
        bad.clip.clear_updaters()
        panel2 = EditPanel(KEYED, "edits/tour.json", size=19, w=5.6).move_to(PANEL_AT + RIGHT * 0.25)
        nxt = footage(CHROMA, 72.0, 77.0).move_to(CLIP_AT)
        nxt.clip.loop()
        self.say("So a key turns a green sheet into anywhere you like.", FadeOut(bad), FadeOut(mistake),
                 FadeIn(nxt), FadeIn(panel2), run_time=1.0)
        shake = footage(DEMOLITION, 12.0, 28.0, 3.6).move_to(RIGHT * 3.55 + UP * 0.2)
        shake.clip.loop()
        self.play(FadeOut(panel2), FadeOut(title), FadeIn(shake), run_time=0.8)
        self.beat(0.4)
        nxt_tag = VGroup(T("next", 22, MUTED), T("Steady", 30, INK, weight=BOLD)).arrange(DOWN, aligned_edge=RIGHT, buff=0.08)
        nxt_tag.move_to([6.2, -3.0, 0], aligned_edge=RIGHT)
        self.say("Next, steadying a shaky camera.", blur_in(nxt_tag), run_time=0.8)
        self.beat(0.6)
        nxt.clip.clear_updaters()
        shake.clip.clear_updaters()
        self.play(*[FadeOut(m) for m in self.stage()], run_time=0.8)
        self.beat(0.4)
