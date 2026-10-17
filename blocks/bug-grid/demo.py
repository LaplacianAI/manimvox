from manimvox.kit import *
from blocks.bug_grid import bug_grid, light


class Demo(Episode):
    def build(self):
        h = heading("Recall", sub="Of 62 hidden bugs, how many were found?")
        g = bug_grid(62).move_to(UP * 0.2)
        result = T("53 of 62  =  85.5%", 30, ACCENT, BOLD).move_to(DOWN * 2.4)
        self.say("Here are sixty-two hidden bugs, one square each.",
                 FadeIn(h, shift=DOWN * 0.2), FadeIn(g, lag_ratio=0.02), run_time=1.6)
        self.say("The model found fifty-three of them.", light(g[:53]), FadeIn(result, shift=UP * 0.2),
                 run_time=2.4)
        self.wait(1)
