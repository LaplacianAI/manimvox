from manimvox.kit import *
from blocks.transitions_demo import KINDS, seam, transition_tile


class Demo(Episode):
    def build(self):
        for kind in KINDS:
            tile = transition_tile(kind).move_to(ORIGIN)
            self.say(f"The {kind} seam leaves from this tile.", FadeIn(tile))
            self.chapter(kind.title(), transition=seam(kind, tile))
        row = VGroup(*[transition_tile(k) for k in KINDS]).arrange(RIGHT, buff=0.25).scale(0.8).move_to(ORIGIN)
        self.say("Five seams, each caused by something on screen.", FadeIn(row))
        self.wait(1)
