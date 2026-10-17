from manimvox.kit import *
from blocks.line_by_level import line_by_level


class Demo(Episode):
    def build(self):
        h = heading("Did more effort help?", sub="Bugs found (of 62) at each effort level")
        chart = line_by_level(["low", "medium", "high", "xhigh", "max"],
                              [("Model A", [25, 30, 32, 43, 53], ACCENT), ("Model B", [1, 17, 41, 28, 42], TEAL)],
                              y_max=62, y_ticks=[0, 20, 40, 60]).move_to(DOWN * 0.55)
        a, b = chart.lines
        self.steps("Model A climbed steadily, from twenty-five at low effort to fifty-three at max.",
                   [[FadeIn(h, shift=DOWN * 0.2), FadeIn(chart.grid), FadeIn(chart.xlabels)],
                    FadeIn(chart.legend[0]), [Create(a[0]), FadeIn(a[1]), FadeIn(a[2])]])
        self.steps("Model B jumped around: forty-one at high, then twenty-eight.",
                   [[FadeIn(chart.legend[1]), Create(b[0]), FadeIn(b[1]), FadeIn(b[2])]])
        self.wait(1)
