from manimvox.kit import *
from blocks.venn import venn


class Demo(Episode):
    def build(self):
        h = heading("Two reviewers, one codebase", sub="Bugs each found, and bugs both found")
        v = venn("Reviewer A: 20 found", "Reviewer B: 22 found", (5, 15, 7)).move_to(DOWN * 0.5)
        self.steps("Reviewer A found twenty bugs. Reviewer B found twenty-two.",
                   [[FadeIn(h, shift=DOWN * 0.2), DrawBorderThenFill(v.A), FadeIn(v.la)],
                    [DrawBorderThenFill(v.B), FadeIn(v.lb)]])
        self.steps("Fifteen were found by both, five only by A, and seven only by B.",
                   [FadeIn(v.tm, scale=1.3), FadeIn(v.ta, scale=1.3), FadeIn(v.tb, scale=1.3)])
        self.wait(1)
