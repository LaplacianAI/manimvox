from manim import Animation, AnimationGroup, linear

from manimvox.kit import *
from manimvox.scenes import callout, from_video, window
from manimvox.scenes.clip import Zoom

SCREENS = "research/screens/"
W = 9.2
CENTER = UP * -0.5  # clip centre; the window bar and a heading fit above it

# regions in source pixels (1920x1080): the terminal is 96 columns of 20 px and rows of 40 px
PY_CMD = (0, 0, 440, 80)
PY_OUT = (0, 40, 240, 40)
VENV_CMD = (0, 120, 480, 40)
ACT_CMD = (0, 200, 760, 40)
ACT_PROMPT = (0, 280, 180, 40)
PIP_CMD = (0, 40, 780, 40)
PIP_BRACKET = (640, 40, 170, 40)
PIP_DONE = (0, 640, 960, 180)
PIP_MANIMVOX = (300, 760, 290, 40)
DOC_CMD = (0, 0, 520, 40)
DOC_OKS = (0, 40, 700, 240)
DOC_GNANI = (0, 560, 930, 40)
SK_CMD = (200, 0, 1160, 40)
SK_AGENT = (680, 0, 380, 40)
SK_OUT = (1220, 40, 700, 40)
CC_PROMPT = (60, 165, 1500, 90)
CC_TOOLS = (60, 270, 560, 300)
CC_BASH = (90, 512, 460, 40)
CC_MSG = (60, 610, 900, 120)
CC_AUDIO = (380, 655, 250, 40)
WHOLE = (0, 0, 1920, 1080)


class PlayRange(Animation):
    """Plays a recording from t0 to t1 (seconds of the recording) over run_time."""

    def __init__(self, clip, t0, t1, run_time):
        self.t0, self.t1 = t0, t1
        super().__init__(clip, run_time=run_time, rate_func=linear)

    def interpolate_mobject(self, alpha):
        n = len(self.mobject.frames)
        t = self.t0 + alpha * (self.t1 - self.t0)
        self.mobject.show(min(n - 1, int(t * self.mobject.fps)))


class SafeZoom(Zoom):
    """Zoom that keeps the view inside the source: a region touching the edge made the view's offset -1e-13."""

    def interpolate_mobject(self, alpha):
        (x0, y0, w0, h0), (x1, y1, w1, h1) = self.start, self.target
        w = w0 * (w1 / w0) ** alpha
        k = (w - w0) / (w1 - w0) if abs(w1 - w0) > 1e-9 else alpha
        cx = x0 + w0 / 2 + k * (x1 + w1 / 2 - x0 - w0 / 2)
        cy = y0 + h0 / 2 + k * (y1 + h1 / 2 - y0 - h0 / 2)
        h = w * h0 / w0
        sw, sh = self.mobject.space
        self.mobject.view = (min(max(cx - w / 2, 0.0), sw - w), min(max(cy - h / 2, 0.0), sh - h), w, h)
        self.mobject.show(self.mobject.shown)


def rec(name, title=None):
    clip = from_video(SCREENS + name + ".mp4", fps=15, width=W).move_to(CENTER)
    if title is None:
        return Group(clip), clip
    return Group(window(clip, title=title), clip), clip


