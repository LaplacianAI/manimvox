import json
from pathlib import Path

from PIL import Image

from manimvox.kit import *
from manimvox.scenes import box_on, screenshot

ROOT = Path(__file__).resolve().parents[1]
SHOT = ROOT / "research/assets/Firefox_157.0_opening_Wikipedia_article_on_Linux_screenshot.png"  # 1600 x 974
TOP = (0, 0, 1600, 640)      # the window without its lower half: wide enough to fill the frame
STRIP = (6, 3, 1046, 115)    # the toolbar rows, cut to the pixels that are the window (a black corner sits at 0, 0)
UP_K = 1.8                   # the strip is resampled this much before it is shown, so it stays sharp


def credit_line():
    """The recorded credit, without its long URL, as the licence asks it to be shown."""
    rec = json.loads((ROOT / "research/assets.json").read_text())["assets"][0]
    return ("Screenshot: Exploraz, \"Firefox 157.0 opening Wikipedia article on Linux screenshot\" (2026), "
            f"Wikimedia Commons, {rec['licence_detected']}. Firefox: Mozilla Foundation. Page: Wikimedia Foundation.")


def crops():
    """The two pictures the episode shows, cut from the one screenshot (written under build/, not committed)."""
    out = ROOT / "build"
    out.mkdir(exist_ok=True)
    img = Image.open(SHOT).convert("RGB")
    img.crop(TOP).save(out / "top.png")
    strip = img.crop(STRIP)
    strip.resize((round(strip.width * UP_K), round(strip.height * UP_K)), Image.Resampling.LANCZOS).save(out / "strip.png")
    return out / "top.png", out / "strip.png"


class Ep01(Episode):
    EP = 1
    TITLE = "Which site am I on?"
    TAGLINE = "Reading the top of a browser window"
    NCHAP = 1
    CHROME = ()

    def build(self):
        top_png, strip_png = crops()
        window = screenshot(top_png, width=12.0).move_to([0, -0.85, 0])
        frame = SurroundingRectangle(window, buff=0, color=LINE, stroke_width=1.5)
        both = Group(window, frame)
        credit = T(credit_line(), 13, MUTED, max_w=12.6).move_to([0, STAGE_BOTTOM + 0.1, 0])
        self.play(FadeIn(both), FadeIn(credit), run_time=0.8)
        Q = "Which part of this window shows which site you are on?"
        self.intro(Q, card=False, question=Q)

        # the toolbar rows, lifted out of the window and shown larger (pixels of the strip as resampled)
        small = screenshot(strip_png, width=(STRIP[2] - STRIP[0]) / TOP[2] * 12.0)
        small.move_to(window.at((STRIP[0] + STRIP[2]) / 2, (STRIP[1] + STRIP[3]) / 2))

        def at(x, y):
            """A point of the lifted strip, from the pixel of the original screenshot."""
            return small.at((x - STRIP[0]) * UP_K, (y - STRIP[1]) * UP_K)

        self.chapter("The top strip", "Start at the top.", card=False, keep=(both, credit))
        self.add(small)
        self.play(FadeOut(both), small.animate.scale(12.8 / small.width).move_to([0, 0.2, 0]), run_time=1.2)
        tab = leaders([(at(150, 8), "the tab")], side="above", size=28)[0]
        rest = leaders([(at(1000, 99), "the address bar"), (at(413, 96), "the domain"), (at(322, 92), "the shield")],
                       side="below", size=28)
        bar_ring = box_on(small, ((303 - STRIP[0]) * UP_K, (58 - STRIP[1]) * UP_K, 960 * UP_K, 44 * UP_K))
        dom_ring = box_on(small, ((343 - STRIP[0]) * UP_K, (66 - STRIP[1]) * UP_K, 140 * UP_K, 28 * UP_K))
        self.say("The tab shows the page's title, but the page chooses that itself.", tab.grow())
        self.say("The address bar is different. It belongs to the browser, so a page cannot write it.",
                 Create(bar_ring), rest[0].grow())
        self.say("Its domain names the site your browser actually asked for.", FadeOut(bar_ring), Create(dom_ring),
                 rest[1].grow())
        self.say("And the shield says the connection to it is encrypted.", FadeOut(dom_ring), rest[2].grow())

        self.play(FadeOut(Group(small, tab, rest, bar_ring, dom_ring)), FadeIn(both), run_time=1.0)
        self.play(both.animate.scale(0.85).move_to([0, -1.0, 0]), run_time=0.7)
        lit = box_on(window, (303, 58, 960, 44))
        self.play(Create(lit), run_time=0.6)
        self.outro([], "Read the address bar. The domain says which site you are on, and the shield says the connection is encrypted.",
                   answer="The domain in the address bar, and the shield beside it.", keep=[both, lit, credit])
