from manimvox.kit import *
from blocks.donut import donut, grow


class Demo(Episode):
    def build(self):
        h = heading("Where the time goes", sub="Share of a typical week, hours")
        data = [("Meetings", 9), ("Focused work", 18), ("Code review", 6), ("Planning", 4),
                ("Support requests", 2.5), ("Learning", 1.5)]
        chart = donut(data, total_label="hours a week")
        chart.move_to(DOWN * 0.55)
        self.say("Here is how the week divides.", FadeIn(h, shift=DOWN * 0.2), grow(chart), run_time=3)
        self.wait(1)
