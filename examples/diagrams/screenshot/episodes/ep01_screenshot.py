from pathlib import Path

from manimvox.kit import *
from manimvox.scenes import screenshot

# a frame from the hash-map gallery video, already in the repo; positions below are its own pixels (1920 x 1080)
SHOT = Path(__file__).resolve().parents[3] / "gallery/directed-videos/research/screens/new-middle.png"


class Ep01(Episode):
    EP = 1
    TITLE = "Reading a screenshot"
    TAGLINE = "Naming the parts of a picture"
    NCHAP = 1

    def build(self):
        self.intro("A picture says more when its parts have names.")
        self.chapter("The parts", "Here is one frame from a video about a hash map.")
        shot = screenshot(SHOT, width=7.2).move_to(DOWN * 0.1)
        shot.set_z_index(-1)
        frame = SurroundingRectangle(shot, buff=0, color=LINE, stroke_width=1.5)
        key, fn, big, rest, box_ = leaders(
            [(shot.at(210, 270), "the key"), (shot.at(770, 215), "a hash function"),
             (shot.at(1500, 270), "the number it gives"), (shot.at(1735, 500), "the remainder"),
             (shot.at(1760, 805), "the box it picks")],
            side="both", x=3.9)
        self.play(FadeIn(shot), FadeIn(frame), run_time=0.8)
        self.say("The key on the left is what we look up.", key.grow())
        self.say("A hash function turns it into one big number.", LaggedStart(fn.grow(), big.grow(), lag_ratio=0.6))
        self.say("The remainder after dividing by eight picks the box,", rest.grow())
        self.say("and the key lands in that box.", box_.grow())
        self.beat(0.5)
        self.outro([], "Name the parts, and the picture explains itself.")
