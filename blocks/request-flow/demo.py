from manimvox.kit import *
from blocks.request_flow import hop, request_flow


class Demo(Episode):
    def build(self):
        h = heading("Safe at every step, dangerous at the end")
        f = request_flow(["Input", "Parser", "Cache", "Browser"]).move_to(UP * 0.2)
        oks = VGroup(*[chip("looks safe", OK, 16).next_to(n, DOWN, buff=0.35) for n in f.nodes[:3]])
        bad = chip("dangerous", ERROR, 16, filled=True).next_to(f.nodes[3], DOWN, buff=0.35)
        self.steps("A value passes through a parser, then a cache, and looks safe each time.",
                   [[FadeIn(h, shift=DOWN * 0.2), FadeIn(f.nodes[0]), FadeIn(f.token), FadeIn(oks[0])],
                    [FadeIn(f.arrows[0]), FadeIn(f.nodes[1]), hop(f, 1), FadeIn(oks[1])],
                    [FadeIn(f.arrows[1]), FadeIn(f.nodes[2]), hop(f, 2), FadeIn(oks[2])]])
        self.say("Then the browser reads it differently, and it becomes dangerous.",
                 FadeIn(f.arrows[2]), FadeIn(f.nodes[3]), hop(f, 3, ERROR), FadeIn(bad), run_time=1.4)
        self.wait(1)
