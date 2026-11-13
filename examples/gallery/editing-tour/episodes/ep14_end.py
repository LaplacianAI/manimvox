"""The ending: the four recordings of the opening return, each turns into its fixed version as its lines in the
edit file light, the whole file is read top to bottom and lit, and the end card. The tiles and spans are ep01's.
Script: episodes/tour.md."""
from bench import *

FILE = """\
{
  "captions": "burn",
  "segments": [
    {"clip": "interview.webm",
     "from_words": "Can you briefly",
     "cut_silences": 0.5},
    {"clip": "demolition.webm",
     "start": 29, "end": 40,
     "speed": [[31, 1], [32, 0.3], …],
     "stabilize": {"smooth": 2}},
    {"image": "build/mountain.png",
     "seconds": 5},
    {"multicam": ["street-wide.webm",
                  "street-close.webm"],
     "cuts": [[12, 1], [17, 0], [20.5, 1]]},
    …
  ],
  "overlays": [
    {"clip": "green-screen.ogv",
     "key": "auto"}
  ],
  "audio": [
    {"say": "Here are four real recordings…"},
    {"music": "build/pad.wav"}
  ]
}"""


def tile(mob, text, size=22):
    """A label laid on the bottom left of a grid tile, on a dark band so it reads over any footage (ep01's)."""
    t = T(text, size, INK)
    band = BackgroundRectangle(t, color=BG, fill_opacity=0.82, buff=0.12)
    g = VGroup(band, t)
    g.move_to(mob.get_corner(DL) + UR * 0.1, aligned_edge=DL)
    return g


class Light(Animation):
    """Light lines of an EditPanel (the rest dim), from whatever it shows now. Built to run later, in order: several
    of the panel's own `.light()` lists made up front all end up showing the last one."""

    def __init__(self, edit, ks, dim=0.32, **kw):
        super().__init__(edit, **kw)
        self.edit, self.ks, self.dim = edit, set(ks), dim

    def begin(self):
        self.before = list(getattr(self.edit, "level", [1.0] * len(self.edit.rows)))
        self.after = [1.0 if k in self.ks else self.dim for k in range(len(self.before))]
        super().begin()

    def interpolate_mobject(self, alpha):
        lvl = [a + (b - a) * alpha for a, b in zip(self.before, self.after, strict=True)]
        for row, bar, v in zip(self.edit.rows, self.edit.bars, lvl, strict=True):
            row.set_opacity(v)
            bar.set_fill(opacity=0.18 * max(0.0, (v - self.dim) / (1 - self.dim)))
        self.edit.level = lvl

    def clean_up_from_scene(self, scene):
        super().clean_up_from_scene(scene)
        self.edit.level = self.after


class Ep14(Bench):
    EP = 14
    TITLE = "Back to the four recordings"

    def build(self):
        # the opening's grid, the same tiles and spans as ep01
        w = 5.6
        talk = footage(INTERVIEW, 12.5, 23.0, w)
        shake = footage(DEMOLITION, 12.0, 28.0, w)
        green = footage(CHROMA, 72.0, 77.0, w)
        wide = footage(CAMERAS[0], 8.0, 16.0, w / 2 - 0.05)
        close = footage(CAMERAS[1], 8.0, 16.0, w / 2 - 0.05)
        street = Group(wide, close).arrange(RIGHT, buff=0.1)
        grid = Group(talk, shake, green, street).arrange_in_grid(2, 2, buff=(0.3, 0.3)).move_to(UP * 0.05)
        street.match_y(green)
        for m in (talk, shake, green, wide, close):
            m.clip.loop()
        labels = VGroup(tile(talk, "long pauses, and an “um”"), tile(shake, "a shaking hand"),
                        tile(green, "a green sheet, no mountain"), tile(street, "two cameras, one moment"))

        self.say("That's every tool in the box.", FadeIn(grid), FadeIn(labels), run_time=1.0)
        self.say("Back to the four recordings.", run_time=0.5)
        self.beat(0.8)

        # the grid steps left; the edit file arrives beside it
        edit = EditPanel(FILE, "edits/results.json", size=15, w=6.0, step=0.215).move_to([3.55, 0.0, 0])
        edit.hide()
        edit.level = [0.0] * len(edit.rows)
        cell = Group(talk, shake, green, street)
        self.play(FadeOut(labels), cell.animate.scale(0.6).move_to([-3.2, 0.0, 0]), FadeIn(edit.bg),
                  FadeIn(edit.head), run_time=1.2)
        self.play(Light(edit, []), run_time=0.5)

        def lines(a, b):
            k = edit.find(a)
            return list(range(k, edit.find(b, k) + 1))

        cw = talk.width
        new = {}

        def swap(old, name, text, key_lines, win=None):
            fixed = result(name, w=cw) if win is None else win
            fixed.move_to(old.get_center())
            fixed.clip.loop()
            new[name] = fixed
            tag = tile(fixed, text, 17)
            return [[FadeOut(old), FadeIn(fixed), FadeIn(tag), Light(edit, key_lines)]], tag

        for m in (talk, shake, green, wide, close):
            m.clip.clear_updaters()
        steps, tags = [], []
        for old, name, text, ks in [
                (talk, "captioned", "cut by its words, captioned", lines('"clip": "interview', '"cut_silences"')),
                (shake, "fixed_fall", "held steady, slowed as it falls", lines('"clip": "demolition', '"stabilize"')),
                (green, "keyed", "now a mountain", lines('"image"', '"seconds"') + lines('"overlays"', '"key"')),
                (street, "cameras", "cut between two cameras", lines('"multicam"', '"cuts"'))]:
            s, tag = swap(old, name, text, ks)
            steps += s
            tags.append(tag)
        self.steps("The interview, cut by its words and captioned. The demolition, held steady and slowed as it "
                   "falls. The green sheet, now a mountain. The street, cut between two cameras.", steps,
                   run_time=0.9)
        self.beat(0.6)

        self.steps("How do you fix all four, and make one film of them, with a text file? You write what each "
                   "piece is, and manimvox does the rest.",
                   [Light(edit, lines('"segments"', '"overlays"')[:-1]), Light(edit, lines('"overlays"', '"key"')),
                    Light(edit, lines('"audio"', '"music"'))], run_time=0.9)
        self.say("Every fix in this film is in that one file. Its source, and a guide to every field, are on the manimvox "
                 "site.", Light(edit, range(len(edit.lines))), run_time=1.2)
        self.beat(1.0)

        for f in new.values():
            f.clip.clear_updaters()
        made = VGroup(T("Made end to end by an AI agent, with manimvox", 34, INK, weight=BOLD),
                      T("the explainers · the voice · the edit · every fix", 24, MUTED)).arrange(DOWN, buff=0.35)
        self.say("And every part of it, the explainers, the voice, the cuts and the fixes, was made by an AI agent "
                 "with manimvox. This is manimvox, explaining itself.",
                 FadeOut(edit), FadeOut(Group(*new.values())), FadeOut(VGroup(*tags)), FadeIn(made), run_time=1.4)
        self.beat(1.0)

        card = VGroup(T("Editing your own footage", 54, INK, weight=BOLD),
                      T("laplacianai.github.io/manimvox/editing", 34, ACCENT)).arrange(DOWN, buff=0.45)
        self.say("Read Editing your own footage next, and try one tool on a recording of your own.",
                 FadeOut(made), FadeIn(card), run_time=1.4)
        self.beat(1.5)
