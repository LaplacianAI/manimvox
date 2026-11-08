"""The opt-in options that let two videos look unlike: motion helpers, CHROME, chapter and clear options,
end cards, the theme ground, animated post cards and the variety note."""
import json

import numpy as np
import pytest

from manimvox.checks.layout import variety_notes
from manimvox.checks.theme import theme_notes
from manimvox.kit.theme import Theme
from manimvox.post.draw import card_image
from manimvox.post.finish import _card_frames
from tests.test_kit import add_episode, copy_fixture, render_episode, run_py

TH = Theme.from_dict({"source": "test"})


# ------------------------------------------------------------------ fast
def test_ground_is_validated_and_defaults_to_none():
    assert Theme.from_dict({}).ground is None
    assert Theme.from_dict({"ground": {"kind": "grain"}}).ground == {"kind": "grain", "amount": 0.5}
    with pytest.raises(ValueError, match="theme.ground.kind"):
        Theme.from_dict({"ground": {"kind": "marble"}})


def test_ground_pixels_are_deterministic_and_solid_is_flat():
    from manimvox.kit.ground import ground_pixels

    a = ground_pixels("paper", 0.8, "#F4EFE6", "#222222")
    assert a.shape == (1080, 1920, 3) and (a == ground_pixels("paper", 0.8, "#F4EFE6", "#222222")).all()
    assert len(np.unique(ground_pixels("solid", 1.0, "#F4EFE6", "#222222"))) == 3  # the bg colour alone
    assert not (a == ground_pixels("grain", 0.8, "#F4EFE6", "#222222")).all()


def test_light_bg_with_dark_default_panels_is_a_warning():
    (note,) = theme_notes(Theme.from_dict({"bg": "#F4EFE6"}))
    assert "panel, panel2, line" in note
    assert theme_notes(Theme.from_dict({})) == []
    light = {"bg": "#F4EFE6", "panel": "#EAE3D6", "panel2": "#DDD5C5", "line": "#C9BFAB"}
    assert theme_notes(Theme.from_dict(light)) == []


def test_variety_warns_only_when_every_seam_picks_the_same_explicit_transition():
    def seams(*kinds):
        return {"chapters": [{"transition": k} for k in kinds]}

    assert len(variety_notes(seams("blur", "blur", "blur"))) == 1
    assert variety_notes(seams("clear", "clear", "clear")) == []  # never chose: not told off
    assert variety_notes(seams("blur", "blur")) == []
    assert variety_notes(seams("blur", "dip", "blur")) == []
    assert variety_notes({"stage": [], "frames": []}) == []  # a layout.json from before this key


def ink(im):
    return int((np.abs(im.astype(int) - im[0, 0].astype(int)).sum(axis=2) > 30).sum())


def test_card_image_progress_types_and_wipes_and_one_is_the_finished_card():
    done = card_image("The title", ["a line"], 320, 180, TH)
    assert (card_image("The title", ["a line"], 320, 180, TH, progress=1.0) == done).all()
    start = card_image("The title", ["a line"], 320, 180, TH, progress=0.0)
    half = card_image("The title", ["a line"], 320, 180, TH, progress=0.5)
    assert ink(start) == 0 < ink(half) < ink(done)


def test_card_frames_ease_in_then_hold_for_the_same_length():
    frames = list(_card_frames("T", ["x"], 160, 90, TH, 30, 10))
    assert len(frames) == 30
    assert not (frames[0] == frames[-1]).all() and (frames[6] == frames[-1]).all() and (frames[-1] == frames[10]).all()
    assert len(list(_card_frames(None, ["x"], 160, 90, TH, 3, 10))) == 3  # shorter than the animation


def test_words_and_letters_are_found_in_text_and_paragraphs():
    from manimvox.kit import P, T
    from manimvox.kit.motion import _units

    assert [w for w, _ in _units(T("Why does it go cold", 30))] == ["Why", "does", "it", "go", "cold"]
    para = P("one two three four five six seven eight nine ten", 30, max_w=3.5, align="center")
    words = _units(para)
    assert [w for w, _ in words] == ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
    assert all(g for _w, g in words)


def test_motion_helpers_return_animations_and_tag_their_kind():
    from manim import Animation, Circle, Dot

    from manimvox.kit import T, accent_word, carry, dip, flood, iris, morph, slot, whip, words_in, zoom_through

    t, d = T("one two", 30), Dot()
    for anim, kind in [(words_in(t), "words_in"), (accent_word(t, "two"), "accent_word"), (zoom_through(d), "zoom_through"),
                       (flood(d, "#fff"), "flood"), (iris([0, 0, 0]), "iris"), (dip(), "dip"), (morph(d, Circle()), "morph"),
                       (carry(d, [1, 1, 0]), "carry"), (slot([T("a")], T("b")), "slot"), (whip(mobs=[d]), "whip")]:
        assert isinstance(anim, Animation) and anim.mv_kind == kind
    assert callable(whip()) and whip().mv_kind == "whip"  # without mobs: waits for the stage
    with pytest.raises(ValueError, match="not a word"):
        accent_word(t, "three")


def test_defaults_are_the_documented_ones():
    from manimvox.kit import Episode

    assert Episode.CHROME == ("label", "bar")


# ------------------------------------------------------------------ slow: renders
DEFAULTS = '''from manimvox.kit import *


class Ep02(Episode):
    EP = 2
    TITLE = "Same"
    TAGLINE = "Defaults"
    NCHAP = 2

    def build(self):
        self.intro("A short intro.", question="Why?"{intro})
        self.chapter("First", "The first chapter."{chap})
        self.say("A picture.", FadeIn(node("B")))
        self.clear({clear})
        self.chapter("Second", "The second chapter.")
        self.outro(["Two"], "The end.", next_title="Next"{outro})
'''


