from blocks.heart_ct import Heart

from manimvox.kit import *
from manimvox.scenes import from_pyvista, screen_xy

CREDIT = "Heart from CT: Rodero et al. 2021, Zenodo 4590294, CC BY 4.0"
ZOOM, WIDTH, CENTRE = 1.25, 10.6, DOWN * 0.2

heart = Heart()
px = {}  # pixel position of each landmark in the front view


def front(pl, t):
    heart.camera(pl, zoom=ZOOM)
    for name, p in {**heart.p, "septum": heart.septum()}.items():
        px[name] = screen_xy(pl, p)


def turning():
    return from_pyvista(lambda pl, t: heart.camera(pl, turn=360 * t / 9, zoom=ZOOM), 9, fps=15, width=WIDTH,
                        setup=lambda pl: heart.add(pl, heart.outside))


def cutting():
    """The front sliced away: the cut sweeps from in front of the heart to the four-chamber plane."""
    shown = []

    def draw(pl, t):
        for a in shown:
            pl.remove_actor(a)
        shown.clear()
        k = min(1.0, t / 2.2)
        shown.extend(heart.add_cut(pl, offset=heart.radius * (1 - smooth(k)), glass=0))
        heart.camera(pl, zoom=ZOOM)

    return from_pyvista(draw, 2.4, fps=15, width=WIDTH)


def opened(glass):
    return from_pyvista(front, 1 / 15, width=WIDTH, setup=lambda pl: heart.add_cut(pl, glass=glass))


def tag(clip, name, text, color, x, dy=0.0):
    """A clean anatomy label: a dot on the part, a thin leader, the name off to the side (`dy` lower)."""
    p = clip.at(*px[name])
    label = T(text, 22, color, BOLD)
    label.move_to([x, p[1] - dy, 0])
    if x < 0:
        label.align_to([x, 0, 0], RIGHT)
    else:
        label.align_to([x, 0, 0], LEFT)
    end = label.get_right() + RIGHT * 0.15 if x < 0 else label.get_left() + LEFT * 0.15
    return VGroup(Line(end, p, color=LINE, stroke_width=2), Dot(p, radius=0.06, color=color), label)


def at(clip, spec):
    """A scene point on the clip: a landmark name, or (name, dx, dy) pixels from it, or (a, b, f) part way."""
    if isinstance(spec, str):
        return clip.at(*px[spec])
    if isinstance(spec[1], str):
        p, q, f = spec
        return at(clip, p) + (at(clip, q) - at(clip, p)) * f
    name, dx, dy = spec
    x, y = px[name]
    return clip.at(x + dx, y + dy)


def stream(clip, route_specs, color, n=40, speed=0.16):
    """Blood as a stream of glowing dots along the route, fading in where it enters and out where it leaves."""
    route = VMobject().set_points_smoothly([at(clip, r) for r in route_specs])
    trail = route.copy().set_stroke(color, 9, opacity=0.14)
    dots = VGroup(*[VGroup(Dot(radius=0.085, color=color), Dot(radius=0.042, color=color)) for _ in range(n)])
    dots.phase, dots.level = 0.0, 1.0

    def flow(m, dt):
        m.phase = (m.phase + dt * speed) % 1
        for i, d in enumerate(m):
            s = (m.phase + i / n) % 1
            d.move_to(route.point_from_proportion(s))
            a = m.level * max(0.0, min(1.0, s / 0.08, (1 - s) / 0.12))
            d[0].set_opacity(0.22 * a)
            d[1].set_opacity(a)

    flow(dots, 0)
    dots.add_updater(flow)
    return trail, dots


def exit_arrow(clip, valve, dx, text, color):
    """Where blood leaves through an artery in front of the cut: a dashed arrow up from the valve."""
    start = at(clip, valve) + UP * 0.15
    end = np.array([start[0] + dx, clip.at(0, 30)[1], 0])
    arr = arrow(start, end, color=color, dashed=True, sw=3)
    label = T(text, 20, color, BOLD).next_to(end, LEFT if dx < 0 else RIGHT, buff=0.15)
    return VGroup(arr, label)


