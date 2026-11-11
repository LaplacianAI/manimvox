from manimvox.kit import *


def thread(y=-0.2):
    """The opening's DNA: one thin wavy thread running edge to edge (not to scale)."""
    return ParametricFunction(lambda t: np.array([t, y + 0.18 * np.sin(2.3 * t) + 0.08 * np.sin(7.1 * t), 0]),
                              t_range=[-6.5, 6.5, 0.02]).set_stroke(STRAND_A, 3)


def nucleus_ring(at=(4.6, 1.15, 0)):
    return Circle(radius=0.32).set_stroke(MUTED, 2).set_fill(PANEL, 0.6).move_to(np.array(at))


def helix(length=9.0, r=0.55, turns=3.2, phase=2.3):
    """A double helix lying along x: two strands and the base-pair rungs between them."""
    def p(t, ph):
        th = 2 * PI * turns * (t + length / 2) / length + ph
        return np.array([t, r * np.cos(th), r * np.sin(th)])
    a = ParametricFunction(lambda t: p(t, 0), t_range=[-length / 2, length / 2, 0.03]).set_stroke(STRAND_A, 6)
    b = ParametricFunction(lambda t: p(t, phase), t_range=[-length / 2, length / 2, 0.03]).set_stroke(STRAND_B, 6)
    rungs = VGroup(*[Line(p(t, 0), p(t, phase)).set_stroke(MUTED, 2, 0.8)
                     for t in np.linspace(-length / 2 + 0.15, length / 2 - 0.15, 34)])
    return VGroup(rungs, a, b)


def octamer(radius=0.42, ring=0.46, gap=0.25, res=(10, 10)):
    """Eight histone proteins: two layers of four spheres, the spool's core (axis along z)."""
    balls = []
    for z in (-gap, gap):
        for k in range(4):
            ang = PI / 4 + k * PI / 2 + (PI / 4 if z > 0 else 0)
            s = Sphere(radius=radius, resolution=res).set_fill(HISTONE, 1).set_stroke(width=0)
            s.move_to([ring * np.cos(ang), ring * np.sin(ang), z])
            balls.append(s)
    return Group(*balls)


def wrap(R=1.0, h=0.9, turns=1.67, tail=1.3, width=9):
    """DNA wrapped about 1.7 turns round the spool, with a short tail in and out."""
    tmax = 2 * PI * turns

    def f(s):
        if s < 0:  # tail in, along the tangent at the start
            return np.array([R, s * tail, -h / 2])
        if s > 1:  # tail out, along the tangent at the end
            end = np.array([R * np.cos(tmax), R * np.sin(tmax), h / 2])
            tan = np.array([-np.sin(tmax), np.cos(tmax), 0])
            return end + tan * (s - 1) * tail
        th = s * tmax
        return np.array([R * np.cos(th), R * np.sin(th), -h / 2 + h * s])
    return ParametricFunction(f, t_range=[-1, 2, 0.01]).set_stroke(STRAND_A, width)


def bead(at, scale=0.36):
    core = Cylinder(radius=0.62, height=0.75, resolution=(12, 2)).set_fill(HISTONE, 1).set_stroke(width=0)
    w = wrap(R=0.8, h=0.6, tail=0.0, width=5)
    return Group(core, w).scale(scale).move_to(np.array(at))


def chromatid(n=26, top=2.2, length=1.15, rings=True, seed=3):
    """Loops fanned round a vertical (z) axis, each with a condensin ring at its base."""
    rng = np.random.default_rng(seed)
    loops, bases = VGroup(), VGroup()
    golden = PI * (3 - np.sqrt(5))
    for k in range(n):
        z = top - 2 * top * k / (n - 1)
        a = k * golden
        u = np.array([np.cos(a), np.sin(a), 0])
        v = np.array([-np.sin(a), np.cos(a), 0])
        L = length * (0.8 + 0.4 * rng.random())

        def f(s, z=z, u=u, v=v, L=L):
            return np.array([0, 0, z]) + u * L * np.sin(PI * s) + v * 0.32 * np.sin(2 * PI * s) \
                + np.array([0, 0, 0.12 * np.sin(2 * PI * s)])
        loops.add(ParametricFunction(f, t_range=[0, 1, 0.04]).set_stroke(LOOP, 3.5))
        if rings:
            c = Circle(radius=0.09).set_stroke(CONDENSIN, 4).move_to([0, 0, z])
            bases.add(c)
    axis = Line([0, 0, -top - 0.2], [0, 0, top + 0.2]).set_stroke(CONDENSIN, 3, 0.7)
    return VGroup(axis, loops, bases)


