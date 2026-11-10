from manimvox.kit import *
from blocks.flow_stream import flow_stream


class Demo(Episode):
    def build(self):
        f = flow_stream(["Queue", "Worker", "Store"], inbound="jobs in", outbound="results out").move_to(UP * 0.2)
        self.say("Jobs come in on the left and results leave on the right.",
                 FadeIn(f.nodes), FadeIn(f.entry), FadeIn(f.exit))
        self.add(f.stream)
        self.say("They flow through the queue, the worker and the store.")
        self.say("When the store is slow, the flow dims while we look at it.", f.stream.fade_to(0.25))
        self.say("Once it catches up, it brightens again.", f.stream.brighten())
        self.wait(1)
