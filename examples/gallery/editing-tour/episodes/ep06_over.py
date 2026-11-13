"""Chapter 6, over the picture: the five overlays, one at a time, each drawn on the footage in its box (the badge,
the text lower third, a clip in a corner, fx.py:speed_meter and scenes.py:Falling), then the mistake of a box that
runs off the frame. Script: episodes/tour.md. The message under the mistake is real (build/said.json)."""
import fx
from bench import *
from make_edit import RAMP

from manimvox.edit.timeline import Clock
from manimvox.scenes import from_frames

W6 = 6.4  # the footage on this bench, a little narrower to leave the panel room
AT6 = np.array([-3.4, -0.2, 0])
PX = np.array([3.4, -0.2, 0])
K = W6 / 1920  # scene units a pixel of the film
LEFT_X, TOP_Y = AT6[0] - W6 / 2, AT6[1] + W6 * 9 / 32
SPAN = (29.0, 40.0)


def film(x, y):
    """The scene point over pixel (x, y) of the 1920 x 1080 film, laid on the footage."""
    return np.array([LEFT_X + x * K, TOP_Y - y * K, 0])


def ov(*lines):
    return EditPanel("\n".join(lines), size=20, w=6.4).move_to(PX).set_z_index(10)


def lit(panel, *ks, dim=0.32):
    ks = {panel.find(k) if isinstance(k, str) else k for k in ks}
    for k, (row, bar) in enumerate(zip(panel.rows, panel.bars, strict=True)):
        row.set_opacity(1 if k in ks else dim)
        bar.set_fill(opacity=0.18 if k in ks else 0)
    return panel


def band(mob, buff=0.1, opacity=0.78):
    return VGroup(BackgroundRectangle(mob, color=BG, fill_opacity=opacity, buff=buff), mob)


def run(clip, clock=None):
    """Play a clip along a ramp's Clock under whatever comes next; `clip._s` is the seconds it has run."""
    clip._s = 0.0
    span = len(clip.frames) / clip.fps

    def step(m, dt):
        m._s += dt
        s = (clock.source(m._s % clock.seconds) - clock.start) if clock else m._s % span
        m.show(min(int(s * m.fps), len(m.frames) - 1))

    clip.add_updater(step)
    return clip


def result_from(ep, name, g):
    """Bench.show_result with the bench clip `g` (a footage group) as its lead. The clip steps out of its group
    for the call (a plain Group cannot save and restore its state) and goes back in after."""
    clip = g.clip
    g.remove(clip)
    ep.add(clip)
    ep.show_result(name, lead=clip)
    ep.remove(clip)
    g.submobjects.insert(0, clip)


