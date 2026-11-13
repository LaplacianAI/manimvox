"""Chapter 7, your own code: fx.py on the bench, with short real excerpts of its countdown (a frames segment, drawn
for real from the function) and its vignette (an effect, laid over the interview from the same formula), the two
ways to name a function, and the mistake of an effect that changes the frame's size. Script: episodes/tour.md.
The message under the mistake is real (build/said.json)."""
import fx
from bench import *

from manimvox.scenes import from_frames, still

W6 = 6.4
AT6 = np.array([-3.4, -0.2, 0])
PX = np.array([3.4, -0.2, 0])
H6 = W6 * 9 / 16

COUNTDOWN = """\
def countdown():
    big = _font(260)

    def draw(t):
        img = Image.new("RGB", (W, H), BG)
        n = 3 - int(t // 0.8)
        k = (t % 0.8) / 0.8
        ...
        d.arc(box, -90, -90 + 360 * k, ...)
        d.text(..., str(max(1, n)), ...)
        return img

    return frames(draw, 2.4)"""

VIGNETTE = """\
def vignette(rgb, t):
    h, w = rgb.shape[:2]
    ...
    y, x = np.ogrid[-1:1:h * 1j, -1:1:w * 1j]
    ... np.hypot(x, y * 0.8) - 0.45 ...
    return (rgb * _VIG[(h, w)]).astype(np.uint8)"""

IN_JSON = """\
{"clip": "interview.webm",
 "start": 12.5, "end": 23,
 "effects": ["fx.py:vignette"]}"""

IN_PY = """\
Clip("interview.webm", start=12.5, end=23,
     effects=[vignette])"""


def code(src, title="fx.py", at=PX, size=20):
    return EditPanel(src, title, size=size, w=6.4).move_to(at).set_z_index(10)


def lit(panel, *ks, dim=0.32):
    ks = {panel.find(k) if isinstance(k, str) else k for k in ks}
    for k, (row, bar) in enumerate(zip(panel.rows, panel.bars, strict=True)):
        row.set_opacity(1 if k in ks else dim)
        bar.set_fill(opacity=0.18 if k in ks else 0)
    return panel


def framed(mob):
    g = Group(mob, SurroundingRectangle(mob, color=LINE, buff=0, stroke_width=2))
    g.clip = mob
    return g


def result_from(ep, name, g):
    """Bench.show_result with the bench clip `g` (a footage group) as its lead. The clip steps out of its group
    for the call (a plain Group cannot save and restore its state) and goes back in after."""
    clip = g.clip
    g.remove(clip)
    ep.add(clip)
    ep.show_result(name, lead=clip)
    ep.remove(clip)
    g.submobjects.insert(0, clip)


