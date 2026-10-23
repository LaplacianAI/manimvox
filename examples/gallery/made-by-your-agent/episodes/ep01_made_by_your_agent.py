from pathlib import Path

import av

from manimvox.kit import *
from manimvox.scenes import from_frames

HEART = Path(__file__).resolve().parents[1] / "research" / "inside-the-heart.mp4"
EXTERNAL = "External sources: Anthropic, Code execution with MCP (2025) · Cloudflare, Code Mode (2025) · Wang et al., CodeAct, ICML 2024"


def heart_clip(start=56.5, seconds=6.0, fps=15, width=7.2):
    """A few seconds of the Inside the heart video, as a clip that plays inside this one."""
    frames, want = [], [start + i / fps for i in range(int(seconds * fps))]
    with av.open(str(HEART)) as c:
        st = c.streams.video[0]
        for f in c.decode(st):
            while want and float(f.pts * st.time_base) >= want[0]:
                frames.append(f.to_image().resize((1280, 720)))
                want.pop(0)
            if not want:
                break
    return from_frames(lambda t: frames[min(len(frames) - 1, int(t * fps))], seconds, fps, width)


def quote(source, text, color=SOURCE):
    """A cited claim: the source as a chip, the words beside it."""
    tag = chip(source, color=color, size=16)
    words = P(text, 24, INK, max_w=8.4)
    return VGroup(tag, words).arrange(RIGHT, buff=0.35, aligned_edge=UP)


