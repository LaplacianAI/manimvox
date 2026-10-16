"""Small icons drawn from primitives, in theme colours."""
from __future__ import annotations

from manim import BOLD, DOWN, LEFT, PI, RIGHT, UL, UP, UR, Arc, Circle, Dot, Ellipse, Line, Polygon, Rectangle, VGroup

from .colours import ACCENT, BG, BLUE, PANEL2, TEAL, WARN
from .components import box
from .text import T


def icon_shop(color=ACCENT, s=1.0):
    body = box(1.5, 1.0, fill=PANEL2, stroke=color, r=0.06, sw=2.5)
    awn = Polygon([-0.9, 0.5, 0], [0.9, 0.5, 0], [0.75, 0.9, 0], [-0.75, 0.9, 0]).set_fill(color, 0.9).set_stroke(color, 2)
    door = box(0.34, 0.6, fill=BG, stroke=color, r=0.03, sw=2).move_to([0.35, -0.2, 0])
    win = box(0.5, 0.34, fill=BG, stroke=color, r=0.03, sw=2).move_to([-0.35, -0.05, 0])
    return VGroup(body, awn, door, win).scale(s)


def icon_doc(color=BLUE, s=1.0, lines=4):
    pg = box(0.95, 1.25, fill=PANEL2, stroke=color, r=0.07, sw=2.5)
    ls = VGroup(*[Line(LEFT * 0.28, RIGHT * (0.28 if i % 2 == 0 else 0.1)).set_stroke(color, 2.5, 0.8) for i in range(lines)])
    ls.arrange(DOWN, buff=0.16, aligned_edge=LEFT).move_to(pg)
    return VGroup(pg, ls).scale(s)


def icon_box(color=WARN, s=1.0):
    b = box(1.1, 0.95, fill=PANEL2, stroke=color, r=0.05, sw=2.5)
    tape = Line(b.get_top(), b.get_bottom()).set_stroke(color, 2.5, 0.7)
    flap = Line(b.get_corner(UL) + DOWN * 0.3, b.get_corner(UR) + DOWN * 0.3).set_stroke(color, 2, 0.7)
    return VGroup(b, tape, flap).scale(s)


def icon_db(color=TEAL, s=1.0):
    top = Ellipse(width=1.1, height=0.36).set_stroke(color, 2.5).set_fill(PANEL2, 1)
    side = Rectangle(width=1.1, height=0.9).set_stroke(color, 0).set_fill(PANEL2, 1).next_to(top, DOWN, buff=-0.18)
    l1 = Line(top.get_left(), top.get_left() + DOWN * 0.9).set_stroke(color, 2.5)
    l2 = Line(top.get_right(), top.get_right() + DOWN * 0.9).set_stroke(color, 2.5)
    bot = Arc(radius=0.55, start_angle=PI, angle=PI).stretch_to_fit_height(0.18).set_stroke(color, 2.5)
    bot.move_to(top.get_center() + DOWN * 0.99)
    mid = bot.copy().shift(UP * 0.45).set_stroke(color, 2, 0.6)
    return VGroup(side, l1, l2, bot, mid, top).scale(s)


def icon_person(color=BLUE, s=1.0):
    head = Circle(radius=0.24).set_stroke(color, 2.5).set_fill(PANEL2, 1)
    body = Arc(radius=0.46, start_angle=0, angle=PI).set_stroke(color, 2.5).set_fill(PANEL2, 1)
    body.next_to(head, DOWN, buff=0.08)
    base = Line(body.get_left() + DOWN * 0.23, body.get_right() + DOWN * 0.23).set_stroke(color, 2.5)
    return VGroup(body, base, head).scale(s)


def icon_bot(color=ACCENT, s=1.0):
    face = box(1.0, 0.8, fill=PANEL2, stroke=color, r=0.18, sw=2.5)
    eyes = VGroup(Dot(radius=0.08, color=color), Dot(radius=0.08, color=color)).arrange(RIGHT, buff=0.3).move_to(face).shift(UP * 0.06)
    mouth = Line(LEFT * 0.16, RIGHT * 0.16).set_stroke(color, 2.5).move_to(face).shift(DOWN * 0.2)
    ant = Line(face.get_top(), face.get_top() + UP * 0.22).set_stroke(color, 2.5)
    tip = Dot(radius=0.06, color=color).move_to(ant.get_end())
    return VGroup(face, eyes, mouth, ant, tip).scale(s)


def icon_phone(color=BLUE, s=1.0):
    b = box(0.7, 1.25, fill=PANEL2, stroke=color, r=0.12, sw=2.5)
    scr = box(0.52, 0.85, fill=BG, stroke=color, r=0.04, sw=1.5).move_to(b).shift(UP * 0.06)
    btn = Dot(radius=0.04, color=color).move_to(b.get_bottom() + UP * 0.12)
    return VGroup(b, scr, btn).scale(s)


def icon_till(color=ACCENT, s=1.0):
    base = box(1.3, 0.5, fill=PANEL2, stroke=color, r=0.06, sw=2.5)
    scr = box(0.8, 0.55, fill=BG, stroke=color, r=0.05, sw=2.5).next_to(base, UP, buff=0.06).shift(LEFT * 0.15)
    keys = VGroup(*[Dot(radius=0.035, color=color) for _ in range(8)]).arrange_in_grid(2, 4, buff=0.1).move_to(base)
    return VGroup(base, scr, keys).scale(s)


def icon_coin(color=WARN, s=1.0, label="$"):
    c = Circle(radius=0.42).set_stroke(color, 2.5).set_fill(PANEL2, 1)
    return VGroup(c, T(label, 14, color, BOLD).move_to(c)).scale(s)


def icon_cloud(color=BLUE, s=1.0):
    parts = VGroup(Circle(radius=0.3).shift(LEFT * 0.32), Circle(radius=0.4).shift(UP * 0.12),
                   Circle(radius=0.3).shift(RIGHT * 0.36), box(0.9, 0.34, r=0.1).shift(DOWN * 0.14))
    for p in parts:
        p.set_fill(PANEL2, 1).set_stroke(color, 2.5)
    return parts.scale(s)
