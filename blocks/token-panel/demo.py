from manimvox.kit import *
from blocks.token_panel import mark, token_panel


class Demo(Episode):
    def build(self):
        h = heading("Duplicate claims in one token")
        tok = token_panel(['"tenant": "acme"', '"role":   "buyer"', '"tenant": "platform"', '"role":   "admin"'],
                          title="login token (JWT), signed").move_to(LEFT * 3.2 + DOWN * 0.4)
        sig = chip("signature check reads the first tenant", OK, 17).move_to(RIGHT * 3.2 + UP * 0.5)
        auth = chip("permission check reads the last role", ERROR, 17).move_to(RIGHT * 3.2 + DOWN * 1.3)
        self.say("This token repeats its fields.", FadeIn(h, shift=DOWN * 0.2), FadeIn(tok))
        self.steps("One check reads the first tenant. Another reads the last role, and grants admin.",
                   [[Create(mark(tok, 0, color=OK)), FadeIn(sig)], [Create(mark(tok, 3, color=ERROR)), FadeIn(auth)]])
        self.wait(1)
