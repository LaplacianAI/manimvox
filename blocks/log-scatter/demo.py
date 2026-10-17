from manimvox.kit import *
from blocks.log_scatter import log_scatter


class Demo(Episode):
    def build(self):
        h = heading("What does a run cost?", sub="Score against the cost of one run, log scale")
        chart = log_scatter(
            [("Model A · max  $24", 24.45, 85.5, ACCENT), ("Model B · high  $9.80", 9.79, 66.1, TEAL),
             ("Model C · max  $1.54", 1.54, 25.8, MUTED), ("Model D · high  $0.05", 0.054, 11.3, MUTED)],
            x_range=(0.03, 30), x_ticks=[(0.03, "$0.03"), (0.3, "$0.30"), (3, "$3"), (30, "$30")],
            y_ticks=[(0, "0"), (50, "50"), (100, "100")]).move_to(DOWN * 0.5)
        m = chart.marks
        self.steps("The strongest model cost about twenty-four dollars a run. The runner-up cost under ten.",
                   [[FadeIn(h, shift=DOWN * 0.2), FadeIn(chart.axes)], FadeIn(m[0], scale=0.8),
                    FadeIn(m[1], scale=0.8)])
        self.steps("The cheapest cost pennies, and found far less.", [FadeIn(m[2], scale=0.8), FadeIn(m[3], scale=0.8)])
        self.wait(1)
