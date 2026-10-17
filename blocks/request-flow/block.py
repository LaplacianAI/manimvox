"""A value passing through a chain of stages: boxes joined by arrows, and a token that hops from box to box."""
from manimvox.kit import *


def request_flow(stages, w=2.4, color=BLUE, gap=0.9, size=19, token_color=ACCENT):
    """`stages` are the box labels, left to right. Returns a VGroup with .nodes, .arrows and .token (a dot above
    the first stage). Reveal the stages one by one; move the token with `hop(flow, i)`.
    Limits: `stages` must not be empty (ValueError)."""
    if not stages:
        raise ValueError("stages must not be empty")
    nodes, arrows = flow(stages, w=w, color=color, gap=gap, size=size)
    token = Dot(radius=0.13, color=token_color).move_to(nodes[0].get_top() + UP * 0.3)
    g = VGroup(nodes, arrows, token)
    g.nodes, g.arrows, g.token = nodes, arrows, token
    return g


def hop(chart, i, color=None):
    """The animation that moves the token above stage `i`, recolouring it when `color` is given.
    Limits: `i` must be a stage index of the flow (ValueError)."""
    if not 0 <= i < len(chart.nodes):
        raise ValueError(f"stage {i} is not within the flow's {len(chart.nodes)} stages")
    anim = chart.token.animate.move_to(chart.nodes[i].get_top() + UP * 0.3)
    return anim.set_color(color) if color else anim
