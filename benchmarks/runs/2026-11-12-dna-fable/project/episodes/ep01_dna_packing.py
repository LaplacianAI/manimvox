"""How DNA packs into a chromosome: one thread followed through each level of packing, in 3D.

Script: episodes/ep01_dna_packing.md. Facts: FACTS.md. The shapes are schematic diagrams, not molecular models.
Objects stand along the screen's y axis and turn about their own axes, so the flat camera the kit returns to
at every seam still shows them from the front; the camera itself tilts over the finished chromosome."""
from manimvox.kit import *
from manimvox.kit.shading import Lighting

# A stroke piece carrying a Lighting is depth-sorted by the kit's camera but keeps its own colour
# (Manim's shading of a near-straight stroke has no stable normal and would flicker).
KEEP_COLOUR = Lighting()


def piece(points, color, width, opacity=1.0):
    m = VMobject().set_points_as_corners([np.array(p, float) for p in points])
    m.set_stroke(color, width, opacity).set_cap_style(CapStyleType.ROUND)
    m.set_shade_in_3d(True)
    m.lighting = KEEP_COLOUR
    return m


def thread(points, color, width, step=2):
    """A 3D polyline as short pieces, so the camera can sort each by depth."""
    return VGroup(*[piece(points[i:i + step + 1], color, width) for i in range(0, len(points) - step, step)])


def hermite(p0, m0, p1, m1, n=14):
    out = []
    for s in np.linspace(0, 1, n):
        h00, h10 = 2 * s**3 - 3 * s**2 + 1, s**3 - 2 * s**2 + s
        h01, h11 = -2 * s**3 + 3 * s**2, s**3 - s**2
        out.append(h00 * p0 + h10 * m0 + h01 * p1 + h11 * m1)
    return out


def helix(length=12.6, radius=0.62, turns=4.5, per_turn=9):
    """The double helix along x: two strands and the rungs between them."""
    w = TAU * turns / length
    xs = np.linspace(-length / 2, length / 2, 161)

    def at(x, phase):
        return np.array([x, radius * np.cos(w * x + phase), radius * np.sin(w * x + phase)])

    second = 0.8 * PI  # not opposite: leaves a wide and a narrow groove
    rungs = VGroup(*[piece([at(x, 0), at(x, second)], MUTED, 3.5, 0.85)
                     for x in np.linspace(-length / 2 + 0.15, length / 2 - 0.15, int(turns * per_turn))])
    return VGroup(rungs, thread([at(x, 0) for x in xs], DNA, 9), thread([at(x, second) for x in xs], DNA_TWO, 9))


TURNS = 1.67
THETA0 = -30.5 * DEGREES  # the thread arrives and leaves on the same side, crossing behind the spool


def wrap(centre, R, h, n=44):
    """Points of the thread going TURNS times round a spool at `centre` (axis up), with its end tangents."""
    pts = []
    for t in np.linspace(0, 1, n):
        a = THETA0 + TURNS * TAU * t
        pts.append(centre + np.array([R * np.cos(a), -h + 2 * h * t, R * np.sin(a)]))
    a0, a1 = THETA0, THETA0 + TURNS * TAU
    return pts, np.array([-np.sin(a0), 0, np.cos(a0)]), np.array([-np.sin(a1), 0, np.cos(a1)])


def strung(centres, R, h, start, end, pull):
    """One thread from `start` to `end`, wrapped round a spool at each centre."""
    pts, here, going = [], np.array(start, float), RIGHT * pull
    for c in centres:
        w, t_in, t_out = wrap(np.array(c, float), R, h)
        pts += hermite(here, going, w[0], t_in * pull)[:-1] + w[:-1]
        here, going = w[-1], t_out * pull
    return pts + hermite(here, going, np.array(end, float), RIGHT * pull)


def ball(centre, radius, color, res):
    return Sphere(center=centre, radius=radius, resolution=res, checkerboard_colors=False,
                  fill_color=color, fill_opacity=1, stroke_color=color, stroke_width=0.5)


def nucleosome():
    """Eight histone spheres in two layers of four, and the thread wrapped 1.67 times round them."""
    core = VGroup()
    for layer, y in enumerate((-0.37, 0.37)):
        for k in range(4):
            a = k * TAU / 4 + layer * TAU / 8
            core.add(ball([0.52 * np.cos(a), y, 0.52 * np.sin(a)], 0.54, HISTONE, (12, 8)))
    dna = thread(strung([ORIGIN], 1.26, 0.56, [-3.6, -0.56, 0], [3.6, 0.56, 0], 2.4), DNA, 10)
    return core, dna


def beads(n=7, gap=1.78):
    """Beads on a string: n small spools on one thread."""
    centres = [np.array([(i - (n - 1) / 2) * gap, 0, 0]) for i in range(n)]
    spools = VGroup(*[ball(c, 0.4, HISTONE, (10, 6)) for c in centres])
    half = (n - 1) / 2 * gap + 0.95
    dna = thread(strung(centres, 0.5, 0.17, [-half, 0, 0], [half, 0, 0], 0.9), DNA, 6)
    return VGroup(spools, dna)


