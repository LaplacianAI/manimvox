"""The repair bench every chapter is drawn on (DIRECTION.md): the raw clip on the left, the edit file on the right
with the line being explained lit, a terminal for commands, the mistake struck through with the fix under it, and
before and after side by side. Every terminal line and error shown is real output, kept by capture.py in
build/said.json; every result shown is a window of out/results.mp4 (make_edit.py results), listed in
build/windows.json."""
import json
import textwrap
from pathlib import Path

import numpy as np

from manimvox.kit import *
from manimvox.post.audio import RATE, read_audio
from manimvox.scenes import from_video, screenshot

HERE = Path(__file__).parent
SAID = json.loads((HERE / "build" / "said.json").read_text())
WINDOWS = json.loads((HERE / "build" / "windows.json").read_text())

INTERVIEW = "research/assets/Interview_Prof_Joyeeta_Gupta_on_strengthening_water_governance_education_and_research.webm"
DEMOLITION = "research/assets/Dundee_Alexander_Street_Hilltown_Multis_Demolition_2011.webm"
CHROMA = "research/assets/Chroma_key_demonstration.ogv"
CAMERAS = ["research/assets/Urilift,_Göteborg,_Kungsportsplatsen_-_angle_1.webm",
           "research/assets/Urilift,_Göteborg,_Kungsportsplatsen_-_angle_2.webm"]
RESULTS = "out/results.mp4"
SHORT = {INTERVIEW: "interview.webm", DEMOLITION: "demolition.webm", CHROMA: "green-screen.ogv",
         CAMERAS[0]: "street-wide.webm", CAMERAS[1]: "street-close.webm"}

FW = 14.222  # the frame's width in scene units
CLIP_W = 7.2  # the raw clip: 55% of the safe width
CLIP_AT = np.array([-3.0, -0.2, 0])
PANEL_W = 5.5
PANEL_AT = np.array([3.55, -0.2, 0])


def short(text: str) -> str:
    """Long footage paths written as the short names the film calls them by."""
    for path, name in SHORT.items():
        text = text.replace(path, name).replace(Path(path).name, name)
    return text


# ---------------------------------------------------------------- footage

def footage(path, start, end, w=CLIP_W, fps=15):
    """A recording on the bench, silent (the voice is always the loudest thing), in a thin frame."""
    clip = from_video(HERE / path, fps=fps, start=start, end=end, width=w)
    frame = SurroundingRectangle(clip, color=LINE, buff=0, stroke_width=2)
    g = Group(clip, frame)
    g.clip = clip
    return g


def result(name, w=CLIP_W, fps=15, start=0.0, end=None):
    """A fix as rendered: its window of out/results.mp4, from `start` seconds into the window."""
    a, b = WINDOWS[name]
    return footage(RESULTS, a + start, b if end is None else a + end, w, fps)


def picture(path, w=CLIP_W):
    """A still (a PNG in build/) in the same thin frame."""
    clip = screenshot(HERE / path, width=w)
    g = Group(clip, SurroundingRectangle(clip, color=LINE, buff=0, stroke_width=2))
    g.clip = clip
    return g


def caption(text, mob, size=24, color=MUTED, buff=0.18, direction=DOWN):
    return T(text, size, color).next_to(mob, direction, buff=buff).align_to(mob, LEFT)


def full(mob):
    """The animation that grows a clip to fill the frame: the seam into the result, which plays full frame next."""
    return mob.animate.scale(FW / mob.width).move_to(ORIGIN)


# ---------------------------------------------------------------- the edit file

def _char_w(size):
    return Text("M" * 20, font=MONO, font_size=size).width / 20