class Ep06(Bench):
    EP = 6
    TITLE = "Over the picture"

    def build(self):
        _title, enter = self.heading("Over the picture", "blur")

        talk = footage(INTERVIEW, 12.5, 23.0, W6).move_to(AT6)
        talk.clip.loop()
        p_text = lit(ov('{"text": "Prof Joyeeta Gupta",', ' "sub": "University of Amsterdam and UNESCO-IHE",',
                        ' "kind": "lower-third",', ' "at": 4.1, "until": 9}'), 3)

        # 1. overlays sit on top, from at to until, on the film's clock
        layer = Rectangle(width=W6, height=W6 * 9 / 16, stroke_color=ACCENT, stroke_width=2.5, fill_color=ACCENT,
                          fill_opacity=0.06).move_to(AT6 + UR * 0.2).set_z_index(6)
        layer_tag = T("overlays", 22, ACCENT).next_to(layer, UP, buff=0.12).align_to(layer, RIGHT)
        x0, per = LEFT_X, W6 / 10.5  # the film's clock under the picture: 10.5 s across
        track = Line([x0, -2.55, 0], [x0 + W6, -2.55, 0], color=LINE, stroke_width=4)
        span = Line([x0 + 4.1 * per, -2.55, 0], [x0 + 9 * per, -2.55, 0], color=ACCENT, stroke_width=8)
        t_at = T("at 4.1", 22, INK).move_to([x0 + 4.1 * per, -2.9, 0])
        t_until = T("until 9", 22, INK).move_to([x0 + 9 * per, -2.9, 0])
        t_clock = T("seconds of the film", 18, MUTED).move_to([x0, -2.9, 0], aligned_edge=LEFT)
        t_clock.shift(DOWN * 0.0)
        t_at.shift(RIGHT * 0.35)
        self.say("So far, everything has been the picture itself. Now, the layer on top of it.",
                 enter, FadeIn(talk), run_time=1.2)
        self.steps("Overlays sit on top of the picture, each from an at time to an until time on the film's clock.",
                   [[FadeIn(p_text), FadeIn(layer), FadeIn(layer_tag)],
                    [FadeIn(track), Create(span), FadeIn(t_at), FadeIn(t_until), FadeIn(t_clock)]], run_time=1.1)
        self.beat(0.3)

        # 2. text: a lower third, a title, a label
        name = T("Prof Joyeeta Gupta", 24, INK, weight=BOLD)
        role = T("University of Amsterdam and UNESCO-IHE", 17, MUTED)
        lt = VGroup(name, role).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        bar = Rectangle(width=0.06, height=lt.height, stroke_width=0, fill_color=ACCENT, fill_opacity=1)
        lt = VGroup(bar, lt).arrange(RIGHT, buff=0.15)
        lt = band(lt, 0.14).move_to(talk.get_corner(DL) + UR * 0.45, aligned_edge=DL).set_z_index(7)
        lt.align_to(talk, LEFT).shift(RIGHT * 0.25)
        big = band(T("Where the water goes", 30, INK, weight=BOLD), 0.2).move_to(talk).set_z_index(7)
        lab = band(T("a label", 22, INK), 0.1).move_to(film(260, 150)).set_z_index(7)
        self.steps("A text overlay is a lower third, with a name and a role, a centred title, or a label at a "
                   "position you give.",
                   [[FadeOut(layer), FadeOut(layer_tag), FadeIn(lt, shift=RIGHT * 0.5), *p_text.light(0, 1)],
                    [FadeOut(lt), FadeIn(big), *p_text.light(2)],
                    [FadeOut(big), FadeIn(lab), *p_text.light(0, 2)]], run_time=0.9)
        self.beat(0.3)

        # 3. image: x, y, width in the film's pixels
        p_img = lit(ov('{"image": "build/badge.png",', ' "box": [1500, 40, 380],', ' "at": 4.1, "until": 9}'), 1)
        badge = picture("build/badge.png", 380 * K).move_to(film(1500 + 190, 40 + 54)).set_z_index(7)
        bw = 380 * K
        badge.move_to(film(1500, 40) + RIGHT * bw / 2 + DOWN * badge.height / 2)
        frame_b = SurroundingRectangle(badge, color=ACCENT, buff=0.04, stroke_width=3).set_z_index(8)
        dims = band(T("x 1500   y 40   width 380", 18, INK), 0.08).next_to(badge, DOWN, buff=0.2).set_z_index(8)
        dims.align_to(badge, RIGHT)
        self.steps("An image overlay places a picture, a logo or a diagram, in a box: x, y and width, in pixels of "
                   "the film. The height follows the image.",
                   [[FadeOut(lab), FadeOut(Group(track, span, t_at, t_until, t_clock)), FadeOut(p_text), FadeIn(p_img)],
                    [FadeIn(badge), Create(frame_b)], [FadeIn(dims)]], run_time=1.0)
        self.beat(0.3)

        # 4. clip: picture-in-picture
        p_clip = lit(ov('{"clip": "demolition.webm",', ' "start": 29,', ' "box": [1280, 600, 560],',
                        ' "at": 4.1, "until": 9}'), 2)
        pip = footage(DEMOLITION, *SPAN, 560 * K)
        pip.move_to(film(1280, 600) + RIGHT * 560 * K / 2 + DOWN * pip.height / 2).set_z_index(7)
        pip.clip.loop()
        pip_box = SurroundingRectangle(pip, color=ACCENT, buff=0.04, stroke_width=3).set_z_index(8)
        silent = band(T("silent", 18, INK), 0.08).next_to(pip, DOWN, buff=0.15).set_z_index(8)
        self.steps("A clip overlay is picture-in-picture, a second video in a box, silent unless you give it a "
                   "volume.",
                   [[FadeOut(Group(badge, frame_b, dims)), FadeOut(p_img), FadeIn(p_clip), FadeIn(pip),
                     Create(pip_box)], [FadeIn(silent)]], run_time=1.0)
        self.beat(0.3)

        # 5. draw: a gauge made by code, over the slowed fall
        clock = Clock(SPAN[0], SPAN[1], tuple((float(a), float(b)) for a, b in RAMP))
        fall = footage(DEMOLITION, *SPAN, W6).move_to(AT6)
        run(fall.clip, clock)
        gauge = from_frames(fx.speed_meter, 20.8, fps=5, width=520 * K)
        gauge.move_to(film(60, 900) + RIGHT * 520 * K / 2 + DOWN * gauge.height / 2).set_z_index(7)
        gauge.add_updater(lambda m: m.show(min(int(fall.clip._s * m.fps), len(m.frames) - 1)))
        p_draw = lit(ov('{"draw": "fx.py:speed_meter",', ' "box": [60, 900, 520],', ' "at": 4.1, "until": 9}'), 1)
        self.steps("A draw overlay is graphics made by your own code, a function given the time that returns a "
                   "picture.",
                   [[FadeOut(Group(talk, pip, pip_box, silent)), FadeIn(fall), FadeOut(p_clip), FadeIn(p_draw)],
                    [FadeIn(gauge)]], run_time=1.0)
        self.beat(0.3)

        # 6. scene: a Manim ring and label, background clear
        k = W6 / FW
        ring = Circle(radius=1.55 * k, color=ACCENT, stroke_width=4).move_to(AT6 + np.array([0.6, 0.6, 0]) * k)
        ring.set_z_index(7)
        text = VGroup(T("four towers come down", 20, INK, weight=BOLD), T("slowed to 0.3x", 16, ACCENT)).arrange(
            DOWN, buff=0.06)
        text = band(text, 0.1, 0.7).next_to(ring, UP, buff=0.12).set_z_index(7)
        p_scene = lit(ov('{"scene": "scenes.py:Falling",', ' "at": 4.1}'), 0)
        self.steps("And a scene overlay renders a Manim scene with a clear background and lays it over the "
                   "footage.", [[FadeOut(p_draw), FadeIn(p_scene), Create(ring)], [FadeIn(text, shift=DOWN * 0.1)]],
                   run_time=0.9)
        self.beat(0.5)
        result_from(self, "r06", fall)

        # the mistake: a box off the frame
        bad = picture("build/badge.png", 400 * K).set_z_index(7)
        bad.move_to(film(1700, 40) + RIGHT * 400 * K / 2 + DOWN * bad.height / 2)
        good_at = film(1500, 40) + RIGHT * 380 * K / 2 + DOWN * (380 * K / 3.51) / 2
        m = Mistake('"box": [1700, 40, 400]', '"box": [1500, 40, 380]', SAID["box"][0], w=5.5, size=21)
        m.move_to([3.85, 0.0, 0])
        self.steps("The mistake is a box that runs off the frame. Check edit catches it, and names the box.",
                   [[FadeOut(Group(ring, text, gauge)), FadeOut(p_scene), FadeIn(bad), *m.wrong_in()],
                    m.struck(),
                    [bad.animate.scale(0.95).move_to(good_at), *m.fixed()]], run_time=1.1)
        self.beat(1.0)

        self.say("So overlays add words, pictures, a second video, your own drawing or a whole scene on top.",
                 FadeOut(Group(m, bad)), run_time=0.8)
        self.say("But what if no file holds the picture you want?", run_time=0.4)
        nxt = VGroup(T("next", 22, MUTED), T("Your own code", 30, INK, weight=BOLD)).arrange(
            DOWN, buff=0.1, aligned_edge=RIGHT).move_to([6.2, -3.0, 0], aligned_edge=RIGHT).set_z_index(12)
        self.say("Next, your own code.", blur_in(nxt), run_time=0.8)
        self.beat(0.8)
        self.play(*[FadeOut(m) for m in self.stage()], run_time=0.8)
        self.beat(0.4)
