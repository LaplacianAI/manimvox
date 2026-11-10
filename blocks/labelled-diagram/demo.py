from manimvox.kit import *
from blocks.labelled_diagram import labelled_diagram


class Demo(Episode):
    def build(self):
        d = labelled_diagram([("Browser", "asks for the page"), ("Gateway", "checks who you are"),
                              ("Service", "does the work"), ("Database", "remembers the result")])
        self.say("A request passes through four parts.", FadeIn(d.nodes), FadeIn(d.arrows))
        self.say("Each one has a single job, named where it sits.", d.labels.grow())
        self.wait(1)
