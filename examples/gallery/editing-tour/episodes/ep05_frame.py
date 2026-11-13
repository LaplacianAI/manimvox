"""Chapter 5, frame and speed: fit (contain, cover, crop) drawn from the demolition inside a film frame, speed as one
number and as keyframes (the graph is plotted from the real ramp with manimvox's own Clock), the before and after of
the slowed fall, and the mistake of giving keyframes in the film's seconds. Script: episodes/tour.md. The message
under the mistake is real (build/said.json)."""
from bench import *
from make_edit import RAMP

from manimvox.edit.timeline import Clock

SPAN = (29.0, 40.0)  # the fall's clip: seconds of the file
H169 = CLIP_W * 9 / 16
SC = CLIP_W / 640  # scene units a source pixel, on the raw clip


def play(clip, rate=1.0, clock=None):
    """Run a clip's frames under whatever plays next: at `clip.rate` times real speed, or along a ramp's Clock."""
    clip._s, clip.rate, clip.s_now = 0.0, rate, 0.0
    span = len(clip.frames) / clip.fps

    def step(m, dt):
        m._s += dt * m.rate
        if clock is not None:
            m.s_now = clock.source(m._s % clock.seconds) - clock.start
        else:
            m.s_now = m._s % span
        m.show(min(int(m.s_now * m.fps), len(m.frames) - 1))

    clip.add_updater(step)
    return clip


def seg(*extra, w=PANEL_W):
    """The demolition segment as the edit file writes it, with the fields being taught."""
    body = ['{"clip": "demolition.webm",', ' "start": 29, "end": 40,', *extra]
    return EditPanel("\n".join(body), size=20, w=w).move_to(PANEL_AT).set_z_index(10)


def lit(panel, *ks, dim=0.32):
    """Lines `ks` lit, the rest dim, at once (for a panel that is about to fade in)."""
    ks = {panel.find(k) if isinstance(k, str) else k for k in ks}
    for k, (row, bar) in enumerate(zip(panel.rows, panel.bars, strict=True)):
        row.set_opacity(1 if k in ks else dim)
        bar.set_fill(opacity=0.18 if k in ks else 0)
    return panel


def masks(frame_w, m):
    """Four dark strips round a frame at the clip's place: whatever grows past the frame is trimmed by them."""
    cx, cy = CLIP_AT[0], CLIP_AT[1]
    out = []
    for sx in (-1, 1):
        out.append(Rectangle(width=m, height=H169 + 1.6, stroke_width=0, fill_color=BG, fill_opacity=1)
                   .move_to([cx + sx * (frame_w / 2 + m / 2), cy, 0]))
    for sy in (-1, 1):
        out.append(Rectangle(width=frame_w, height=0.8, stroke_width=0, fill_color=BG, fill_opacity=1)
                   .move_to([cx, cy + sy * (H169 / 2 + 0.4), 0]))
    return VGroup(*out).set_z_index(5)


def cap(text, y=-2.62, x=CLIP_AT[0]):
    return T(text, 22, MUTED).move_to([x, y, 0]).set_z_index(8)


def result_from(ep, name, g):
    """Bench.show_result with the bench clip `g` (a footage group) as its lead. The clip steps out of its group
    for the call (a plain Group cannot save and restore its state) and goes back in after."""
    clip = g.clip
    g.remove(clip)
    ep.add(clip)
    ep.show_result(name, lead=clip)
    ep.remove(clip)
    g.submobjects.insert(0, clip)


