"""Actors as lifelines and the messages between them, top to bottom, one message per line of narration."""
from manimvox.kit import *


def sequence_diagram(actors, messages, top=2.1, bottom=-3.1, width=11.0, colors=None, size=15):
    """`actors` are column names, left to right, spread across `width`. `messages` are (from, to, label) or
    (from, to, label, "reply"), naming actors as in `actors`; replies are dashed and muted. Returns a VGroup
    with .lifelines (one per actor) and .messages (in order, to reveal one at a time).
    Limits: at least 2 actors with distinct names, and every message names actors from `actors` (ValueError)."""
    n = len(actors)
    if n < 2:
        raise ValueError("actors needs at least 2 names")
    if len(set(actors)) != n:
        raise ValueError("actors must have distinct names")
    xs = [-width / 2 + width * i / (n - 1) for i in range(n)]
    cols = colors or [BLUE] * n
    lanes = VGroup(*[lifeline(a, x, top=top, bottom=bottom, color=cols[i], w=min(2.3, width / max(1, n) - 0.3))
                     for i, (a, x) in enumerate(zip(actors, xs))])
    lane = dict(zip(actors, lanes))
    step = (top - 0.9 - bottom) / (len(messages) + 1)
    msgs = VGroup()
    for k, m in enumerate(messages):
        a, b, label = m[0], m[1], m[2]
        if a not in lane or b not in lane:
            raise ValueError(f"message {k + 1} names an actor that is not in {list(actors)}")
        reply = len(m) > 3 and m[3] == "reply"
        msgs.add(message(lane[a], lane[b], top - 0.9 - step * (k + 1), label,
                         color=MUTED if reply else ACCENT, dashed=reply, size=size))
    g = VGroup(lanes, msgs)
    g.lifelines, g.messages = lanes, msgs
    return g
