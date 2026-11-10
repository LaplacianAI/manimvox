"""Dots flowing through a chain of stages, with a dashed arrow in and a dashed arrow out."""
from manimvox.kit import *


def flow_stream(stages, inbound="in", outbound="out", color=ACCENT, w=2.0, gap=1.0):
    """`stages` are box labels, left to right. Returns a VGroup with .nodes, .stream (see `stream`: .fade_to(level),
    .brighten(), .stop()), .entry and .exit (the markers, with their labels). The dots start moving once the group is
    on stage and keep moving through self.say and self.wait.
    Limits: `stages` must not be empty (ValueError)."""
    if not stages:
        raise ValueError("stages must not be empty")
    nodes = VGroup(*[node(s, w=w, color=color, size=20) for s in stages]).arrange(RIGHT, buff=gap)
    fit(nodes, 10.0)
    s = stream([nodes[0].get_left() + LEFT * 0.3, nodes[0].get_right(), nodes[-1].get_left(),
                nodes[-1].get_right() + RIGHT * 0.3], color=color)
    s.set_z_index(-1)  # the dots pass behind the boxes, so they read as going through them
    entry = enters(nodes[0].get_left() + LEFT * 0.3, RIGHT, inbound, length=1.0)
    exit_ = leaves(nodes[-1].get_right() + RIGHT * 0.3, RIGHT, outbound, length=1.0)
    g = VGroup(nodes, s, entry, exit_)
    g.nodes, g.stream, g.entry, g.exit = nodes, s, entry, exit_
    return g
