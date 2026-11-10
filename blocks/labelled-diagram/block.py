"""A small architecture diagram, boxes joined by arrows, with a pointing label for each part."""
from manimvox.kit import *


def labelled_diagram(parts, color=BLUE, side="right", w=3.0, gap=0.55, at=LEFT * 2.2 + UP * 0.2):
    """`parts` are (name, note) pairs, top to bottom: the name goes in the box, the note is the label that points
    at it. `at` is where the boxes' centre goes (the labels need to be laid out there, so don't move the group after).
    Returns a VGroup with .nodes, .arrows and .labels (from `leaders`, so every label has .dot, .line and
    .label; `labels.grow()` animates them).
    Limits: `parts` must not be empty (ValueError)."""
    if not parts:
        raise ValueError("parts must not be empty")
    nodes = VGroup(*[node(name, w=w, color=color, size=20) for name, _ in parts]).arrange(DOWN, buff=gap)
    nodes.scale_to_fit_height(min(nodes.height, 5.6))
    nodes.move_to(at)  # labels are laid out where the boxes are now, so place them first
    arrows = VGroup(*[arrow(nodes[i], nodes[i + 1], buff=0.06) for i in range(len(nodes) - 1)])
    labels = leaders([(n.get_right(), note) for n, (_, note) in zip(nodes, parts)], side=side, size=20)
    g = VGroup(nodes, arrows, labels)
    g.nodes, g.arrows, g.labels = nodes, arrows, labels
    return g
