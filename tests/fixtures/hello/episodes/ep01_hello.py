from manimvox.kit import *  # noqa: F401,F403


class Ep01(Episode):
    EP = 1
    TITLE = "Hello"
    TAGLINE = "A two-line test episode"
    NCHAP = 1

    def build(self):
        self.intro("Hello from the test episode.")
        self.chapter("One idea", "This is the only chapter.")
        n = node("Box", "a node", color=AGENT).move_to(ORIGIN)
        self.say("Here is one box on the stage.", FadeIn(n))
        self.outro(["One box"], "That is all.")
