from manimvox.kit import *
from blocks.end_card import end_card


class Demo(Episode):
    def build(self):
        card = end_card(["It was the missing index.", "Next time: how to find it before it bites.", "Part two of three"])
        card.move_to(STAGE_CENTER)
        self.steps("The card is carried in line by line, and the rule is wiped in last.", card.build())
        self.wait(1)
