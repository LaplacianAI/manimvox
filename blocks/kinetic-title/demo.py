from manimvox.kit import *
from blocks.kinetic_title import kinetic_title


class Demo(Episode):
    def build(self):
        a = kinetic_title("Why does the cache go cold?", sub="Word by word, no movement", accent="cold").move_to(UP * 2.0)
        b = kinetic_title("Letter by letter", size=44).move_to(ORIGIN)
        c = kinetic_title("Or settling in", sub="A fade with a hair of scale", size=44).move_to(DOWN * 2.1)
        self.say("A title can type in word by word.", a.enter("words"), run_time=1.6)
        self.say("One word can be picked out.", *a.land(), a.pick())
        self.say("Or letter by letter.", b.enter("letters"), run_time=1.4)
        self.say("Or settle in.", c.enter("blur"), *c.land())
        self.wait(1)
