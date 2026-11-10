"""Diagrams that explain: pointing labels, streams, entry and exit markers, and the calm style."""
import itertools
import json

import numpy as np
import pytest
from manim import DOWN, LEFT, RIGHT, UP, FadeOut, Square, VGroup

from manimvox.kit import enters, leader, leaders, leaves, node, stream
from manimvox.kit.text import STAGE_BOTTOM, STAGE_TOP
from manimvox.kit.theme import Theme
from tests.test_kit import add_episode, copy_fixture, render_episode, run_py

# ------------------------------------------------------------------ helpers


def _boxes(g):
    return [(m.label.get_left()[0], m.label.get_right()[0], m.label.get_bottom()[1], m.label.get_top()[1]) for m in g]


def _overlap(a, b):
    return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]


def _segments(m):
    pts = m.line.get_anchors()
    return [(pts[i][:2], pts[i + 1][:2]) for i in range(len(pts) - 1)]


def _cross(s, t):
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    a, b = s
    c, d = t
    return orient(a, b, c) * orient(a, b, d) < 0 and orient(c, d, a) * orient(c, d, b) < 0


def _check_layout(g):
    boxes = _boxes(g)
    for a, b in itertools.combinations(boxes, 2):
        assert not _overlap(a, b)
    for x0, x1, y0, y1 in boxes:
        assert -6.6 - 1e-6 <= x0 and x1 <= 6.6 + 1e-6 and STAGE_BOTTOM - 1e-6 <= y0 and y1 <= STAGE_TOP + 1e-6
    for a, b in itertools.combinations(g, 2):
        for s, t in itertools.product(_segments(a), _segments(b)):
            assert not _cross(s, t)


def _items(points):
    return [(np.array([x, y, 0.0]), f"Part number {i}") for i, (x, y) in enumerate(points)]


# ------------------------------------------------------------------ leaders
def test_leaders_spread_and_never_cross():
    g = leaders(_items([(-1, 2), (0.5, 1), (-2, 0), (1, -1), (-0.5, -2.5)]))
    assert len(g) == 5
    _check_layout(g)


def test_leaders_crowded_cluster_stays_inside_the_stage():
    pts = [(-1 + 0.3 * (i % 3), 0.2 + 0.05 * i) for i in range(8)]
    for side in ("right", "left"):
        _check_layout(leaders(_items(pts), side=side))


def test_leaders_at_the_stage_edges():
    _check_layout(leaders(_items([(0, 3.1), (1, 3.0), (-1, 2.9), (2, -3.4), (0, -3.3), (1, -3.2)])))


def test_leaders_both_sides_split_by_mean_x():
    pts = [(-3, 1), (-2.5, 0.8), (-3.2, 0.7), (3, 0.9), (2.5, 1.0), (3.3, 0.6), (0.1, -1)]
    g = leaders(_items(pts), side="both")
    assert len(g) == 7
    _check_layout(g)
    mean = np.mean([p[0] for p in pts])
    for (x, _), m in zip(pts, g):
        assert (m.label.get_center()[0] < 0) == (x < mean)


def test_leaders_keep_the_order_of_items_and_parts_are_reachable():
    g = leaders([(np.array([0, 1, 0.0]), "A", "#ff0000"), (np.array([0, -1, 0.0]), "B")])
    assert g[0].label.get_center()[1] > g[1].label.get_center()[1]
    assert np.allclose(g[0].dot.get_center(), [0, 1, 0])
    assert g[0].grow() is not None and g.grow() is not None
    with pytest.raises(ValueError, match="side"):
        leaders([], side="up")


def test_leader_takes_a_mobject_or_a_point():
    n = node("Server").move_to([-2, 1, 0])
    a = leader(n, "the server")
    assert np.allclose(a.dot.get_center(), n.get_center())
    for p in ((-2, 1), np.array([-2.0, 1.0, 0.0]), (-2, 1, 0)):
        b = leader(p, "the server", side="left")
        assert np.allclose(b.dot.get_center(), [-2, 1, 0])
        assert b.label.get_center()[0] < -2
    assert a.label.get_left()[0] > 0 and a.label.get_right()[0] <= 6.6 + 1e-6
    c = leader(n, "x", x=4.0)
    assert abs(c.label.get_left()[0] - 4.0) < 1e-6