class Ep07(Bench):
    EP = 7
    TITLE = "Your own code"

    def build(self):
        _title, enter = self.heading("Your own code", "write")

        # what the code draws, for real: the countdown's frames, and the vignette's mask
        cd_src = fx.countdown()
        cd = framed(from_frames(cd_src.get_frame, cd_src.duration, fps=10, width=W6)).move_to(AT6)
        cd.clip.loop()
        cd0 = framed(still(cd_src.get_frame(0.0), W6)).move_to(AT6)
        white = np.full((360, 640, 3), 255, np.uint8)
        dark = 255 - fx.vignette(white, 0.0)[..., 0]  # how much the real effect darkens each pixel
        mask_img = np.zeros((360, 640, 4), np.uint8)
        mask_img[..., 3] = np.clip(dark.astype(int) * 2, 0, 255)  # drawn twice as strong, so it shows
        talk = footage(INTERVIEW, 12.5, 23.0, W6).move_to(AT6)
        talk.clip.loop()
        mask = still(mask_img, W6).move_to(AT6)
        stack = Group(talk, mask)

        blank = Rectangle(width=W6, height=H6, stroke_color=LINE, stroke_width=2, fill_color=PANEL, fill_opacity=1)
        blank.move_to(AT6)
        nothing = T("no recording, just code", 22, MUTED).move_to(blank)

        p_cd = lit(code(COUNTDOWN), 0)
        p_vig = lit(code(VIGNETTE), 0)

        self.say("Last chapter used a gauge drawn by code. Now, how to write code like that yourself.",
                 enter, FadeIn(blank), FadeIn(nothing), run_time=1.2)
        self.say("Then you make it. A frames segment is a piece of film made entirely by code.",
                 FadeIn(p_cd), run_time=1.0)
        self.beat(0.3)

        self.steps("This countdown is a function that draws each frame from the time. Frames runs it for as many "
                   "seconds as you give.",
                   [[FadeOut(blank), FadeOut(nothing), FadeIn(cd), *p_cd.light(3, 5, 6, 8, 9)],
                    [*p_cd.light(12)]], run_time=1.0)
        self.beat(0.3)

        # a MoviePy clip slots in beside it
        icon = VGroup(RoundedRectangle(corner_radius=0.05, width=0.42, height=0.3, stroke_color=INK, stroke_width=2),
                      Triangle(color=INK, fill_opacity=1, stroke_width=0).scale(0.07).rotate(-PI / 2)).arrange(
            ORIGIN, buff=0)
        icon[1].move_to(icon[0])
        chip = VGroup(RoundedRectangle(corner_radius=0.1, width=2.9, height=0.6, fill_color=PANEL, fill_opacity=1,
                                       stroke_color=LINE, stroke_width=1.5), icon,
                      T("a MoviePy clip", 22, INK))
        icon.move_to(chip[0].get_left() + RIGHT * 0.4)
        chip[2].move_to(chip[0].get_left() + RIGHT * 0.8, aligned_edge=LEFT)
        works = T("also a frames segment", 20, MUTED)
        row = VGroup(chip, works).arrange(RIGHT, buff=0.3)
        row.move_to([AT6[0] - W6 / 2 + row.width / 2, -2.75, 0])
        self.say("If you use MoviePy, a MoviePy clip works as a frames segment too.",
                 FadeIn(chip, shift=LEFT * 0.5), FadeIn(works), run_time=1.0)
        self.beat(0.3)

        # effects: the vignette on the interview
        self.steps("And effects change every frame of a segment. This one darkens the corners of the interview a "
                   "little, so the eye stays on her.",
                   [[FadeOut(Group(cd, row)), FadeIn(talk), FadeOut(p_cd), FadeIn(p_vig)],
                    [FadeIn(mask), *p_vig.light(4)]], run_time=1.0)
        self.beat(0.4)

        # naming it: JSON and Python
        p_json = lit(code(IN_JSON, "edits/tour.json", PX + UP * 1.05), 2)
        p_py = lit(code(IN_PY, "edits/tour.py", PX + DOWN * 1.35), 1)
        self.steps("In JSON you name the function as the file and its name, separated by a colon. In Python, you "
                   "pass the function itself.",
                   [[FadeOut(p_vig), FadeIn(p_json)], [FadeIn(p_py)]], run_time=1.0)
        self.beat(0.3)
        result_from(self, "r07", talk)

        # the mistake
        m = Mistake("return rgb[::2]", "return rgb   # the frame it was given", SAID["effect"][0], w=5.6, size=22)
        m.move_to([3.7, 0.1, 0])
        bad = T("854 x 240", 22, ERROR)
        good = T("854 x 480", 22, OK)
        bad.next_to(talk, DOWN, buff=0.2).align_to(talk, LEFT)
        good.move_to(bad, aligned_edge=LEFT)
        wrong_box = Rectangle(width=W6, height=H6 / 2, stroke_color=ERROR, stroke_width=5).move_to(
            AT6 + UP * H6 / 4).set_z_index(8)
        right_box = Rectangle(width=W6, height=H6, stroke_color=OK, stroke_width=5).move_to(AT6).set_z_index(8)
        self.steps("The mistake is an effect that changes the frame's size. It must give back a frame the same "
                   "size, or the render stops and says so.",
                   [[FadeOut(Group(p_json, p_py)), *m.wrong_in(),
                     Create(wrong_box), FadeIn(bad)],
                    m.struck(),
                    [*m.fixed(), ReplacementTransform(wrong_box, right_box), FadeOut(bad), FadeIn(good)]],
                   run_time=1.1)
        self.beat(1.0)

        self.say("So when no file has the picture, your own code can draw it.",
                 FadeOut(Group(m, good, stack, right_box)), FadeIn(cd0), run_time=1.0)
        nxt = VGroup(T("next", 22, MUTED), T("Sound", 30, INK, weight=BOLD)).arrange(
            DOWN, buff=0.1, aligned_edge=RIGHT).move_to([6.2, -3.0, 0], aligned_edge=RIGHT).set_z_index(12)
        self.say("Next, sound.", blur_in(nxt), run_time=0.8)
        self.beat(0.8)
        self.play(*[FadeOut(m) for m in self.stage()], run_time=0.8)
        self.beat(0.4)
