import json
import math
from functools import partial
from pathlib import Path

import pyvista as pv

from manimvox.kit import *
from manimvox.scenes import Cutaway, SceneError

HERE = Path(__file__).resolve().parents[1]
ASSET = json.loads((HERE / "research/assets.json").read_text())["assets"][0]
CREDIT = f"{ASSET['credit']} ({ASSET['licence']})"

# The 3D part is mounted the way it sits in the wheel: its axle (x) runs left to right, up is up, so the weight points
# down and a sideways push runs along the axle. One camera serves every clip: from the front, a little above and to
# the side. The wedge opens towards the front so that a cut face runs through a roller at the bottom of the ring,
# where the weight is carried (rollers stand 360/14 degrees apart: the ninth is 231.4 degrees round).
ROLLER_ANGLE = 360 / 14 * 9
OPENS = math.radians(ROLLER_ANGLE - 45)
CAM = {"turn": 30, "lift": 0.6, "zoom": 1.2}
STEEL = {1: "#9AA3AE", 2: "#7D8793", 3: "#8A939E", 0: "#B8BFC8"}  # inner ring, outer ring, cage, rollers
FACES = {1: "#B9C2CD", 2: "#69737F", 3: "#98A2AE", 0: "#E6EAEE"}  # the cut faces tell the parts apart
WIDTH, CENTRE = 14.2, DOWN * 0.05
WHEEL_C, WHEEL_R = np.array([0.0, -1.0, 0.0]), 2.2
UPWARD, AXLE = np.array([0.0, 0.0, 1.0]), np.array([1.0, 0.0, 0.0])
SHADE = "#5E6773"  # a roller in the drawing, when it is not the thing being named
SAY_PAD = 0.35  # the kit's 0.7 s after each line is long for a one-minute video


def label_parts(mesh):
    """Name the separate bodies of the model by where they sit: rings by radius, the cage as the big one left
    over, the rest are the rollers (0)."""
    parts = mesh.connectivity("all")
    ids = np.asarray(parts.cell_data["RegionId"])
    sizes = np.bincount(ids)
    radius = {i: np.hypot(*parts.extract_cells(np.where(ids == i)[0]).points[:, 1:].T) for i in range(len(sizes))}
    inner = min(radius, key=lambda i: radius[i].min())
    outer = max(radius, key=lambda i: radius[i].max())
    cage = max((i for i in radius if i not in (inner, outer)), key=lambda i: sizes[i])
    kind = {inner: 1, outer: 2, cage: 3}
    parts.cell_data["part"] = np.array([kind.get(i, 0) for i in ids], dtype=np.int32)
    return parts


bearing = Cutaway(label_parts(pv.read(str(HERE / ASSET["file"]))), regions="part", colours=STEEL, section_colours=FACES,
                  glass_regions=[2], axis="x", towards=(0, math.cos(OPENS), math.sin(OPENS)), up=tuple(UPWARD))


def hot(region, see_through=False):
    """Steel for every part, the accent on the one the voice is naming. `see_through` draws the outer ring as glass."""
    accent = str(ACCENT)
    bearing.colour({**STEEL, region: accent} if region is not None else dict(STEEL),
                   {**FACES, region: accent} if region is not None else dict(FACES), ghost={2: 0.22} if see_through else {})
    return bearing


def roller_face():
    """The cut face that holds a roller (the other face cuts between two rollers) and a point in that roller."""
    for f in (0, 1):
        try:
            return f, bearing.region_centre(0, face=f)
        except SceneError:  # this face has no roller on it
            continue
    raise RuntimeError("no roller on either cut face")