class Ep01(Episode):
    EP = 1
    TITLE = "Made by your agent"
    TAGLINE = "Explainer videos made by your AI agent"
    NCHAP = 3

    def build(self):
        self.intro("What if you could ask your coding agent for an explainer video, and get one, with every claim cited?",
                   question="What if your agent could make the explainer video?")

        # 1 -- what manimvox is
        self.chapter("What manimvox is", "First, what manimvox is.")
        h = heading("manimvox", sub="An open-source library and command line for explainer videos")
        parts = VGroup(
            card("Picture", "Manim draws every frame", w=3.7, color=BLUE),
            card("Voice", "text-to-speech narration, with subtitles", w=3.7, color=VIOLET),
            card("Checks", "contrast, layout and silence, before it ships", w=3.7, color=OK),
        ).arrange(RIGHT, buff=0.45).move_to(UP * 0.35)
        self.say("manimvox is an open-source library and command line for narrated, animated explainer videos.",
                 FadeIn(h, shift=DOWN * 0.2))
        self.steps("Manim draws the picture, a voice tells the story, and checks catch mistakes before a video ships.",
                   [FadeIn(c, shift=UP * 0.2) for c in parts])
        agent = node("Your agent", sub="+ 11 manimvox skills", w=3.6, color=AGENT, size=24)
        kinds = VGroup(*[chip(k, color=ACCENT, size=18) for k in ("a paper", "an idea", "a codebase", "a pull request")])
        kinds.arrange(RIGHT, buff=0.45)
        VGroup(agent, kinds).arrange(DOWN, buff=0.75).move_to(DOWN * 1.75)  # lays the two rows out together
        hub = agent.get_bottom() + DOWN * 0.05
        links = VGroup(*[arrow(hub, k.get_top() + UP * 0.04, color=LINE, buff=0.0, sw=2.4) for k in kinds])
        self.play(parts.animate.scale(0.82).shift(UP * 0.55), run_time=0.6)
        self.say("It is built for AI agents: eleven skills teach an agent to make a video from a paper, an idea, a codebase or a pull request.",
                 FadeIn(agent, shift=UP * 0.2), LaggedStart(*[Create(a) for a in links], lag_ratio=0.15),
                 LaggedStart(*[FadeIn(k) for k in kinds], lag_ratio=0.15))
        self.beat(0.6)

        # 2 -- why code, not tools
        self.chapter("Why code, not tools", "Why build it this way?")
        h2 = heading("Why code, not tools?")
        q1 = quote("Anthropic, 2025", "“LLMs are adept at writing code and developers should take advantage of this strength.”")
        q2 = quote("Cloudflare, 2025", "“LLMs are better at writing code to call MCP, than at calling MCP directly.”")
        q3 = VGroup(chip("CodeAct, ICML 2024", color=SOURCE, size=16),
                    VGroup(T("up to 20%", 40, ACCENT, BOLD), P("higher success when agents act through Python code, across 17 models", 22, INK, max_w=6.2))
                    .arrange(RIGHT, buff=0.35)).arrange(RIGHT, buff=0.35)
        rows = VGroup(q1, q2, q3).arrange(DOWN, buff=0.55, aligned_edge=LEFT).move_to(DOWN * 0.15)
        col = max(r[0].get_right()[0] for r in rows) + 0.35  # the quotes start in one column, whatever the chip's width
        for r in rows:
            r[0].align_to([col - 0.35, 0, 0], RIGHT)
            r[1].align_to([col, 0, 0], LEFT)
        src = note(EXTERNAL)
        self.say("Why give an agent a library, and not a list of tools?", FadeIn(h2, shift=DOWN * 0.2), FadeIn(src))
        self.say("Anthropic's engineers write that language models are adept at writing code.", FadeIn(q1, shift=RIGHT * 0.2))
        self.say("Cloudflare found that models are better at writing code that calls tools than at calling the tools directly.",
                 FadeIn(q2, shift=RIGHT * 0.2))
        self.say("And the CodeAct study found that agents acting through Python code succeed up to twenty percent more often.",
                 FadeIn(q3, shift=RIGHT * 0.2))
        snippet = code('class Ep01(Episode):\n    def build(self):\n        heart = heart_cut_open()\n        self.say("Four chambers appear.", FadeIn(heart))',
                       size=19, title="episodes/ep01_heart.py")
        verbs = VGroup(*[chip(v, color=AGENT, size=18, filled=True) for v in ("writes", "checks", "fixes")]).arrange(RIGHT, buff=0.35)
        video = VGroup(snippet, verbs).arrange(DOWN, buff=0.4).move_to(DOWN * 0.2)
        self.swap(rows, video)
        self.say("So every manimvox video is code: code the agent writes, checks and fixes.",
                 LaggedStart(*[FadeIn(v, scale=0.9) for v in verbs], lag_ratio=0.3))
        self.beat(0.6)

        # 3 -- how to use it
        self.chapter("How to use it", "Here is how you use it.")
        h3 = heading("Ask your agent")
        term = code('uv tool install "manimvox[kokoro]"\nmanimvox skills install', size=20, title="terminal", w=7.4)
        ask = card("You, to your agent", "“Make an explainer video of the human heart.”", w=7.4, color=AGENT, body_size=22)
        top = VGroup(term, ask).arrange(DOWN, buff=0.4).move_to(UP * 0.55)
        self.say("Install manimvox, then give your coding agent its skills.", FadeIn(h3, shift=DOWN * 0.2), FadeIn(term, shift=UP * 0.2))
        self.say("Then just ask, for example: make an explainer video of the human heart.", FadeIn(ask, shift=UP * 0.2))
        steps, arrows_ = flow(["Sources", "FACTS.md", "Script", "Episode code", "Draft + checks", "Render"], w=1.9, color=ACCENT, size=17)
        line = VGroup(steps, arrows_).move_to(DOWN * 2.25)
        self.steps("The agent gathers sources and writes down the facts, then the script.",
                   [FadeIn(steps[0]), [Create(arrows_[0]), FadeIn(steps[1])], [Create(arrows_[1]), FadeIn(steps[2])]])
        self.steps("It writes the episode as Python, drafts it, reads its own checks, and renders.",
                   [[Create(arrows_[2]), FadeIn(steps[3])], [Create(arrows_[3]), FadeIn(steps[4])],
                    [Create(arrows_[4]), FadeIn(steps[5])]])
        clip = heart_clip().move_to(UP * 0.1)
        frame = SurroundingRectangle(clip, buff=0.06, color=LINE, stroke_width=2, corner_radius=0.08)
        credit = note("Inside the heart · made by Claude Code with manimvox · heart from CT: Rodero et al. 2021, CC BY 4.0")
        self.play(FadeOut(top), FadeOut(h3), line.animate.scale(0.85).move_to(DOWN * 2.85), run_time=0.6)
        self.add(clip)
        with self.narrate("This heart video was made exactly that way, from three prompts.") as dur:
            self.play(FadeIn(clip), Create(frame), FadeIn(credit), run_time=0.5)
            self.play(clip.play(), run_time=max(1.0, dur - 0.5))
        self.beat(0.5)

        self.outro(["Built for AI agents: eleven skills, four kinds of video",
                    "Every video is code the agent writes, checks and fixes",
                    "Sources and facts first, then the script, then the render"],
                   "Ask your agent. manimvox gives it the rest.",
                   answer="Ask your agent. It writes the video as code, cites every claim, and checks its own work.")