class Ep01(Episode):
    EP = 1
    TITLE = "Install manimvox and make a video"
    TAGLINE = "From an empty folder to a narrated video, with Claude Code"
    NCHAP = 2

    def show(self, text, clip, a, b, zoom=None, tz=None, tag=None, where=None, at=None, side="down"):
        """Narrate `text` while the recording plays its seconds a to b at real speed (faster only when the
        line is shorter). At recording time `tz` zoom into `zoom`; once the recording reaches `at`, when the
        thing pointed at is on screen, point at `where` with a callout."""
        with self.narrate(text) as dur:
            k = max(1.0, (b - a) / dur)
            pos = [0.0]

            def ct(s):
                return a + min(b - a, k * s)

            def run(span, *extra):
                if span < 0.05:
                    return
                s = pos[0]
                self.play(AnimationGroup(PlayRange(clip, ct(s), ct(s + span), span), *extra), run_time=span)
                pos[0] = s + span

            def until(t):  # play on until the recording shows second t
                run(min(dur, (t - a) / k) - pos[0])

            if zoom:
                until(a if tz is None else tz)
                run(1.1, SafeZoom(clip, clip.framing(*zoom), run_time=1.1))
            if tag:
                until(a if at is None else at)
                if dur - pos[0] > 1.3:
                    ov = callout(clip, where, tag, side=side, gap=0.55).set_z_index(10)  # above the clip, which each play() lifts
                    run(0.4, FadeIn(ov))
                    run(dur - pos[0] - 0.35)
                    run(0.35, FadeOut(ov))
            run(dur - pos[0])

    def build(self):
        # cold open: the whole job in one sentence
        prompt = code("Make a short video, about a minute,\nexplaining how UPI payments work.", size=26,
                      title="a real prompt to Claude Code").move_to(LEFT * 3.0 + UP * 0.2)
        result = card("ep01_upi.mp4", ["narrated video", "1 min 19 s"], w=3.6, color=ACCENT).move_to(RIGHT * 4.5 + UP * 0.2)
        link = arrow(prompt, result, color=ACCENT)
        self.steps("One plain sentence, and a narrated video comes back.", [Create(prompt), [Create(link), FadeIn(result)]])
        self.intro("Here is how to set that up, from an empty folder, with real commands.",
                   question="How do you go from nothing to a narrated video?")

        # ---- chapter 1
        self.chapter("Install in a clean environment")
        h1 = heading("1  Check Python, make an environment")
        g1, c1 = rec("venv", "Terminal  ·  Windows Command Prompt")
        self.play(FadeIn(Group(h1, g1)), run_time=0.8)
        self.show("Check Python. Three point eleven or newer; this is three point twelve.", c1, 0, 3.2,
                  PY_CMD, 0, "3.12 is new enough", PY_OUT, 2.5, "down")
        self.show("Make a virtual environment: a private folder for this project's packages.", c1, 3.2, 8.0,
                  VENV_CMD, 3.2, "a private folder: .venv", VENV_CMD, 4.5, "down")
        self.show("Activate it. The dot venv prefix shows it is on.", c1, 8.0, 12.1,
                  ACT_CMD, 8.0, "environment is on", ACT_PROMPT, 10.8, "right")

        h2 = heading("2  Install manimvox from PyPI")
        g2, c2 = rec("install", "Terminal  ·  Windows Command Prompt")
        self.play(FadeOut(Group(h1, g1)), FadeIn(Group(h2, g2)), run_time=0.8)
        self.show("Install manimvox from PyPI. The brackets add Kokoro, the default offline voice.", c2, 0, 4.6,
                  PIP_CMD, 0, "the default voice", PIP_BRACKET, 3.7, "down")
        self.show("Pip fetches forty-eight packages. It took seventy-eight seconds here, so the video skips the waiting.",
                  c2, 4.6, 21.0, WHOLE, 4.6)
        self.show("It ends with Successfully installed, and manimvox zero point four point zero.", c2, 21.0, 26.4,
                  PIP_DONE, 21.0, "manimvox 0.4.0", PIP_MANIMVOX, 25.2, "down")

        h3 = heading("3  Check the setup with doctor")
        g3, c3 = rec("doctor", "Terminal  ·  Windows Command Prompt")
        self.play(FadeOut(Group(h2, g2)), FadeIn(Group(h3, g3)), run_time=0.8)
        self.show("Run manimvox doctor. It checks your setup and names the fix for anything missing.", c3, 0, 4.4,
                  DOC_CMD, 0, "the setup check", DOC_CMD, 3.0, "down")
        self.show("Everything you need says ok. Dashes are optional extras.", c3, 4.4, 5.6,
                  DOC_OKS, 4.4, "all ok", DOC_OKS, 4.6, "right")
        self.show("Gnani, our narration voice, is ok because an API key is set.", c3, 5.6, 6.1,
                  DOC_GNANI, 5.6, "voice gnani: ok", DOC_GNANI, 5.7, "down")

        h4 = heading("4  Give Claude Code the skills")
        g4, c4 = rec("skills", "Terminal  ·  Windows Command Prompt")
        self.play(FadeOut(Group(h3, g3)), FadeIn(Group(h4, g4)), run_time=0.8)
        self.show("Last, install the skills for Claude Code. They teach it how to make a video.", c4, 0, 5.4,
                  SK_CMD, 0, "name the agent", SK_AGENT, 4.6, "down")
        self.show("Eleven skills, copied into this project's dot claude folder.", c4, 5.4, 8.2,
                  SK_OUT, 6.6, "11 skills", SK_OUT, 6.9, "down")

        # takeaway: the four commands
        self.play(FadeOut(Group(h4, g4)), run_time=0.6)
        nodes, arrows = flow(["python -m venv", "pip install", "manimvox doctor", "skills install"], w=2.5, color=ACCENT)
        nodes.move_to(STAGE_CENTER)
        arrows.set_z_index(-1)
        self.steps("So: one environment, one install, one check, one skills command.",
                   [FadeIn(nodes[0]), [Create(arrows[0]), FadeIn(nodes[1])], [Create(arrows[1]), FadeIn(nodes[2])],
                    [Create(arrows[2]), FadeIn(nodes[3])]])
        self.beat()

        # ---- chapter 2
        self.say("But what do you ask Claude Code?", FadeOut(VGroup(nodes, arrows)))
        self.chapter("Ask Claude Code")
        h5 = heading("5  A real Claude Code run")
        c5 = from_video(SCREENS + "claude-code.mp4", fps=15, width=W).move_to(CENTER)
        g5 = Group(h5, c5)
        self.play(FadeIn(g5), run_time=0.8)
        self.show("Open Claude Code in that folder and ask in plain words. This real run asked for a one-minute UPI video.",
                  c5, 0, 4.4, None, None, "the whole request", CC_PROMPT, 4.0, "down")
        self.show("It loaded the manimvox skill, searched the web, read files, and ran eight shell commands.",
                  c5, 4.4, 14.9, CC_TOOLS, 4.4, "8 shell commands", CC_BASH, 6.8, "right")
        self.show("A hundred eighty-three seconds later, it reports the video is rendered: one minute nineteen, audio check ok.",
                  c5, 14.9, 29.0, CC_MSG, 14.9, "audio check: ok", CC_AUDIO, 20.0, "down")
        self.play(SafeZoom(c5, c5.whole, run_time=1.0))
        self.beat(1.5)
        self.play(FadeOut(g5), run_time=0.6)

        self.outro([], "To try it yourself, start at the manimvox docs install page.",
                   next_label="TRY", next_title="laplacianai.github.io/manimvox/install",
                   answer="Install in a clean environment, check it, add the skills, and ask Claude Code.")