class Ep05(Bench):
    EP = 5
    TITLE = "Frame and speed"

    def build(self):
        _title, enter = self.heading("Frame and speed", "letters")

        # the film's frame, and the demolition in it
        fbg = Rectangle(width=CLIP_W, height=H169, stroke_width=0, fill_color=PANEL2, fill_opacity=1).move_to(CLIP_AT)
        fout = Rectangle(width=CLIP_W, height=H169, stroke_color=MUTED, stroke_width=2).move_to(CLIP_AT)
        fout.set_z_index(6)
        src = footage(DEMOLITION, *SPAN, CLIP_W).move_to(CLIP_AT)
        clip = src.clip.loop()

        p_contain = lit(seg(' "fit": "contain"}'), "fit")
        p_cover = lit(seg(' "fit": "cover"}'), "fit")
        p_crop = lit(seg(' "fit": "crop",', ' "crop": [80, 90, 480, 270]}'), 2, 3)
        p_speed = lit(seg(' "speed": 2}'), 2)
        p_ramp = lit(seg(' "speed": [[31, 1], [32, 0.3],', '           [35.5, 0.3], [36.5, 1]]}'), 2, 3)

        c0 = cap("a 640 x 360 picture in a 1920 x 1080 frame")
        self.say("Last chapter joined pieces end to end. Now we change what's inside a piece: its shape, and its "
                 "time.", enter, FadeIn(fbg), FadeIn(src), run_time=1.2)
        self.say("Footage rarely matches the film's shape, so fit says how it fills the frame.",
                 FadeIn(p_contain), FadeIn(c0), run_time=0.8)
        self.beat(0.3)

        # contain, then cover: a squarer frame, so the difference shows
        c1, c2 = cap("a squarer frame: contain"), cap("cover")
        m4 = masks(CLIP_W * 0.75, 1.0)

        def squarer():
            return [fbg.animate.stretch_to_fit_width(CLIP_W * 0.75), fout.animate.stretch_to_fit_width(CLIP_W * 0.75),
                    src.animate.scale(0.75), FadeOut(c0), FadeIn(c1)]

        def trim():
            self.add(m4)
            return [src.animate.scale(4 / 3), FadeOut(p_contain), FadeIn(p_cover), FadeOut(c1), FadeIn(c2)]

        self.say("Contain letterboxes it, with bars.", *squarer(), run_time=1.1)
        self.say("Cover fills the frame and trims the edges.", *trim(), run_time=1.1)
        self.beat(0.3)

        # crop: a box in the file's own pixels, scaled up to fill
        def px(x, y):
            return CLIP_AT + np.array([(x - 320) * SC, (180 - y) * SC, 0])

        boxc = px(320, 225)  # the crop box [80, 90, 480, 270] is centred at (320, 225)
        box = Rectangle(width=480 * SC, height=270 * SC, stroke_color=ACCENT, stroke_width=4).move_to(boxc)
        box.set_z_index(7)
        c3, c4 = cap("crop: 480 x 270 of the file's pixels"), cap("scaled up to fill the frame")

        def show_box():
            return [FadeOut(m4), fbg.animate.stretch_to_fit_width(CLIP_W), fout.animate.stretch_to_fit_width(CLIP_W),
                    FadeOut(p_cover), FadeIn(p_crop), FadeOut(c2), FadeIn(c3), Create(box)]

        def fill():
            return [clip.zoom(80, 90, 480, 270, pad=0), FadeOut(box), FadeOut(c3), FadeIn(c4)]

        self.steps("And crop shows just the region you give, in the file's own pixels, scaled up to fill.",
                   [show_box(), fill()], run_time=1.2)
        self.beat(0.3)

        # speed: one number
        bar_y = -2.62
        track = Rectangle(width=CLIP_W, height=0.16, stroke_color=LINE, stroke_width=1.5).move_to([CLIP_AT[0], bar_y, 0])
        fillbar = Rectangle(width=CLIP_W, height=0.16, stroke_width=0, fill_color=ACCENT, fill_opacity=1)
        fillbar.move_to(track)
        l1 = T("11 s at normal speed", 22, INK).next_to(track, DOWN, buff=0.22).align_to(track, LEFT)
        l2 = T("5.5 s at 2x", 22, INK).move_to(l1, aligned_edge=LEFT)
        rng = T("0.25x to 4x, the pitch kept", 22, MUTED).next_to(track, DOWN, buff=0.22).align_to(track, RIGHT)

        self.play(clip.zoom_out(), FadeOut(c4), run_time=0.8)
        clip.clear_updaters()
        play(clip, 1.0)
        self.steps("Speed plays a clip faster or slower, from a quarter to four times, and the sound keeps its "
                   "pitch, so voices don't squeak.",
                   [[FadeOut(p_crop), FadeIn(p_speed), FadeIn(track), FadeIn(fillbar), FadeIn(l1)],
                    [UpdateFromAlphaFunc(clip, lambda m, a: setattr(m, "rate", 1 + a)),
                     fillbar.animate.stretch_to_fit_width(CLIP_W / 2).align_to(track, LEFT),
                     FadeOut(l1), FadeIn(l2), FadeIn(rng)]], run_time=1.2)
        self.beat(0.3)

        # speed as keyframes: the graph is the real ramp
        gx0, gx1, gy0, gy1 = -5.9, -0.4, -2.5, -1.15  # the plot's box; speed 0 to 1.1
        file0, file1 = SPAN

        def at(s, v):
            return np.array([gx0 + (s - file0) / (file1 - file0) * (gx1 - gx0), gy0 + v / 1.1 * (gy1 - gy0), 0])

        ramp = tuple((float(a), float(b)) for a, b in RAMP)
        clock = Clock(file0, file1, ramp)
        ss = np.linspace(file0, file1, 220)
        curve = VMobject(color=ACCENT, stroke_width=5).set_points_as_corners([at(s, float(clock.rate(s))) for s in ss])
        axis = VGroup(Line(at(file0, 0), at(file1, 0), color=LINE, stroke_width=2),
                      Line(at(file0, 0), at(file0, 1.1), color=LINE, stroke_width=2))
        ticks = VGroup(*[T(f"{s}", 18, MUTED).move_to(at(s, 0) + DOWN * 0.3) for s in (30, 32, 34, 36, 38, 40)])
        ylab = VGroup(T("1x", 18, MUTED).move_to(at(file0, 1) + LEFT * 0.35),
                      T("0.3x", 18, MUTED).move_to(at(file0, 0.3) + LEFT * 0.4))
        title_g = T("speed, by seconds of the file", 18, MUTED).move_to(at(file1, 0) + DOWN * 0.62, aligned_edge=RIGHT)
        graph = VGroup(axis, ticks, ylab, title_g)
        dots = VGroup(*[Dot(at(s, v), radius=0.07, color=INK) for s, v in RAMP])
        head = Dot(at(file0, 1), radius=0.1, color=INK).set_z_index(9)

        def follow(m):
            s = file0 + clip.s_now
            m.move_to(at(s, float(clock.rate(s))))

        head.add_updater(follow)

        small = 4.8 / CLIP_W
        clip.clear_updaters()
        play(clip, 1.0, clock)
        self.steps("But a moment can be slowed on its own. Give speed as keyframes, each a second of the file and "
                   "a speed, and the speed eases from one to the next.",
                   [[src.animate.scale(small).move_to([-3.4, 0.55, 0]), FadeOut(fbg), FadeOut(fout), FadeOut(track),
                     FadeOut(fillbar), FadeOut(l2), FadeOut(rng), FadeOut(p_speed), FadeIn(p_ramp)],
                    [FadeIn(graph), Create(curve)],
                    [LaggedStart(*[FadeIn(d, scale=1.6) for d in dots], lag_ratio=0.25)]], run_time=1.2)
        self.add(head)
        self.steps("Here it runs at normal speed, slows to three tenths as the towers fall, holds, and speeds up "
                   "again.", [FadeIn(head), Indicate(curve, color=ACCENT, scale_factor=1.0)], run_time=0.8)
        self.beat(0.3)
        result_from(self, "r05", src)

        # before and after: the fall at real speed, then stretched
        clip.clear_updaters()
        before = footage(DEMOLITION, *SPAN, 6.4)
        after = result("fall", 6.4)
        pair, tags = before_after(before, after)
        for m in (before, after):
            m.clip.loop()
        l_b = T("11 s of the file", 22, INK).next_to(before, DOWN, buff=0.2).align_to(before, LEFT)
        l_a = T("20.8 s on the film", 22, INK).next_to(after, DOWN, buff=0.2).align_to(after, LEFT)
        self.say("The fall took about four seconds. Slowed, it fills about thirteen, long enough to watch each "
                 "tower go.",
                 FadeOut(Group(src, graph, curve, dots, head, p_ramp)), FadeIn(pair), FadeIn(tags), FadeIn(l_b),
                 FadeIn(l_a), run_time=1.2)
        self.beat(0.5)

        # the mistake
        m = Mistake('"speed": [[2, 1], [3, 0.3]]', '"speed": [[31, 1], [32, 0.3]]', SAID["film_keys"][0], w=9.0,
                    size=26).move_to(DOWN * 0.1)
        t_wrong = T("seconds of the film", 22, MUTED).next_to(m.wrong, RIGHT, buff=0.5)
        t_right = T("seconds of the file", 22, MUTED).next_to(m.right, RIGHT, buff=0.5)
        VGroup(m.wrong, m.strike)
        self.steps("The mistake is giving keyframes in the film's seconds. They're seconds of the clip's own file, "
                   "the same clock as start and end.",
                   [[FadeOut(Group(pair, tags, l_a, l_b))], [*m.wrong_in(), FadeIn(t_wrong)],
                    m.struck(), [*m.fixed(), FadeIn(t_right)]], run_time=1.2)
        self.beat(1.0)

        # takeaway and bridge, ending on the clip the result starts with
        end = footage(DEMOLITION, *SPAN, CLIP_W).move_to(CLIP_AT)
        end.clip.loop()
        self.say("So fit shapes the picture, and speed changes time, steadily or around one moment.",
                 FadeOut(Group(m, t_wrong, t_right)), FadeIn(end), run_time=1.0)
        nxt = VGroup(T("next", 22, MUTED), T("Over the picture", 30, INK, weight=BOLD)).arrange(
            DOWN, buff=0.1, aligned_edge=RIGHT).move_to([6.2, -3.0, 0], aligned_edge=RIGHT).set_z_index(12)
        self.say("Next, what sits over the picture.", blur_in(nxt), run_time=0.8)
        self.beat(0.8)
        self.play(*[FadeOut(m) for m in self.stage()], run_time=0.8)
        self.beat(0.4)
