from manimvox.kit import *
from blocks.sequence_diagram import sequence_diagram


class Demo(Episode):
    def build(self):
        h = heading("Starting a run")
        d = sequence_diagram(["Client", "Server", "Store"],
                             [("Client", "Server", "POST /runs"), ("Server", "Store", "save run"),
                              ("Store", "Server", "saved", "reply"), ("Server", "Client", "202 Accepted", "reply")])
        self.say("Three parts take part: a client, a server and a store.",
                 FadeIn(h, shift=DOWN * 0.2), FadeIn(d.lifelines, lag_ratio=0.2))
        self.steps("The client posts a run. The server saves it. The store confirms, and the server accepts.",
                   [FadeIn(m) for m in d.messages])
        self.wait(1)