class Ep01(Episode3D):
    EP = 1
    TITLE = "How DNA fits in a chromosome"
    TAGLINE = "From a two-nanometre helix to a chromosome, in two moves"
    NCHAP = 2
    CHROME = ()

    def opening(self):
        th = thread()
        nuc = nucleus_ring()
        len_lbl = T("≈ 2 m of DNA per cell", 34, ACCENT, BOLD).move_to([-3.2, -1.25, 0])
        nuc_lbl = T("nucleus: 10–20 µm", 22, MUTED).next_to(nuc, DOWN, buff=0.22)
        scale = note("not to scale")
        return th, nuc, len_lbl, nuc_lbl, scale

    def build(self):
        # ---- cold open: a thread far longer than the place it must fit
        th, nuc, len_lbl, nuc_lbl, scale = self.opening()
        self.say("Each human cell holds about two metres of DNA, in a nucleus just ten to twenty microns across.",
                 Create(th, run_time=2.2), FadeIn(len_lbl), FadeIn(nuc), FadeIn(nuc_lbl), FadeIn(scale))
        self.intro("So how does that thread pack into chromosomes? In two moves: spools, then loops.",
                   question="How does two metres of DNA pack into chromosomes?", card=False, leave=[len_lbl, nuc_lbl])

        # ---- 1 Spools
        self.chapter("Spools", transition=zoom_through(nuc), card=False)
        dna = helix()
        lbl_helix = T("double helix", 26, INK, BOLD).move_to([-4.6, 2.55, 0])
        lbl_nm = T("2 nm wide", 30, ACCENT, BOLD).next_to(lbl_helix, DOWN, aligned_edge=LEFT, buff=0.18)
        scale1 = note("diagrams not to scale")
        self.pin(lbl_helix, lbl_nm, scale1)
        with self.narrate("Up close, the thread is a double helix, two nanometres wide."):
            self.play(Create(dna[1]), Create(dna[2]), FadeIn(dna[0]), FadeIn(scale1), run_time=1.6)
            self.move_camera(phi=62 * DEGREES, theta=-70 * DEGREES, run_time=1.6,
                             added_anims=[FadeIn(lbl_helix), FadeIn(lbl_nm)])

        spool = octamer()
        dw = wrap()
        nuc_group = Group(spool, dw).move_to(LEFT * 0.6)
        lbl_hist = T("8 histone proteins", 24, HISTONE, BOLD)
        lbl_bp = T("≈ 147 base pairs", 24, STRAND_A, BOLD)
        lbl_nuc = T("= one nucleosome", 26, INK, BOLD)
        col = VGroup(lbl_hist, lbl_bp, lbl_nuc).arrange(DOWN, aligned_edge=LEFT, buff=0.32).move_to([4.4, 0.4, 0])
        self.pin(col)
        self.steps("It wraps almost twice around a spool of eight histone proteins. Spool and DNA together make a nucleosome.",
                   [[FadeOut(dna, run_time=0.5), FadeOut(lbl_helix), FadeOut(lbl_nm)],
                    [FadeIn(spool), FadeIn(lbl_hist)],
                    [Create(dw, run_time=1.6), FadeIn(lbl_bp)],
                    FadeIn(lbl_nuc)])

        beads = Group()
        xs = np.linspace(-4.2, 4.2, 6)
        string = ParametricFunction(lambda t: np.array([t, 0.25 * np.sin(1.3 * t), 0.15 * np.cos(2.1 * t)]),
                                    t_range=[-6.0, 6.0, 0.03]).set_stroke(STRAND_A, 4)
        for x in xs:
            beads.add(bead([x, 0.25 * np.sin(1.3 * x), 0.15 * np.cos(2.1 * x)]))
        lbl_beads = T("beads on a string", 26, INK, BOLD).move_to([0, 2.55, 0])
        lbl_7 = T("≈ 7× shorter", 40, ACCENT, BOLD).move_to([0, -2.6, 0])
        self.pin(lbl_beads, lbl_7)
        self.steps("Repeated along the strand like beads on a string, nucleosomes make it about seven times shorter.",
                   [[FadeOut(nuc_group, run_time=0.5), FadeOut(col)],
                    [Create(string, run_time=1.2), FadeIn(beads, lag_ratio=0.2), FadeIn(lbl_beads)],
                    FadeIn(lbl_7, scale=1.2)])
        self.beat()

        # ---- 2 Loops
        self.chapter("Loops", bridge="But that is still far too long.", transition="dip", card=False)
        self.set_camera_orientation(phi=72 * DEGREES, theta=-60 * DEGREES, zoom=0.9)
        one = chromatid()
        axis, loops, rings = one
        lbl_cond = T("condensin rings", 24, CONDENSIN, BOLD)
        lbl_loop = T("loops of DNA", 24, LOOP, BOLD)
        col2 = VGroup(lbl_cond, lbl_loop).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([4.6, 1.2, 0])
        scale2 = note("diagram, not to scale")
        self.pin(col2, scale2)
        groups = [VGroup(*loops[i:i + 7]) for i in range(0, len(loops), 7)]
        rgroups = [VGroup(*rings[i:i + 7]) for i in range(0, len(rings), 7)]
        self.steps("Before a cell divides, protein rings called condensin pull the string into loops along a central axis.",
                   [[Create(axis), FadeIn(scale2), FadeIn(lbl_cond)]]
                   + [[FadeIn(r), Create(g, lag_ratio=0.15)] for r, g in zip(rgroups, groups)][:1]
                   + [[FadeIn(lbl_loop)] + [FadeIn(r) for r in rgroups[1:]] + [Create(g, lag_ratio=0.15) for g in groups[1:]]])

        two = chromatid(seed=8)
        two[1].set_stroke(interpolate_color(ManimColor(LOOP), ManimColor(INK), 0.35))
        sister_a = one
        sister_b = two
        lbl_sis = T("two sister chromatids", 24, INK, BOLD)
        lbl_cen = T("joined at the centromere", 22, MUTED)
        col3 = VGroup(lbl_sis, lbl_cen).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([4.5, -1.6, 0])
        self.pin(col3)
        self.begin_ambient_camera_rotation(rate=0.12)
        with self.narrate("Stacked loops thicken the axis into a chromosome: two copies, joined in the middle."):
            self.play(FadeOut(col2), FadeIn(sister_b), run_time=1.0)
            self.play(Rotate(sister_a, 26 * DEGREES, axis=UP, about_point=ORIGIN),
                      Rotate(sister_b, -26 * DEGREES, axis=UP, about_point=ORIGIN),
                      FadeIn(col3), run_time=1.6)
        self.beat()
        self.stop_ambient_camera_rotation()

        # ---- ending: back to the thread and the nucleus
        self.clear(how="blur")
        self.camera_home(run_time=0.1)
        th, nuc, len_lbl, nuc_lbl, scale = self.opening()
        big = Circle(radius=1.25).set_stroke(MUTED, 2).set_fill(PANEL, 0.6).move_to([0, -0.9, 0])
        self.play(FadeIn(th), FadeIn(nuc), FadeIn(scale), run_time=0.8)
        scale_end = T("not to scale", 15, MUTED, slant=ITALIC)
        xs = VGroup()
        rng = np.random.default_rng(5)
        for k in range(9):
            a = Line(UP * 0.17 + LEFT * 0.06, DOWN * 0.17 + RIGHT * 0.06).set_stroke(LOOP, 6)
            b = Line(UP * 0.17 + RIGHT * 0.06, DOWN * 0.17 + LEFT * 0.06).set_stroke(LOOP, 6)
            x = VGroup(a, b).rotate(rng.uniform(0, PI))
            ang, rad = 2 * PI * k / 9, 0.78 if k % 2 else 0.45
            x.move_to(big.get_center() + np.array([rad * np.cos(ang), rad * np.sin(ang), 0]))
            xs.add(x)
        ratio = T("≈ 10,000× shorter", 34, ACCENT, BOLD).next_to(big, RIGHT, buff=0.6)
        scale_end.next_to(ratio, DOWN, aligned_edge=LEFT, buff=0.2)
        self.play(ReplacementTransform(nuc, big), ReplacementTransform(th, xs), FadeIn(ratio),
                  ReplacementTransform(scale, scale_end), run_time=1.8)
        self.outro([], "To read more, start with Nature Scitable on DNA packaging.",
                   answer="Spools, then loops: about ten thousand times shorter than the bare thread.",
                   keep=[big, xs, ratio, scale_end], next_label="READ", next_title="Nature Scitable: DNA Packaging")