def build_wheel(ring_colour=MUTED):
    """A wheel from the front on its fixed axle: tyre, rim and spokes turn; the axle does not. The bearing is the
    ring between them."""
    c = WHEEL_C
    tyre = Annulus(inner_radius=WHEEL_R * 0.82, outer_radius=WHEEL_R, fill_color=LINE, fill_opacity=1, stroke_width=0)
    rim = Circle(radius=WHEEL_R * 0.82, stroke_color=MUTED, stroke_width=4)
    spokes = VGroup(*[Line(ORIGIN, RIGHT * WHEEL_R * 0.82).rotate(k * TAU / 5, about_point=ORIGIN) for k in range(5)])
    spokes.set_stroke(MUTED, 6)
    tread = VGroup(*[Line(RIGHT * WHEEL_R * 0.93, RIGHT * WHEEL_R * 1.0).rotate(k * TAU / 16, about_point=ORIGIN)
                     for k in range(16)]).set_stroke(MUTED, 3)
    hub = Circle(radius=WHEEL_R * 0.34, stroke_width=0).set_fill(PANEL2, 1)
    turning = VGroup(tyre, tread, rim, spokes, hub).move_to(c)
    ring = Annulus(inner_radius=WHEEL_R * 0.17, outer_radius=WHEEL_R * 0.3, fill_color=ring_colour, fill_opacity=1,
                   stroke_width=0).move_to(c)
    axle = Circle(radius=WHEEL_R * 0.17, stroke_width=0).set_fill("#9AA3AE", 1).move_to(c)
    ground = Line([-3.2, c[1] - WHEEL_R, 0], [3.2, c[1] - WHEEL_R, 0]).set_stroke(LINE, 4)
    return turning, ring, axle, ground


def fat_arrow(a, b, colour, width=8):
    """A thick arrow from a to b (the kit's `arrow` is thin, and these carry the point of the picture)."""
    return Arrow(a, b, buff=0, color=colour, stroke_width=width, max_tip_length_to_length_ratio=0.35,
                 max_stroke_width_to_length_ratio=40)


def spin(m, dt):
    m.rotate(dt * 2.2, about_point=m.get_center())


