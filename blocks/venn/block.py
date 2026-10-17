"""Two overlapping circles with a count in each region: what only A has, what both have, what only B has."""
from manimvox.kit import *


def venn(left, right, counts, colors=(BLUE, TEAL), r=1.55, d=1.8, size=44):
    """Two circles `d` apart. `counts` is (only left, both, only right); `left` and `right` label the circles.
    Returns a VGroup with .A and .B (the circles), .la and .lb (their labels) and .ta, .tm and .tb (the counts
    in the left, middle and right regions), to reveal one by one as the narration names them."""
    a_only, both, b_only = counts
    ca, cb = colors
    A = Circle(radius=r).set_fill(ca, 0.16).set_stroke(ca, 3).shift(LEFT * d / 2)
    B = Circle(radius=r).set_fill(cb, 0.16).set_stroke(cb, 3).shift(RIGHT * d / 2)
    ta = T(str(a_only), size, ca, BOLD).move_to(LEFT * r)
    tm = T(str(both), size, INK, BOLD).move_to(ORIGIN)
    tb = T(str(b_only), size, cb, BOLD).move_to(RIGHT * r)
    label_w = r + d / 2 - 0.15
    la = T(left, 20, ca, BOLD, max_w=label_w).next_to(A, UP, buff=0.15).align_to(A, LEFT)
    lb = T(right, 20, cb, BOLD, max_w=label_w).next_to(B, UP, buff=0.15).align_to(B, RIGHT)
    g = VGroup(A, B, la, lb, ta, tm, tb)
    g.A, g.B, g.la, g.lb, g.ta, g.tm, g.tb = A, B, la, lb, ta, tm, tb
    return g