@pytest.mark.slow
def test_explicit_defaults_render_exactly_as_no_options(tmp_path):
    p = copy_fixture(tmp_path)
    add_episode(p, "ep02_plain", "Ep02", "Same", DEFAULTS.format(intro="", chap="", clear="", outro=""))
    plain = render_episode(p, "ep02_plain", "Ep02", voiced=False)
    add_episode(p, "ep03_same", "Ep02", "Same", DEFAULTS.format(
        intro=", card=True", chap=", transition=None, keep=(), number=True",
        clear='how="left", keep=()', outro=", end=None"))
    named = render_episode(p, "ep03_same", "Ep02", voiced=False)
    assert plain["frames"] == named["frames"] and plain["stage"] == named["stage"]
    assert plain["intro_card"] is True and plain["chapters"] == [{"transition": "clear"}] * 2
    first = {t["text"] for t in plain["frames"][0]["texts"]}
    assert {"Same", "Why?"} <= first  # the card, with its question
    assert any("01" in t["text"] for fr in plain["frames"] for t in fr["texts"])  # the faded numeral


DIRECTED = '''import json
from pathlib import Path

from manimvox.kit import *


class Ep02(Episode):
    EP = 2
    TITLE = "Directed"
    TAGLINE = "Everything opt in"
    NCHAP = 5
    CHROME = ()

    def build(self):
        rec = {}
        subject = node("Cold open subject").move_to(DOWN * 1.5)
        self.add(subject)
        self.intro("Straight in.", question="Why?", card=False)
        rec["subject_kept"] = subject in self.mobjects
        rec["chrome"] = len(self._chrome)
        self.chapter("One", "No numeral, kept thing.", number=False, keep=[subject], transition="blur")
        rec["kept_across_seam"] = subject in self.mobjects
        a = node("A").move_to(LEFT * 3)
        self.say("A.", FadeIn(a))
        self.chapter("Two", "Zoom.", transition=zoom_through(a))
        b = node("B").move_to(RIGHT * 3)
        self.say("B.", FadeIn(b))
        self.chapter("Three", "Flood.", transition=flood(b, ACCENT))
        c = node("C")
        self.say("C.", FadeIn(c))
        self.chapter("Four", "Iris.", transition=iris(c.get_center()))
        self.say("D.", FadeIn(node("D")))
        self.chapter("Five", "Whip.", transition=whip(UP))
        self.say("E.", FadeIn(node("E")))
        self.clear(how="dip")
        self.say("F.", FadeIn(node("F")))
        self.clear(how="down")
        self.say("G.", FadeIn(node("G")))
        self.clear(how="blur")
        rec["stage_after_clears"] = len(self.stage())
        self.outro([], "Ending.", answer="The index.", end=["Read more", "docs", "part two"])
        Path("probe.json").write_text(json.dumps(rec), encoding="utf-8")
'''


@pytest.mark.slow
def test_directed_episode_uses_every_option(tmp_path):
    p = copy_fixture(tmp_path)
    add_episode(p, "ep02_directed", "Ep02", "Directed", DIRECTED)
    layout = render_episode(p, "ep02_directed", "Ep02", voiced=False)
    rec = json.loads((p / "probe.json").read_text(encoding="utf-8"))
    assert rec == {"subject_kept": True, "chrome": 0, "kept_across_seam": True, "stage_after_clears": 0}
    assert layout["intro_card"] is False
    assert [c["transition"] for c in layout["chapters"]] == ["blur", "zoom_through", "flood", "iris", "whip"]
    texts = [{t["text"] for t in fr["texts"]} for fr in layout["frames"]]
    assert {"Cold open subject", "Directed"} <= texts[0]  # the title arrives over the cold open
    shown = set().union(*texts)
    assert "01" not in shown and "02" in shown and "Recap" not in shown  # number=False on the first chapter only
    assert {"Read more", "docs", "part two"} <= texts[-1]


GROUND = '''from manimvox.kit import *


class Ep02(Episode):
    EP = 2
    TITLE = "Paper"
    TAGLINE = "A light ground"
    NCHAP = 1

    def build(self):
        self.intro("On paper.")
        self.chapter("Light", "Ink on paper.")
        self.say("A box.", FadeIn(node("Box")))
        self.clear()
        self.outro([], "Done.")
'''


@pytest.mark.slow
def test_a_light_ground_renders_and_is_never_cleared(tmp_path):
    p = copy_fixture(tmp_path)
    data = json.loads((p / "series.json").read_text(encoding="utf-8"))
    data["theme"] |= {"bg": "#F4EFE6", "ink": "#222222", "muted": "#5A5A5A", "ground": {"kind": "paper", "amount": 0.7}}
    (p / "series.json").write_text(json.dumps(data), encoding="utf-8")
    add_episode(p, "ep02_paper", "Ep02", "Paper", GROUND)
    layout = render_episode(p, "ep02_paper", "Ep02", voiced=False)
    shown = {t["text"] for fr in layout["frames"] for t in fr["texts"]}
    assert {"Paper", "Box"} <= shown
    r = run_py("from manimvox.kit import *; from manimvox.kit.ground import ground_mobject; print(ground_mobject() is not None)", p)
    assert r.stdout.strip() == "True", r.stderr