class Ep01(Episode):
    EP = 1
    TITLE = "What lets a loaded wheel turn so freely?"
    TAGLINE = "Inside a tapered roller bearing"
    NCHAP = 3
    CHROME = ()

    def build(self):
        say, steps = partial(self.say, pad=SAY_PAD), partial(self.steps, pad=SAY_PAD)

        # ---- cold open: a loaded wheel turning on its axle -------------------------------------
        turning, ring, axle, ground = build_wheel()
        weight = fat_arrow(WHEEL_C + UP * 0.3, WHEEL_C + DOWN * (WHEEL_R - 0.05), ACCENT)
        weight_label = leader(weight.get_end(), "the car's weight", color=ACCENT, size=28, x=WHEEL_R + 0.5)
        self.add(ground, turning, ring, axle, weight)
        turning.add_updater(spin)
        say("A car wheel carries the whole car, and still it spins freely.", weight_label.grow())
        edge = WHEEL_C + np.array([math.cos(0.8), math.sin(0.8), 0]) * WHEEL_R * 0.92
        names = leaders([(axle, "the axle stays still"), (edge, "the wheel turns")], side="both", size=28)
        self.intro("What lets a loaded wheel turn so freely?",
                   question="What lets a loaded wheel turn so freely?", card=False)
        say("Between the axle and the wheel sits a bearing.", ring.animate.set_color(ACCENT),
            weight.animate.set_color(MUTED), FadeOut(weight_label), names.grow(lag=0.6))
        turning.clear_updaters()

        # ---- chapter 1: inside the hub ------------------------------------------------------------
        face, P = roller_face()
        near = {**CAM, "aim": bearing.centre + (P - bearing.centre) * 0.4, "zoom": 1.4}  # the same camera, eased down toward the bottom roller: the whole ring stays in frame
        spin_clip = hot(None).turning(5, **CAM, width=WIDTH)
        cut = hot(None).sweep(2.0, **CAM, width=WIDTH)
        push = hot(None).move(1.6, CAM, near, glass=0.0, width=WIDTH)
        shots = {r: hot(r, see_through=r == 0).opened(0.0, **near, width=WIDTH) for r in (1, 2, 0)}
        for i, clip in enumerate([spin_clip, cut, push, *shots.values()]):
            clip.move_to(CENTRE).set_z_index(-20 + i)
        credit = T(CREDIT, 13, MUTED, max_w=12.9).move_to([0, STAGE_BOTTOM + 0.1, 0])

        self.chapter("Inside the hub", "Here it is, taken out.", transition=zoom_through(ring), card=False, number=False)
        self.add(spin_clip)
        self.play(FadeIn(spin_clip), FadeIn(credit), run_time=0.5)
        with self.narrate("Two steel rings, with something between them.", pad=SAY_PAD) as dur:
            self.play(spin_clip.play(), run_time=max(dur, 3.0))
        self.remove(spin_clip)
        self.add(cut)
        with self.narrate("Cut a quarter away, and look in.", pad=SAY_PAD):
            self.play(cut.play())
            self.remove(cut)
            self.add(push)
            self.play(push.play())
        self.remove(push)
        self.add(shots[1])
        # one dot on each part, on the cut face, the names split left and right of the ring
        pick = {"inner ring": bearing.region_centre(1, face=face), "rollers": bearing.region_centre(0, face=face),
                "outer ring": bearing.region_centre(2, face=face)}
        marks = leaders(bearing.labelled(shots[1], pick), side="both", size=28, weight=BOLD)
        steps("An inner ring, on the axle. An outer ring, in the wheel. Between them, rollers.",
              [[marks[0].grow()], [FadeIn(shots[2]), marks[2].grow()], [FadeIn(shots[0]), marks[1].grow()]])
        self.remove(shots[1], shots[2])

        # ---- chapter 2: the load ------------------------------------------------------------------------
        self.chapter("The load", "Now the weight.", keep=(shots[0], credit), card=False, number=False)
        push = shots[0]  # the same view, rollers still lit: the weight is drawn over them
        # the weight runs straight down through the inner ring, the roller and the outer ring; the push along the axle
        wt = fat_arrow(bearing.at(push, P + UPWARD * 7.5), bearing.at(push, P - UPWARD * 4.5), ACCENT)
        wt_label = T("the weight", 30, ACCENT, BOLD).next_to(wt.get_start(), RIGHT, buff=0.4)
        with self.narrate("The weight pushes down through the axle. The rollers pass it on, and roll, so nothing drags.",
                          pad=SAY_PAD) as dur:
            self.play(Create(wt), FadeIn(wt_label), run_time=0.7)
            self.wait(max(0.1, dur - 0.7))
        sw = fat_arrow(bearing.at(push, P - AXLE * 13 + UPWARD * 3.5), bearing.at(push, P - AXLE * 6.8 + UPWARD * 3.5), ACCENT)
        sw_label = T("sideways push", 30, ACCENT, BOLD).next_to(sw.get_start(), UP, buff=0.15)
        say("A turn pushes sideways too.", wt.animate.set_color(MUTED), wt_label.animate.set_color(MUTED),
            Create(sw), FadeIn(sw_label))

        # ---- chapter 3: why tapered (a simplified drawing) -----------------------------------------------
        self.chapter("Why tapered", "Why are the rollers tapered?", transition="blur", card=False, number=False)
        ax_y, ax_x = -2.4, -6.0
        A1, A2, A3 = 8, 16, 24  # the inner ring's line, the roller's own line, the outer ring's line (exaggerated)

        def y(deg, x):
            return ax_y + math.tan(math.radians(deg)) * (x - ax_x)

        x1, x2 = -2.2, 1.2
        steel = "#7D8793"

        def band(deg, sign):  # a ring on one side of its raceway line: a strip 0.55 thick beyond it
            a, b = x1 - 0.5, x2 + 0.5
            pts = [[a, y(deg, a), 0], [b, y(deg, b), 0], [b, y(deg, b) + sign * 0.55, 0], [a, y(deg, a) + sign * 0.55, 0]]
            return Polygon(*pts).set_fill(steel, 1).set_stroke("#9AA3AE", 2)

        def rib(x, deg_from, deg_to):  # a lip on the ring that keeps the roller from sliding out
            return Polygon([x - 0.12, y(deg_from, x), 0], [x + 0.12, y(deg_from, x), 0], [x + 0.12, y(deg_to, x), 0],
                           [x - 0.12, y(deg_to, x), 0]).set_fill(steel, 1).set_stroke("#9AA3AE", 2)

        roller = Polygon([x1, y(A1, x1), 0], [x2, y(A1, x2), 0], [x2, y(A3, x2), 0], [x1, y(A3, x1), 0])
        roller.set_fill(SHADE, 1).set_stroke("#B8BFC8", 2)
        pieces = VGroup(band(A1, -1), band(A3, 1), rib(x2 + 0.3, A1, A2 + 2), roller)
        inner_tag = T("inner ring", 26, MUTED).move_to([x1 + 0.7, ax_y - 0.4, 0])
        outer_tag = T("outer ring", 26, MUTED).move_to([x1 + 1.0, y(A3, x1 + 1.0) + 1.0, 0])
        roller_tag = T("roller", 26, INK, BOLD).move_to([x1 + 0.9, y(A2, x1 + 0.9) + 0.0, 0])
        axis_line = DashedLine([-6.3, ax_y, 0], [6.3, ax_y, 0], color=MUTED, stroke_width=2)
        axle_tag = T("the axle's line", 26, MUTED).move_to([-4.9, ax_y - 0.4, 0])
        simple = note("simplified drawing, not to scale", size=20)
        self.play(FadeIn(pieces, shift=UP * 0.1), Create(axis_line), FadeIn(axle_tag), FadeIn(simple),
                  FadeIn(inner_tag), FadeIn(outer_tag), FadeIn(roller_tag), run_time=0.8)
        # the ring pushes at right angles to the slanted face; that push is a part down and a part along
        xc = -0.3
        pc = np.array([xc, y(A3, xc), 0])
        k, a3 = 2.0, math.radians(A3)
        push_ = fat_arrow(pc, pc + np.array([math.sin(a3), -math.cos(a3), 0]) * 1.2, ACCENT, 7)
        origin = np.array([4.2, 1.3, 0])
        mid = origin + DOWN * (k * math.cos(a3))
        head = mid + RIGHT * (k * math.sin(a3))
        res = fat_arrow(origin, head, ACCENT, 7)
        down = fat_arrow(origin, mid, INK, 5)
        side = fat_arrow(mid, head, INK, 5)
        t_res = T("the ring's push", 24, ACCENT, BOLD).next_to(origin, UP, buff=0.2).shift(LEFT * 0.2)
        t_down = T("weight", 26, INK, BOLD).next_to(down, LEFT, buff=0.2)
        t_side = T("sideways", 26, INK, BOLD).next_to(side, DOWN, buff=0.25)
        with self.narrate("Each roller is a slice of a cone, set at a slant, so it takes the weight and the sideways push.",
                          pad=SAY_PAD) as dur:
            self.play(roller.animate.set_fill(ACCENT, 1), FadeOut(roller_tag), Create(push_), run_time=0.8)
            self.play(Create(res), FadeIn(t_res), run_time=0.6)
            self.play(Create(down), Create(side), FadeIn(t_down), FadeIn(t_side), run_time=0.9)
            self.wait(max(0.1, dur - 2.3))
        lines = [DashedLine([x1, y(a, x1), 0], [ax_x, y(a, ax_x), 0], color=ACCENT, stroke_width=3) for a in (A1, A2, A3)]
        dot = Dot([ax_x, ax_y, 0], radius=0.12, color=ACCENT)
        one = T("one point", 28, ACCENT, BOLD).next_to(dot, UP, buff=0.35).shift(RIGHT * 0.5)
        steps("Extend the lines, and they meet at one point on the axle. So they roll, not slide.",
              [[roller.animate.set_fill(SHADE, 1), push_.animate.set_color(MUTED), res.animate.set_color(MUTED),
                t_res.animate.set_color(MUTED), down.animate.set_color(MUTED), side.animate.set_color(MUTED),
                t_down.animate.set_color(MUTED), t_side.animate.set_color(MUTED)],
               [Create(l) for l in lines], [FadeIn(dot, scale=2), FadeIn(one)]])

        # ---- ending: back to the wheel, the answer above it ------------------------------------------------
        self.clear()
        turning, ring, axle, ground = build_wheel(ring_colour=ACCENT)
        picture = VGroup(ground, turning, ring, axle)
        picture.scale(1.0).move_to([0, -1.25, 0])
        picture.shift(LEFT * turning.get_center()[0])
        bearing_label = leader(ring, "the bearing", color=ACCENT, size=26, x=WHEEL_R + 0.4)
        turning.add_updater(spin)
        self.add(picture, bearing_label)
        self.outro([], "That is the trick.",
                   answer="Slanted rollers carry the weight and the sideways push, and roll instead of sliding.",
                   keep=[picture, bearing_label])