class Ep01(Episode):
    EP = 1
    TITLE = "Inside the Heart"
    TAGLINE = "Its parts, and how blood flows through them"
    NCHAP = 2

    def build(self):
        spin = turning().move_to(CENTRE)
        cut = cutting().move_to(CENTRE)
        clean = opened(0).move_to(CENTRE)
        for z, clip in enumerate((spin, cut, clean)):
            clip.set_z_index(-10 + z)  # under every label and the blood
        self.intro("Your heart is two pumps in one. Let's open one up and see.",
                   question="What is inside the heart, and how does blood move through it?")

        # 1 -- the parts, on a real heart cut open
        self.chapter("The parts", "First, the parts.")
        credit = note(CREDIT)
        self.add(spin)
        self.play(FadeIn(spin), FadeIn(credit), run_time=0.6)
        with self.narrate("This is a real human heart, rebuilt from a CT scan.") as dur:
            self.play(spin.play(), run_time=max(dur, 5))
        self.remove(spin)
        self.add(cut)
        with self.narrate("Slice away the front, and four chambers appear.") as dur:
            self.play(cut.play(), run_time=dur)
        self.remove(cut)
        self.add(clean)

        ra = tag(clean, "ra", "Right atrium", OXYGEN_POOR, -3.4)
        la = tag(clean, "la", "Left atrium", OXYGEN_RICH, 3.4)
        rv = tag(clean, "rv", "Right ventricle", OXYGEN_POOR, -3.4)
        lv = tag(clean, "lv", "Left ventricle", OXYGEN_RICH, 3.4)
        self.say("On top, the two atria take blood in.", LaggedStart(FadeIn(ra), FadeIn(la), lag_ratio=0.4))
        self.say("Below, the two ventricles pump it out.", LaggedStart(FadeIn(rv), FadeIn(lv), lag_ratio=0.4))
        septum = tag(clean, "septum", "Septum", INK, -3.4, dy=1.1)
        self.say("A wall of tissue, the septum, keeps the two sides apart.", FadeIn(septum))
        tv = tag(clean, "tricuspid", "Tricuspid valve", WARN, -3.4)
        mv = tag(clean, "mitral", "Mitral valve", WARN, 3.4)
        self.say("And valves, in yellow, keep blood moving one way.", LaggedStart(FadeIn(tv), FadeIn(mv), lag_ratio=0.4))
        self.beat(0.5)

        # 2 -- the flow: the right side to the lungs, the left side to the body
        self.chapter("Two pumps", "Now follow the blood.")
        self.add(clean, note(CREDIT))
        self.play(FadeIn(clean), run_time=0.6)
        # down the outer wall of each ventricle, then up beside the septum to the outflow valve
        poor_trail, poor = stream(clean, [("svc", 0, -70), "svc", "ra", "tricuspid", ("rv", -45, 40),
                                          ("rv_apex", "rv", 0.3), ("septum", -40, -30), "pulmonary_valve"],
                                  OXYGEN_POOR)
        rich_trail, rich = stream(clean, [("rspv", 0, -40), "la", "mitral", ("lv", 55, 20), ("apex", "lv", 0.35),
                                          ("septum", 40, -30), "aortic_valve"], OXYGEN_RICH)
        to_lungs = exit_arrow(clean, "pulmonary_valve", -1.6, "to the lungs", OXYGEN_POOR)
        to_body = exit_arrow(clean, "aortic_valve", 1.6, "to the body", OXYGEN_RICH)

        self.say("Oxygen-poor blood from the body enters the right atrium.", Create(poor_trail), FadeIn(poor))
        self.say("It passes the tricuspid valve into the right ventricle,")
        self.say("which pumps it through the pulmonary valve, to the lungs.", Create(to_lungs[0]), FadeIn(to_lungs[1]))
        self.say("Oxygen-rich blood comes back from the lungs into the left atrium.",
                 Create(rich_trail), FadeIn(rich), poor_trail.animate.set_stroke(opacity=0.05), to_lungs.animate.set_opacity(0.3))
        poor.level = 0.3
        self.say("It passes the mitral valve into the left ventricle,")
        self.say("which pumps it through the aortic valve, to the whole body.", Create(to_body[0]), FadeIn(to_body[1]))
        poor.level = 1.0
        self.say("Right side to the lungs, left side to the body: two pumps, side by side.",
                 poor_trail.animate.set_stroke(opacity=0.14), to_lungs.animate.set_opacity(1))
        self.beat(1.0)
        for m in (poor, rich):
            m.clear_updaters()

        self.outro(["The atria take blood in; the ventricles pump it out",
                    "The septum keeps the sides apart; valves keep blood moving one way",
                    "The right side pumps to the lungs, the left side to the body"],
                   "Four chambers, two pumps, one heartbeat.",
                   answer="Four chambers and their valves: blood goes from the body through the right side to "
                          "the lungs, then through the left side out to the body.")
