from manimvox.kit import *
from blocks.code_diff import code_diff

BEFORE = """
def total(items):
    sum = 0
    for i in items:
        sum += i.price
    return sum
"""

AFTER = """
def total(items):
    return sum(i.price * i.qty for i in items)
"""


class Demo(Episode):
    def build(self):
        h = heading("One loop becomes one line")
        d = code_diff(BEFORE, AFTER).move_to(DOWN * 0.4)
        self.say("Here is the function before and after the change.",
                 FadeIn(h, shift=DOWN * 0.2), FadeIn(d.left), FadeIn(d.right))
        self.steps("Four lines of loop go, and one line that also counts quantity takes their place.",
                   [FadeIn(d.removed), FadeIn(d.added)])
        self.wait(1)