class EditPanel(VGroup):
    """The edit file on the bench. `light(k, ...)` dims every other line and lays the accent behind those."""

    def __init__(self, src, title="edits/tour.json", size=20, w=PANEL_W, step=None):
        super().__init__()
        lines = textwrap.dedent(src).strip("\n").split("\n")
        cw = _char_w(size)
        step = step or size * 0.021
        longest = max(len(line) for line in lines)
        scale = min(1.0, (w - 0.7) / (longest * cw)) if longest else 1.0
        cw, step = cw * scale, step * max(scale, 0.8)
        h = len(lines) * step + 1.0
        self.bg = RoundedRectangle(corner_radius=0.14, width=w, height=h, fill_color=PANEL, fill_opacity=1,
                                   stroke_color=LINE, stroke_width=1.5)
        self.head = T(title, 18, MUTED, font=MONO).move_to(self.bg.get_corner(UL) + RIGHT * 0.32 + DOWN * 0.3,
                                                          aligned_edge=LEFT)
        x0 = self.bg.get_left()[0] + 0.35
        y0 = self.bg.get_top()[1] - 0.8
        self.bars, self.rows = VGroup(), VGroup()
        for k, line in enumerate(lines):
            y = y0 - k * step
            bar = Rectangle(width=w - 0.16, height=step * 0.98, stroke_width=0, fill_color=ACCENT, fill_opacity=0)
            bar.move_to([self.bg.get_center()[0], y, 0])
            self.bars.add(bar)
            body = line.strip()
            if body:
                row = Text(body, font=MONO, font_size=size, color=INK, disable_ligatures=True).scale(scale)
                row.move_to([x0 + (len(line) - len(line.lstrip())) * cw, y, 0], aligned_edge=LEFT)
            else:
                row = VectorizedPoint([x0, y, 0])
            self.rows.add(row)
        self.add(self.bg, self.bars, self.head, self.rows)
        self.lines = lines

    def find(self, text, after=0):
        """The index of the first line (from `after`) that contains `text`."""
        for k in range(after, len(self.lines)):
            if text in self.lines[k]:
                return k
        raise ValueError(f"no line with {text!r}")

    def light(self, *ks, dim=0.32):
        """Light the lines `ks` (indices, or text found in them); dim the rest. Each call is its own animation,
        reading the panel as it is when it starts, so several can be built ahead and played in turn."""
        ks = {self.find(k) if isinstance(k, str) else k for k in ks}
        return [_Lit(self, [(1.0 if k in ks else dim, 0.18 if k in ks else 0.0) for k in range(len(self.rows))])]

    def plain(self):
        """Every line at full ink, nothing lit."""
        return [_Lit(self, [(1.0, 0.0)] * len(self.rows))]

    def typed(self, *ks):
        """Lines typed in, letter by letter (they start hidden: call hide() first)."""
        ks = [self.find(k) if isinstance(k, str) else k for k in ks]
        return [AddTextLetterByLetter(self.rows[k], time_per_char=0.02) for k in ks if isinstance(self.rows[k], Text)]

    def hide(self, *ks):
        for k in ks or range(len(self.rows)):
            self.rows[self.find(k) if isinstance(k, str) else k].set_opacity(0)
        return self


class _Lit(Animation):
    """Each line of an EditPanel from its opacity (and its bar's) when the animation starts to `targets`:
    [(line opacity, bar opacity)], one per line. Not built on .animate, whose one target per mobject is shared:
    built ahead, every such animation would play the last one's target."""

    def __init__(self, panel, targets, run_time=0.6, **kwargs):
        self.panel, self.targets = panel, targets
        super().__init__(panel, run_time=run_time, **kwargs)

    def begin(self):
        self.start = [(r.get_fill_opacity() if r.has_points() or r.submobjects else 0.0, b.get_fill_opacity())
                      for r, b in zip(self.panel.rows, self.panel.bars, strict=True)]
        super().begin()

    def interpolate_mobject(self, alpha):
        a = self.rate_func(alpha)
        for (r, b), (r0, b0), (r1, b1) in zip(zip(self.panel.rows, self.panel.bars, strict=True), self.start,
                                              self.targets, strict=True):
            r.set_opacity(r0 + (r1 - r0) * a)
            b.set_fill(opacity=b0 + (b1 - b0) * a)


# ---------------------------------------------------------------- terminal

class Terminal(VGroup):
    """A terminal: the command after a muted $, then what manimvox printed, wrapped to the panel."""

    def __init__(self, cmd, out=(), w=PANEL_W, size=17, keep=8):
        super().__init__()
        cw = _char_w(size)
        chars = max(20, int((w - 0.6) / cw))
        wrapped = []
        for line in out:
            wrapped += textwrap.wrap(short(line), chars, subsequent_indent="  ", break_on_hyphens=False) or [""]
        wrapped = wrapped[:keep]
        cmd_lines = textwrap.wrap(short(cmd), chars - 2, subsequent_indent="  ", break_on_hyphens=False)
        step = size * 0.021
        n = len(cmd_lines) + len(wrapped)
        self.bg = RoundedRectangle(corner_radius=0.14, width=w, height=n * step + 0.7, fill_color=CODE_BG,
                                   fill_opacity=1, stroke_color=LINE, stroke_width=1.5)
        x0, y0 = self.bg.get_left()[0] + 0.3, self.bg.get_top()[1] - 0.35 - step / 2
        self.cmd = VGroup()
        for k, line in enumerate(cmd_lines):
            text = ("$ " if k == 0 else "  ") + line
            row = Text(text, font=MONO, font_size=size, color=INK, disable_ligatures=True,
                       t2c={"$ ": MUTED} if k == 0 else {})
            self.cmd.add(row.move_to([x0, y0 - k * step, 0], aligned_edge=LEFT))
        self.out = VGroup()
        for k, line in enumerate(wrapped):
            y = y0 - (len(cmd_lines) + k) * step
            row = Text(line, font=MONO, font_size=size, color=MUTED, disable_ligatures=True) if line.strip() \
                else VectorizedPoint([x0, y, 0])
            self.out.add(row.move_to([x0, y, 0], aligned_edge=LEFT))
        self.add(self.bg, self.cmd, self.out)

    def run(self):
        """Animations: the panel, then the command typed, then the output printed line by line."""
        return [FadeIn(self.bg), *[AddTextLetterByLetter(r, time_per_char=0.015) for r in self.cmd],
                LaggedStart(*[FadeIn(r) for r in self.out], lag_ratio=0.25)]