# ------------------------------------------------------------------ streams
def _opacities(s):
    return [d[-1].fill_opacity for d in s.dots]


def test_leaders_below_a_wide_strip_never_overlap_or_cross():
    g = leaders(_items([(-3, 1), (-1.5, 1), (0.2, 1.1), (2.5, 1), (5, 0.9)]), side="below")
    assert len(g) == 5
    _check_layout(g)
    assert all(m.label.get_top()[1] < 0.9 for m in g)  # the row sits under every target
    xs = [m.label.get_center()[0] for m in g]
    assert xs == sorted(xs)  # left to right, the order of the targets


def test_leaders_above_a_row_of_parts():
    g = leaders(_items([(-4, -1), (-1, -1.2), (3, -1)]), side="above")
    _check_layout(g)
    assert all(m.label.get_bottom()[1] > -1 for m in g)


def test_leaders_row_with_targets_close_together_spreads_the_labels():
    g = leaders(_items([(0.0, 1), (0.1, 1), (0.2, 1), (0.3, 1)]), side="below")
    _check_layout(g)
    xs = sorted(m.label.get_center()[0] for m in g)
    assert xs[-1] - xs[0] > 3


def test_leaders_row_at_the_stage_edges_stays_inside():
    g = leaders(_items([(-6.4, 1), (6.4, 1), (0, 1)]), side="below")
    _check_layout(g)


def test_leaders_row_takes_mobjects_and_a_given_row_height():
    a, b = node("A", w=1.5).move_to([-2, 1, 0]), node("B", w=1.5).move_to([2, 1, 0])
    g = leaders([(a, "first"), (b, "second")], side="above", y=2.4)
    _check_layout(g)
    assert abs(g[0].label.get_bottom()[1] - 2.4) < 1e-6


def test_a_label_row_over_the_picture_is_refused():
    with pytest.raises(ValueError, match="row at y"):
        leaders(_items([(-1, 1), (1, 1)]), side="below", y=1.0)
    with pytest.raises(ValueError, match="row at y"):
        leaders(_items([(-1, 1), (1, 1)]), side="above", y=1.0)


def test_too_many_labels_for_one_row_is_refused():
    with pytest.raises(ValueError, match="do not fit"):
        leaders(_items([(i, 0) for i in range(-6, 7)]), side="below")


def test_stream_fades_in_and_out_along_the_path():
    s = stream([(-5, 0, 0), (0, 1, 0), (5, 0, 0)], n=40)
    ops = _opacities(s)
    assert min(ops) < 0.05 and max(ops) == pytest.approx(1.0)
    ends = [d for d, _ in zip(s.dots, ops)]
    for d in ends:
        s_ = d[-1].get_center()
        if abs(s_[0]) > 4.9:
            assert d[-1].fill_opacity < 0.25  # near the start or end of the path
        if abs(s_[0]) < 3:
            assert d[-1].fill_opacity == pytest.approx(1.0)  # the middle


def test_stream_fade_brighten_and_stop():
    s = stream([(-5, 0, 0), (5, 0, 0)])
    full = max(_opacities(s))
    s.level.set_value(0.25)
    s.update(0)
    assert max(_opacities(s)) == pytest.approx(0.25 * full)
    assert s.fade_to(0.3) is not None and s.brighten() is not None
    n = len(s.updaters)
    assert n == 1
    s.update(1.0)
    moved = s.dots[0].get_center().copy()
    s.stop()
    assert not s.updaters
    s.update(1.0)  # updaters are off now: update() runs none
    assert np.allclose(s.dots[0].get_center(), moved)


