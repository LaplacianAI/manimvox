from manimvox.kit import *
from blocks.bar_ranking import bar_ranking, grow, value_x


class Demo(Episode):
    def build(self):
        h = heading("Best score for each model", sub="Share of the hidden bugs found, %")
        data = [("Model A · max", 85.5), ("Model B · max", 67.7), ("Model C · ultra", 51.6),
                ("Model D · xhigh", 43.5), ("Model E · ultra", 27.4), ("Model F · high", 21.0),
                ("Model G · high", 12.9), ("Model H · low", 3.2)]
        chart = bar_ranking(data, max_value=100, colors={0: ACCENT, 1: TEAL, 2: BLUE}, row_h=0.5, size=18, fmt="{:.0f}")
        chart.move_to(DOWN * 0.45)
        x = value_x(chart, 50)
        fifty = DashedLine([x, chart.get_top()[1] + 0.15, 0], [x, chart.get_bottom()[1] - 0.1, 0],
                           dash_length=0.1).set_stroke(WARN, 2)
        self.say("Here is the best score for each model.", FadeIn(h, shift=DOWN * 0.2), grow(chart), run_time=2.4)
        self.say("Only three passed fifty percent.", Create(fifty))
        self.wait(1)