def loop_array(n=34, height=5.2, reach=1.75):
    """Loops of the string standing out all round a central scaffold."""
    loops, bases = VGroup(), []
    for i in range(n):
        y = -height / 2 + height * (i + 0.5) / n
        a = i * 2.39996  # the golden angle spreads the loops evenly round the axis
        out = np.array([np.cos(a), 0, np.sin(a)])
        side = np.cross(UP, out)
        far = reach * (0.82 + 0.18 * np.sin(i * 1.7))
        base = UP * y
        pts = [base + out * far * np.sin(PI * s) + (side * 0.3 + UP * 0.12) * far * np.sin(TAU * s) for s in np.linspace(0, 1, 13)]
        m = VMobject().set_points_smoothly(pts).set_stroke(DNA if i % 2 else DNA_TWO, 6)
        m.set_shade_in_3d(True)
        m.lighting = KEEP_COLOUR
        loops.add(m)
        bases.append(base)
    ys = np.linspace(-height / 2 - 0.1, height / 2 + 0.1, 41)
    scaffold = thread([UP * y for y in ys], CONDENSIN, 13)
    return loops, scaffold, bases


def chromatid(sign):
    def middle(u):
        y = 1.5 * u if u > 0 else 2.3 * u
        return np.array([sign * (0.2 + 0.55 * (y / 2) ** 2), y, 0]), y

    def surface(u, v):
        c, y = middle(u)
        r = 0.4 * (1 - 0.5 * np.exp(-(y / 0.3) ** 2)) * max(np.sqrt(max(1 - abs(u) ** 8, 0)), 0.1)  # never zero: a closed tip makes degenerate faces
        return c + r * (np.cos(v) * RIGHT + np.sin(v) * OUT)

    return Surface(surface, u_range=[-1, 1], v_range=[0, TAU], resolution=(30, 12), checkerboard_colors=False,
                   fill_color=CHROMATID, fill_opacity=1, stroke_color=CHROMATID, stroke_width=0.5)


def chromosome():
    return VGroup(chromatid(-1), chromatid(1))


def spin(mob, axis, rate):
    """Turn `mob` about `axis` through its pivot, `rate` radians a second, until clear_updaters()."""
    mob.pivot = mob.get_center()
    mob.add_updater(lambda m, dt: m.rotate(rate * dt, axis=axis, about_point=m.pivot))


def figure(value, label, color, size=60):
    return VGroup(T(value, size, color, BOLD), T(label, 20, MUTED)).arrange(DOWN, buff=0.16)