def test_stream_is_deterministic_and_moves():
    a, b = stream([(-5, 0, 0), (5, 1, 0)]), stream([(-5, 0, 0), (5, 1, 0)])
    for _ in range(5):
        a.update(0.1)
        b.update(0.1)
    assert np.allclose(a.dots.get_center(), b.dots.get_center())
    assert all(np.allclose(x.get_center(), y.get_center()) for x, y in zip(a.dots, b.dots))
    c = stream([(-5, 0, 0), (5, 1, 0)])
    assert not np.allclose(a.dots[0].get_center(), c.dots[0].get_center())


def test_stream_follows_its_handle_when_moved():
    s = stream([(-5, 0, 0), (5, 0, 0)])
    s.shift(UP * 2)
    s.update(0)
    assert all(abs(d.get_center()[1] - 2) < 1e-6 for d in s.dots)


def test_stream_options():
    s = stream([(-1, 0, 0), (1, 0, 0)], glow=False, trail=False, n=5)
    assert s.trail is None and len(s.dots) == 5 and len(s.dots[0]) == 1


# ------------------------------------------------------------------ markers
def test_enters_ends_at_the_point_and_leaves_starts_there():
    p = np.array([1.0, 2.0, 0.0])
    e = enters(p, direction=RIGHT, text="request", length=1.5)
    assert np.allclose(e.arrow[0][1].get_end(), p, atol=0.05)  # the arrowhead is at the point
    assert e.arrow.get_left()[0] == pytest.approx(p[0] - 1.5, abs=0.05)
    assert e.arrow.get_right()[0] == pytest.approx(p[0], abs=0.1)
    assert e.label.get_right()[0] < e.arrow.get_left()[0]
    lv = leaves(p, direction=DOWN, text="out", length=1.0)
    assert lv.arrow.get_top()[1] == pytest.approx(p[1], abs=0.1)
    assert lv.arrow.get_bottom()[1] == pytest.approx(p[1] - 1.0, abs=0.1)
    assert lv.label.get_top()[1] < lv.arrow.get_bottom()[1]
    up = leaves(p, direction=UP)
    assert up.label is None and up.arrow.get_bottom()[1] == pytest.approx(p[1], abs=0.1)
    assert leaves(p, direction=LEFT, text="x").label.get_right()[0] < p[0] - 1.0


# ------------------------------------------------------------------ calm style
def test_style_is_validated_and_defaults_to_standard():
    assert Theme.from_dict({}).style == "standard"
    assert Theme.from_dict({"style": "calm"}).style == "calm"
    with pytest.raises(ValueError, match="theme.style"):
        Theme.from_dict({"style": "loud"})
    assert Theme.from_dict({}).stroke_scale == 1.0 and Theme.from_dict({"style": "calm"}).stroke_scale < 1.0


def test_load_project_rejects_an_unknown_style(tmp_path):
    from manimvox.project import ProjectError, load_project

    p = copy_fixture(tmp_path)
    data = json.loads((p / "series.json").read_text(encoding="utf-8"))
    data["theme"]["style"] = "loud"
    (p / "series.json").write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ProjectError, match="theme.style"):
        load_project(p)


WIDTHS = ("from manimvox.kit import *\n"
          "n=node('a','b'); b=box(2,1); a=arrow(LEFT,RIGHT); c=card('t','body')\n"
          "print(n.bg.stroke_width, b.stroke_width, a[0].stroke_width, c.bg.height, n.bg.get_stroke_opacity())")


def test_calm_draws_thinner_strokes_and_standard_is_unchanged(tmp_path):
    p = copy_fixture(tmp_path)
    r = run_py(WIDTHS, p)
    assert r.returncode == 0, r.stderr
    std = [float(v) for v in r.stdout.split()]
    assert std[:3] == [2.4, 2, 3.0] and std[4] == 1.0
    data = json.loads((p / "series.json").read_text(encoding="utf-8"))
    data["theme"]["style"] = "calm"
    (p / "series.json").write_text(json.dumps(data), encoding="utf-8")
    r = run_py(WIDTHS, p)
    assert r.returncode == 0, r.stderr
    calm = [float(v) for v in r.stdout.split()]
    assert all(c < s for c, s in zip(calm[:3], std[:3])) and calm[3] > std[3] and calm[4] < 1.0


