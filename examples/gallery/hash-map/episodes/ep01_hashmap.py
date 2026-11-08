import inspect

import numpy as np

from manimvox.kit import *

KEYS = ["kiwi", "lime", "pear", "date", "mango", "peach", "grape", "plum"]
PLUM = 7  # 7401935 = 8 x 925241 + 7 (an invented example number)
WORK_Y = -2.15  # where the shelf sits while the chapters work above it
OPEN_Y = 0.0    # the opening's place, and the ending's
LABEL = 24      # every label on screen is this size; numbers are 44, 72 or 96; notes are 16


def build_shelf():
    """Eight big labelled boxes in a row, with their numbers underneath."""
    cells, nums = [], []
    for k in KEYS:
        b = box(1.55, 1.5, fill=PANEL, stroke=LINE, sw=3)
        cells.append(VGroup(b, T(k, LABEL, INK, max_w=1.35).move_to(b)))
    row = VGroup(*cells).arrange(RIGHT, buff=0.1)
    for i, c in enumerate(cells):
        nums.append(T(str(i), 22, MUTED).next_to(c, DOWN, buff=0.16))
    return VGroup(row, VGroup(*nums)), cells


def mono(s, size=LABEL, color=INK):
    return T(s, size, color, font=MONO)


def tag(text, w=None, stroke=LINE):
    t = T(text, LABEL, INK)
    b = box(w or t.width + 0.6, 0.8, fill=PANEL2, stroke=stroke)
    return VGroup(b, t.move_to(b))


def tick(at, size=0.4):
    """A check mark drawn from two lines, its foot on `at`."""
    a = np.array([at[0], at[1], 0.0])
    return VGroup(Line(a + LEFT * size * 0.5 + UP * size * 0.45, a, stroke_width=7),
                  Line(a, a + RIGHT * size + UP * size * 1.1, stroke_width=7)).set_color(ACCENT)