# ---------------------------------------------------------------- the mistake

class Mistake(VGroup):
    """The wrong line struck through in the error colour, what manimvox says about it, and the fix under it."""

    def __init__(self, wrong, right, note=None, w=PANEL_W + 1.0, size=22):
        super().__init__()
        self.wrong = Text(wrong, font=MONO, font_size=size, color=ERROR, disable_ligatures=True)
        if self.wrong.width > w:
            self.wrong.scale_to_fit_width(w)
        self.strike = Line(self.wrong.get_left() + LEFT * 0.08, self.wrong.get_right() + RIGHT * 0.08,
                           color=ERROR, stroke_width=4)
        parts = [VGroup(self.wrong, self.strike)]
        self.note = None
        if note:
            self.note = P(short(note), 19, MUTED, max_w=w, font=MONO)
            parts.append(self.note)
        self.right = Text(right, font=MONO, font_size=size, color=OK, disable_ligatures=True)
        if self.right.width > w:
            self.right.scale_to_fit_width(w)
        parts.append(self.right)
        VGroup(*parts).arrange(DOWN, buff=0.38, aligned_edge=LEFT)
        self.add(*parts)

    def wrong_in(self):
        return [AddTextLetterByLetter(self.wrong, time_per_char=0.02)]

    def struck(self):
        return [Create(self.strike)] + ([FadeIn(self.note)] if self.note else [])

    def fixed(self):
        return [AddTextLetterByLetter(self.right, time_per_char=0.02)]


# ---------------------------------------------------------------- before and after

def before_after(before, after, labels=("before", "after"), w=6.4):
    """Two equal halves, labelled once."""
    for m in (before, after):
        m.scale_to_fit_width(w)
    pair = Group(before, after).arrange(RIGHT, buff=0.3).move_to(DOWN * 0.15)
    tags = VGroup(caption(labels[0], before, 24, MUTED, direction=UP), caption(labels[1], after, 24, MUTED,
                                                                                 direction=UP))
    return pair, tags


# ---------------------------------------------------------------- sound, drawn

def loudness(path, start, end, n=160):
    """The recording's loudness from `start` to `end` seconds, as `n` values from 0 to 1."""
    x = read_audio(HERE / path)
    x = np.abs(x.mean(axis=0)[int(start * RATE):int(end * RATE)])
    bins = np.array_split(x, n)
    v = np.array([np.sqrt(np.mean(b ** 2)) if b.size else 0.0 for b in bins])
    return v / (v.max() or 1.0)


def wave(values, w, h, color=MUTED, stroke=3):
    """Loudness drawn as a row of vertical strokes, `w` wide and up to `h` tall."""
    n = len(values)
    g = VGroup(*[Line(UP * max(0.02, v) * h / 2, DOWN * max(0.02, v) * h / 2, color=color, stroke_width=stroke)
                 .move_to(RIGHT * (k + 0.5) * w / n) for k, v in enumerate(values)])
    return g.move_to(ORIGIN)


# ---------------------------------------------------------------- the episode

class Bench(Episode):
    """An explainer on the bench: no header or progress bar (the bench is the chapter's own frame)."""
    CHROME = ()
    NCHAP = 1

    def show_result(self, name, lead=None):
        """Play the chapter's fix full frame from out/results.mp4, with the sound the edit mixed for it (its
        narration, footage and effects), then come back to the bench as it was. `lead`, a clip on the bench, grows
        to fill the frame first, so the result arrives out of it."""
        a, b = WINDOWS[name]
        clip = from_video(HERE / RESULTS, fps=30, start=a, end=b, width=FW, sound=True).move_to(ORIGIN)
        ground = getattr(self, "_ground", None)
        others = [m for m in self.stage() if m is not lead and m is not ground]
        if lead is not None:
            home = (lead.width, lead.get_center())  # not save_state: a Group holding an image cannot restore
            self.play(full(lead), *[FadeOut(m) for m in others], run_time=0.8)
        else:
            self.play(*[FadeOut(m) for m in others], run_time=0.5)
        self.play(FadeIn(clip), run_time=0.25)
        if lead is not None:
            self.remove(lead)
        self.play(clip.play())
        back = [FadeIn(m) for m in others]
        if lead is not None:
            lead.scale(home[0] / lead.width).move_to(home[1])
            back.append(FadeIn(lead))
        self.play(FadeOut(clip), *back, run_time=0.7)

    def heading(self, text, how="words"):
        """The chapter's name, top left, arriving one of several ways; it holds still once it lands."""
        t = T(text, 40, INK, weight=BOLD).to_corner(UL, buff=0.5)
        enter = {"words": lambda: words_in(t), "letters": lambda: letters_in(t), "blur": lambda: blur_in(t),
                 "write": lambda: AddTextLetterByLetter(t, time_per_char=0.04)}[how]()
        return t, enter