# ------------------------------------------------------------------ slow: a render
EPISODE = '''from manimvox.kit import *


class Ep02(Episode):
    EP = 2
    TITLE = "Pointing"
    TAGLINE = "Labels, flow, markers"
    NCHAP = 1

    def build(self):
        self.intro("A short intro.")
        self.chapter("Diagram", "A request goes through two services.")
        a = node("API", w=2).move_to(LEFT * 3)
        b = node("DB", w=2).move_to(RIGHT * 1)
        flow_ = stream([a.get_right(), b.get_left()], n=12)
        self.say("Two services.", FadeIn(a), FadeIn(b), FadeIn(enters(a.get_left(), RIGHT, "request")))
        labels = leaders([(a, "front door"), (b, "storage")])
        self.say("Each has a name.", labels.grow())
        self.add(flow_)
        self.say("A request flows.", flow_.fade_to(0.3))
        out = leaves(b.get_right(), RIGHT, "reply")
        self.say("Then the reply leaves.", FadeIn(out), flow_.brighten())
        flow_.stop()
        self.clear()
        self.outro([], "Done.")
'''


@pytest.mark.slow
def test_an_episode_with_leaders_a_stream_and_markers_renders(tmp_path):
    p = copy_fixture(tmp_path)
    add_episode(p, "ep02_pointing", "Ep02", "Pointing", EPISODE)
    layout = render_episode(p, "ep02_pointing", "Ep02", voiced=False)
    shown = {t["text"] for fr in layout["frames"] for t in fr["texts"]}
    assert {"front door", "storage", "request", "reply"} <= shown


def test_labels_start_past_the_target_not_against_the_stage_edge():
    """By default the column sits just past the outermost target's edge, never over a box it points at, and is
    pulled in at the stage edge."""
    boxes = [node(f"Part {i}").move_to([-3, 1.5 - i, 0]) for i in range(3)]
    g = leaders([(b, f"label {i}") for i, b in enumerate(boxes)])
    for b, m in zip(boxes, g):
        assert m.label.get_left()[0] > b.get_right()[0]
        assert m.label.get_left()[0] < b.get_right()[0] + 1.5
    left = leaders([(b, "x") for b in boxes], side="left")
    assert all(m.label.get_right()[0] < b.get_left()[0] for b, m in zip(boxes, left))
    near = leader(node("Near").move_to([1.5, 0, 0]), "a label near the edge")
    assert near.label.get_right()[0] <= 6.6 + 1e-6


def test_a_label_column_over_the_picture_is_refused():
    """A column that would sit over its targets makes the lines double back through the picture: refused."""
    with pytest.raises(ValueError, match="over the picture"):
        leader(node("Far").move_to([5.5, 0, 0]), "a long label at the edge")
    with pytest.raises(ValueError, match="over the picture"):
        leaders([((0, 0, 0), "a"), ((2, 1, 0), "b")], x=1.0)
    with pytest.raises(ValueError, match="over the picture"):
        leaders([((0, 0, 0), "a")], side="left", x=-0.2)


def test_bold_labels():
    a, b = leader((0, 0, 0), "name"), leader((0, 0, 0), "name", weight="BOLD")
    assert b.label.width > a.label.width
    assert leaders([((0, 0, 0), "name")], weight="BOLD")[0].label.width == pytest.approx(b.label.width)


def test_a_stream_fades_out_inside_a_group():
    """A fade runs the updaters of its own copies of the mobject; the stream's copies must not restore the dots."""
    s = stream([(-5, 0, 0), (5, 0, 0)])
    a = FadeOut(VGroup(Square(), s))
    a.begin()
    for k in range(1, 10):
        a.update_mobjects(0.05)
        a.interpolate(k / 10)
    assert max(d[-1].get_fill_opacity() for d in s.dots) < 0.2
    moving = stream([(-5, 0, 0), (5, 0, 0)])
    before = moving.dots[0].get_center().copy()
    moving.update(0.5)
    assert not np.allclose(moving.dots[0].get_center(), before)  # the stream itself still moves
