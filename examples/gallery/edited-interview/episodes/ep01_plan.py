"""The plan Prof Gupta lists in the interview (1:16 to 1:40), drawn between her two answers: two institutions,
the agreement between them, colleagues going both ways, and what they will make together. Every number is hers
(FACTS.md)."""
from manimvox.kit import *

IHE, UVA = [-4.5, 1.0, 0], [4.5, 1.0, 0]  # inside the 13.2-unit safe stage, with room between for the link
W, H = 4.0, 1.8


def institution(lines, field, at):
    """An institution as a panel: its name (one or two lines), and under it what it specialises in."""
    b = box(W, H, fill=PANEL, stroke=LINE)
    name = VGroup(*(T(s, 28, INK, weight=BOLD) for s in lines)).arrange(DOWN, buff=0.06)
    b.add(VGroup(name, T(field, 24, MUTED)).arrange(DOWN, buff=0.14).move_to(b))
    return b.move_to(at).set_z_index(2)


def made(n, what):
    """One thing they will make together: its number large, its name under it."""
    return VGroup(T(str(n), 52, ACCENT, weight=BOLD), T(what, 24, INK)).arrange(DOWN, buff=0.08)


class Ep01(Episode):
    EP = 1
    TITLE = "The plan she describes"
    TAGLINE = "Two institutions, one programme"
    NCHAP = 1
    CHROME = ()

    def build(self):
        ihe = institution(["UNESCO-IHE"], "water education", IHE)
        uva = institution(["University of", "Amsterdam"], "social science", UVA)
        mou = DashedLine(ihe.get_right(), uva.get_left(), color=LINE, dash_length=0.12).set_z_index(1)
        mou_name = T("memorandum of understanding", 22, MUTED).next_to(mou, UP, buff=0.55)  # clear of the dots

        go = stream([ihe.get_right() + UP * 0.25, uva.get_left() + UP * 0.25], color=ACCENT, n=3, speed=0.18, size=0.09)
        back = stream([uva.get_left() + DOWN * 0.25, ihe.get_right() + DOWN * 0.25], color=ACCENT, n=3, speed=0.18,
                      size=0.09)
        each_way = T("3 colleagues each way", 24, ACCENT).next_to(mou, DOWN, buff=0.6)
        for f in (go, back):
            f.level.set_value(0)
            f.set_z_index(1)

        outputs = VGroup(made(3, "joint PhDs"), made(2, "special issues"), made(1, "joint research project"))
        outputs.arrange(RIGHT, buff=1.4).move_to([0, -2.2, 0])

        self.add(go, back)
        self.say("She describes a plan that joins a water institute and a social science department.",
                 FadeIn(ihe, shift=RIGHT * 0.2), FadeIn(uva, shift=LEFT * 0.2), Create(mou), FadeIn(mou_name),
                 run_time=1.4)
        self.say("Three colleagues will move each way, to work at the other.",
                 go.fade_to(1.0), back.fade_to(1.0), FadeIn(each_way), run_time=1.0)
        with self.narrate("Then three joint PhDs, two special issues, and a joint research project.") as dur:
            self.play(LaggedStart(*(FadeIn(o, shift=UP * 0.15) for o in outputs), lag_ratio=0.45),
                      go.fade_to(0.35), back.fade_to(0.35), run_time=min(dur, 2.4))
        self.beat(0.6)