class Ep01(Episode):
    EP = 1
    TITLE = "How a hash map finds a key"
    TAGLINE = "Why a dict does not search"
    NCHAP = 3
    CHROME = ()
    GAP = 0.3  # silence between lines: the next line follows at once

    def over(self, text, anims, pad=None, rt=0.9):
        """One line of voice with `anims` spread over it. `pre` is a seam that plays during the first moments."""
        with self.narrate(text, pad=self.GAP if pad is None else pad) as dur:
            t0 = self.time
            left = max(0.5, dur - (self.time - t0) - 0.25)
            slot = left / len(anims)
            for a in anims:
                a = a() if inspect.isfunction(a) else a  # built when its turn comes, so it sees the mobjects as they are then
                group = a if isinstance(a, (list, tuple)) else [a]
                run = min(rt, slot)
                self.play(*group, run_time=run)
                if slot - run > 0.05:
                    self.wait(slot - run)

    def build(self):
        # ---- cold open: the problem happening --------------------------------
        shelf, cells = build_shelf()
        shelf.move_to([0, OPEN_Y, 0])
        eg = note("example data: the keys, values and numbers here are invented")
        frame = box(1.7, 1.67, fill=BG, stroke=ERROR, sw=6, op=0).move_to(cells[0])
        looks = ValueTracker(1)
        counter = always_redraw(lambda: T(f"{int(looks.get_value())} look" + ("" if int(looks.get_value()) == 1 else "s"),
                                          72, ERROR, BOLD).move_to([0, OPEN_Y - 1.8, 0]))
        self.add(shelf, eg, frame, counter)
        hops = [[frame.animate.move_to(cells[i]), looks.animate.set_value(i + 1),
                 cells[i - 1][0].animate.set_fill(PANEL2, 1)] for i in range(1, PLUM + 1)]
        with self.narrate("To find plum on this shelf, you check every box, one by one.", pad=self.GAP) as dur:
            slot = max(0.3, (dur - 0.3) / len(hops))
            for h in hops:
                self.play(*h, run_time=min(0.4, slot))
                self.wait(max(0, slot - 0.4))
        counter.clear_updaters()
        c2 = T("up to 8 looks. A thousand boxes: up to 1,000.", 28, ERROR, BOLD).move_to([0, OPEN_Y - 2.5, 0])
        self.over("Up to eight looks. For a thousand boxes, a thousand.", [FadeIn(c2, shift=UP * 0.15)])

        # the title types in over the picture; the picture then makes way for the chapters
        self.intro("A Python dict finds plum in one look. How?",
                   question="How does a dict find a key so fast?", card=False, leave=[c2, eg, frame, counter])
        target = cells[PLUM][0]
        label7 = cells[PLUM][1]
        ref = shelf.copy().scale(0.9).move_to([0, WORK_Y, 0])  # where the shelf will stand, for placing things above it
        tx = ref[0][PLUM].get_center()[0]
        eg = note("example data: the keys, values and numbers here are invented")

        # ---- chapter 1: a key becomes a number (iris from plum's box, no card) --
        key = tag("plum", w=1.9).move_to([-4.6, 2.0, 0])
        hf = VGroup(box(2.5, 0.8, fill=PANEL, stroke=ACCENT), mono("hash()", LABEL, ACCENT))
        hf[1].move_to(hf[0])
        hf.move_to([-1.4, 2.0, 0])
        num = T("7401935", 48, INK, BOLD).move_to([2.3, 2.0, 0])
        a1, a2 = arrow(key, hf), arrow(hf, num)
        self.chapter("A key becomes a number", "First, the key becomes a number.",
                     transition=iris(cells[PLUM].get_center()), keep=(shelf,), card=False)
        self.over("Python's hash does that.",
                  [[*[c[0].animate.set_fill(PANEL, 1) for c in cells], shelf.animate.scale(0.9).move_to([0, WORK_Y, 0]),
                    FadeIn(key)],
                   [Create(a1), FadeIn(hf)], [Create(a2), FadeIn(num), FadeIn(eg)]])
        eq = VGroup(T("7401935", 44, INK), T("=", 44, MUTED), T("8 × 925241", 44, INK), T("+", 44, MUTED),
                    T("7", 96, ACCENT, BOLD)).arrange(RIGHT, buff=0.3).move_to([-0.6, 0.3, 0])
        eq.shift(RIGHT * (tx - eq[-1].get_center()[0]))
        py = mono("in Python:  7401935 % 8  gives  7", 18, MUTED).next_to(eq, DOWN, buff=0.3).align_to(eq, LEFT)
        down = arrow(eq[-1], ref[0][PLUM][0], color=ACCENT, sw=5)
        self.over("Divide by eight, the number of boxes. What's left over, seven, is plum's box.",
                  [[FadeIn(eq[:4]), FadeIn(py)], FadeIn(eq[-1], scale=1.3),
                   [Create(down), target.animate.set_stroke(ACCENT, 6)]])
        stored = T("plum: 3", LABEL, INK, BOLD).move_to(label7)
        self.over("That is where plum lives, with its value.", [Transform(label7, stored)])

        # ---- chapter 2: jump straight there (whip right, no card) ---------------
        eg2 = note("example data: the keys, values and numbers here are invented")
        d = VGroup(box(3.0, 0.9, fill=CODE_BG, stroke=LINE), mono('d["plum"]'))
        d[1].move_to(d[0])
        d.move_to([-4.3, 2.0, 0])
        hf2 = VGroup(box(2.5, 0.8, fill=PANEL, stroke=ACCENT), mono("hash()", LABEL, ACCENT))
        hf2[1].move_to(hf2[0])
        hf2.move_to([-0.8, 2.0, 0])
        seven = T("7", 96, ACCENT, BOLD).move_to([tx, 1.0, 0])
        b1, b2 = arrow(d, hf2), arrow(hf2, seven, color=ACCENT)

        self.chapter("Jump straight there", "Now, look plum up.", transition=whip(RIGHT), keep=(shelf,), card=False)
        target.set_stroke(LINE, 3)
        self.over("Do the same sum. Same key, same box.",
                  [[FadeIn(d), FadeIn(eg2)], [Create(b1), FadeIn(hf2)], [Create(b2), FadeIn(seven)]])
        jump = arrow(seven, target, color=ACCENT, sw=6)
        three = T("3", 96, ACCENT, BOLD).scale(0.3).move_to(target).set_opacity(0)
        self.add(three)
        got = np.array([-4.3, -0.15, 0])
        back = arrow(d.get_bottom(), got + UP * 0.8)
        self.over("Go straight there. The value, three, comes out. One look, however long the shelf.",
                  [[Create(jump), target.animate.set_stroke(ACCENT, 6)],
                   three.animate.set_opacity(1).scale(1 / 0.3).move_to(got),
                   Create(back)], rt=1.2)

        # ---- chapter 3: two keys, one box (flood from the box, no card) ---------
        orig = target.copy()
        fig = tag("fig", w=1.5).move_to([tx - 3.4, 1.0, 0])
        seven3 = T("7", 72, ACCENT, BOLD).move_to([tx, 1.0, 0])
        c_a = arrow(fig, seven3)
        grown = box(target.width, target.height * 1.7, fill=PANEL, stroke=ACCENT, sw=6).align_to(target, DOWN)
        grown.set_x(tx)
        c_b = arrow(seven3, grown, color=ACCENT)
        e_plum = T("plum: 3", LABEL, INK, BOLD).move_to([tx, grown.get_bottom()[1] + 0.42, 0])
        e_fig = T("fig: 5", LABEL, INK, BOLD).move_to([tx, grown.get_top()[1] - 0.42, 0])
        note3 = note("example data. Python docs: a key's hash never changes (hashable)")

        self.chapter("Two keys, one box", "But keys can collide.", transition=flood(target, ACCENT), keep=(shelf,),
                     card=False)
        target.set_stroke(ACCENT, 6)
        self.over("Two keys land in the same box.",
                  [FadeIn(fig), [Create(c_a), FadeIn(seven3)],
                   [Create(c_b), Transform(target, grown), label7.animate.move_to(e_plum),
                    ReplacementTransform(fig, e_fig), FadeIn(note3)]])
        q = VGroup(box(3.0, 0.9, fill=CODE_BG, stroke=LINE), mono('d["plum"]'))
        q[1].move_to(q[0])
        q.move_to([tx - 3.4, 0.6, 0])
        qa = arrow(q.get_bottom(), target.get_top() + LEFT * 0.3, color=ACCENT)
        mark = tick([tx + 1.1, e_plum.get_center()[1] - 0.12])
        self.over("The box keeps both, and checks which key you asked for.",
                  [[FadeOut(c_a), FadeOut(c_b), FadeOut(seven3), FadeIn(q)], Create(qa), Create(mark)])
        q2 = VGroup(box(3.0, 0.9, fill=CODE_BG, stroke=LINE), mono('d["plums"]'))
        q2[1].move_to(q2[0])
        q2.move_to(q)
        box3 = cells[3][0]
        qa2 = arrow(q2.get_bottom(), box3.get_top(), color=ERROR)
        one = T("1 look", 72, ACCENT, BOLD).move_to([0, OPEN_Y - 1.8, 0])
        self.over("That is why a key can not change: its box would move.",
                  [[FadeOut(mark), ReplacementTransform(q, q2), ReplacementTransform(qa, qa2),
                    box3.animate.set_stroke(ERROR, 6)],
                   lambda: [FadeOut(q2), FadeOut(qa2), FadeOut(e_fig), FadeOut(note3), Transform(target, orig),
                            label7.animate.move_to(orig), box3.animate.set_stroke(LINE, 3)],
                   lambda: [shelf.animate.scale(1 / 0.9).move_to([0, OPEN_Y, 0]), FadeIn(one)]], rt=1.1, pad=0)

        self.outro([], "Next time you read a dict, picture the shelf.",
                   answer="A hash turns the key into a shelf number, so lookup jumps straight there.",
                   end="Your dict is a shelf, and the key is its address.", keep=[shelf, one])