class Ep01(Episode3D):
    EP = 1
    TITLE = "How DNA packs into a chromosome"
    TAGLINE = "Two metres of thread, wound and looped"
    NCHAP = 2

    def left(self, t0, dur, least=0.4):
        return max(least, dur - (self.time - t0))

    def build(self):
        # Cold open: the helix, already turning, and the two numbers that do not fit together.
        hx = helix().move_to([0, 0.0, 0])
        self.add(hx)
        spin(hx, RIGHT, 0.5)
        two = figure("2 m", "of DNA in every human cell", ACCENT).move_to([-3.3, -2.25, 0])
        six = figure("6 µm", "the width of the cell's nucleus", INK).move_to([3.3, -2.25, 0])
        self.pin(two, six)
        self.steps("Each of your cells holds about two metres of DNA, in a nucleus six thousandths of a millimetre wide.",
                   [FadeIn(two, shift=UP * 0.2), FadeIn(six, shift=UP * 0.2)], run_time=0.9)
        self.beat()
        self.intro("So how does two metres of DNA pack into tiny chromosomes? Wind it, then loop it.",
                   question="How does two metres of DNA pack into tiny chromosomes?", card=False, leave=[two, six])

        # 1 · Wind it: the helix round a spool of eight histones, then spool after spool.
        self.chapter("Wind it", "First, wind it.", card=False, keep=(hx,), transition="blur")
        hx.clear_updaters()
        tilt = rotate_vector(rotate_vector(UP, 28 * DEGREES, RIGHT), -10 * DEGREES, OUT)
        core, dna = nucleosome()
        unit = VGroup(core, dna).rotate(28 * DEGREES, RIGHT, about_point=ORIGIN).rotate(-10 * DEGREES, OUT, about_point=ORIGIN)
        unit.move_to([-1.9, 0.25, 0])
        turns = figure("1.67 turns", "of DNA, about 147 base pairs", DNA, 40).move_to([4.5, 1.1, 0])
        eight = figure("8 histones", "the protein spool", HISTONE, 40).move_to([4.5, -0.9, 0])
        sketch = note("schematic, not to scale")
        self.pin(turns, eight, sketch)
        with self.narrate("DNA's twisted ladder, the double helix, wraps almost twice around a spool of eight "
                          "proteins called histones.") as dur:
            t0 = self.time
            self.play(FadeOut(hx, scale=0.3), FadeIn(core, scale=1.25), FadeIn(sketch), run_time=1.0)
            self.play(ShowIncreasingSubsets(dna), FadeIn(turns, shift=LEFT * 0.2), run_time=min(2.6, dur * 0.4))
            spin(unit, tilt, 0.45)
            self.wait(self.left(t0, dur, 1.2) - 1.0)
            self.play(FadeIn(eight, shift=LEFT * 0.2), run_time=0.8)
        name = T("nucleosome", 40, ACCENT, BOLD).move_to([-1.9, -2.65, 0])
        string = beads().rotate(18 * DEGREES, RIGHT, about_point=ORIGIN).move_to([0, 0.35, 0])
        caption = figure("beads on a string", "about 10 nm thick; the bare helix is 2 nm", ACCENT, 40).move_to([0, -2.1, 0])
        self.pin(name, caption)
        with self.narrate("Each wrapped spool is a nucleosome. Spool after spool, the DNA becomes beads on a string.") as dur:
            t0 = self.time
            self.play(FadeIn(name, shift=UP * 0.2), run_time=0.8)
            self.wait(max(0.3, dur * 0.36 - 0.8))
            unit.clear_updaters()
            self.play(FadeOut(name), FadeOut(turns), FadeOut(eight), unit.animate.scale(0.34).move_to(string), run_time=1.0)
            self.play(FadeOut(unit), FadeIn(string), run_time=0.8)
            spin(string, RIGHT, 0.4)
            self.wait(max(0.1, self.left(t0, dur) - 1.3))
            self.play(FadeIn(caption, shift=UP * 0.2), run_time=0.9)
        self.beat()

        # 2 · Loop it: the string runs off along its own length; condensins pull it into loops.
        self.chapter("Loop it", bridge="But that string is still far too long.", card=False, transition=whip(LEFT))
        loops, scaffold, bases = loop_array()
        brush = VGroup(scaffold, loops).move_to([-1.9, -0.15, 0])
        bases = [b + scaffold.get_center() for b in bases]  # the scaffold was built centred on the origin
        ax = scaffold.get_center()
        strand = thread([ax + np.array([0.22 * np.sin(5 * y), y, 0.22 * np.cos(5 * y)]) for y in np.linspace(2.7, -2.7, 81)], DNA, 6)
        cond = figure("condensins", "proteins along a central scaffold", CONDENSIN, 40).move_to([4.2, 1.1, 0])
        looped = figure("loops", "of the beaded string", DNA, 40).move_to([4.2, -0.9, 0])
        sketch = note("schematic, not to scale")
        self.pin(cond, looped, sketch)
        with self.narrate("So before a cell divides, proteins called condensins pull it into loops, packed around a "
                          "central scaffold.") as dur:
            t0 = self.time
            self.play(ShowIncreasingSubsets(strand), FadeIn(sketch), run_time=min(1.3, dur * 0.22))
            self.play(FadeIn(scaffold), FadeIn(cond, shift=LEFT * 0.2), run_time=0.9)
            self.play(LaggedStart(*[GrowFromPoint(m, b) for m, b in zip(loops, bases)], lag_ratio=0.06),
                      FadeOut(strand), FadeIn(looped, shift=LEFT * 0.2), run_time=min(2.8, self.left(t0, dur, 1.5)))
            spin(brush, UP, 0.5)
        chrom = chromosome().scale(1.25).move_to([-1.9, -0.15, 0])
        shorter = figure("≈10,000×", "shorter than the stretched-out DNA", ACCENT, 56).move_to([3.9, 1.0, 0])
        named = figure("chromosome", "one of 46 in a human cell", INK, 40).move_to([3.9, -1.1, 0])
        self.pin(shorter, named)
        with self.narrate("Loop upon loop, the DNA becomes about ten thousand times shorter. That is a chromosome.") as dur:
            t0 = self.time
            brush.clear_updaters()
            self.play(FadeOut(cond), FadeOut(looped), brush.animate.scale(0.5), run_time=0.9)
            self.play(FadeOut(brush, scale=0.8), FadeIn(chrom, scale=1.15), FadeIn(shorter, shift=LEFT * 0.2), run_time=0.9)
            turn = Rotate(chrom, TAU, axis=UP, about_point=chrom.get_center(), rate_func=smooth)
            self.move_camera(phi=24 * DEGREES, theta=-90 * DEGREES, added_anims=[turn],
                             run_time=max(2.0, self.left(t0, dur) - 0.2))
            self.play(FadeIn(named, shift=LEFT * 0.2), run_time=0.6)
        self.beat()

        # Ending: the question comes back over the finished chromosome and is answered there.
        self.play(FadeOut(shorter), FadeOut(named), FadeOut(sketch), run_time=0.4)
        self.move_camera(phi=0, theta=-90 * DEGREES, added_anims=[chrom.animate.scale_to_fit_height(3.7).move_to([0, -1.5, 0])], run_time=0.9)
        self.outro([], "To go deeper, read about chromatin in OpenStax Biology.",
                   answer="Wound on histone spools, then looped: about 10,000 times shorter.",
                   answer_tts="Wound on histone spools, then looped: about ten thousand times shorter.", keep=[chrom])
