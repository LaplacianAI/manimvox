from manimvox.kit import *

KEYS = ["kiwi", "lime", "pear", "date", "mango", "peach", "grape", "plum"]
PLUM = 7  # 7401935 mod 8 = 7 (an invented example number)
WORK_Y = -2.15  # where the shelf sits while the chapters work above it
OPEN_Y = -0.4   # the opening's place, and the ending's


def build_shelf():
    """Eight big labelled boxes in a row, with their numbers underneath."""
    cells, nums = [], []
    for k in KEYS:
        b = box(1.45, 1.5, fill=PANEL, stroke=LINE, sw=3)
        cells.append(VGroup(b, T(k, 30, INK, max_w=1.3).move_to(b)))
    row = VGroup(*cells).arrange(RIGHT, buff=0.12)
    for i, c in enumerate(cells):
        nums.append(T(str(i), 22, MUTED).next_to(c, DOWN, buff=0.16))
    return VGroup(row, VGroup(*nums)), cells


def mono(s, size=26, color=INK):
    return T(s, size, color, font=MONO)


def tag(text, size=28, fill=PANEL2, stroke=LINE, w=None):
    t = T(text, size, INK)
    b = box(w or t.width + 0.6, 0.8, fill=fill, stroke=stroke)
    return VGroup(b, t.move_to(b))


class Ep01(Episode):
    EP = 1
    TITLE = "How a hash map finds a key"
    TAGLINE = "Why a dict does not search"
    NCHAP = 3
    CHROME = ()

    def build(self):
        # ---- cold open: the problem happening --------------------------------
        shelf, cells = build_shelf()
        shelf.move_to([0, OPEN_Y, 0])
        eg = note("example data: the keys, values and numbers here are invented")
        frame = box(1.62, 1.67, fill=BG, stroke=ERROR, sw=6, op=0).move_to(cells[0])
        looks = ValueTracker(1)
        counter = always_redraw(lambda: T(f"{int(looks.get_value())} look" + ("" if int(looks.get_value()) == 1 else "s"),
                                          72, ERROR, BOLD).move_to([0, -2.2, 0]))
        self.add(shelf, eg, frame, counter)
        hops = [[frame.animate.move_to(cells[i]), looks.animate.set_value(i + 1),
                 cells[i - 1][0].animate.set_fill(PANEL2, 1)] for i in range(1, PLUM + 1)]
        self.steps("To find plum on this shelf, you check every box, one by one.", hops)
        counter.clear_updaters()
        c2 = T("up to 8 looks. For a thousand boxes: up to 1,000.", 28, ERROR, BOLD).move_to([0, -2.95, 0])
        self.say("Up to eight looks. For a thousand boxes, up to a thousand.", FadeIn(c2, shift=UP * 0.15))

        self.intro("A Python dict does it in one look. How?",
                   question="How does a dict find a key so fast?", card=False)
        self.beat()

        # the shelf moves down so the chapters can work above it
        self.play(FadeOut(c2), FadeOut(eg), FadeOut(frame), FadeOut(counter),
                  *[c[0].animate.set_fill(PANEL, 1) for c in cells],
                  shelf.animate.scale(0.9).move_to([0, WORK_Y, 0]), run_time=0.9)
        target = cells[PLUM][0]
        tx = cells[PLUM].get_center()[0]

        # ---- chapter 1: a key becomes a number (the one card, typed in) --------
        self.chapter("A key becomes a number", transition=iris(cells[PLUM].get_center()), keep=(shelf,),
                     number=False, entrance=blur_in)
        key = tag("plum", 32, w=1.9).move_to([-4.6, 2.0, 0])
        hf = VGroup(box(2.5, 0.8, fill=PANEL, stroke=ACCENT), mono("hash()", 28, ACCENT))
        hf[1].move_to(hf[0])
        hf.move_to([-1.4, 2.0, 0])
        num = T("7401935", 48, INK, BOLD).move_to([2.3, 2.0, 0])
        ex = chip("example number", MUTED, 16).next_to(num, UP, buff=0.18)
        a1, a2 = arrow(key, hf), arrow(hf, num)
        self.steps("Python turns the key into a number, with hash.",
                   [FadeIn(key), [Create(a1), FadeIn(hf)], [Create(a2), FadeIn(num), FadeIn(ex)]])
        calc = VGroup(T("7401935", 52, INK), mono("mod", 36, MUTED), T("8", 52, INK), T("=", 52, MUTED),
                      T("7", 96, ACCENT, BOLD)).arrange(RIGHT, buff=0.35).move_to([-0.6, 0.15, 0])
        calc.shift(RIGHT * (tx - calc[-1].get_center()[0]))
        down = arrow(calc[-1], target, color=ACCENT, sw=5)
        self.steps("Divide by eight, the number of boxes. The remainder, seven, is plum's shelf.",
                   [FadeIn(calc[:3]), FadeIn(calc[3:]), [Create(down), target.animate.set_stroke(ACCENT, 6)]])
        self.beat()

        # ---- chapter 2: jump straight there (no card; the shelf carries it) -----
        self.chapter("Jump straight there", transition=whip(RIGHT), keep=(shelf,), card=False)
        target.set_stroke(LINE, 3)
        d = VGroup(box(3.0, 0.9, fill=CODE_BG, stroke=LINE), mono('d["plum"]', 30))
        d[1].move_to(d[0])
        d.move_to([-4.3, 2.0, 0])
        sumbox = VGroup(box(3.4, 0.9, fill=PANEL, stroke=ACCENT), mono("hash, mod 8", 28, ACCENT))
        sumbox[1].move_to(sumbox[0])
        sumbox.move_to([-0.2, 2.0, 0])
        seven = T("7", 96, ACCENT, BOLD).move_to([tx, 0.6, 0])
        b1, b2 = arrow(d, sumbox), arrow(sumbox, seven, color=ACCENT)
        self.steps("To look up plum, do the same sum. Same key, same shelf.",
                   [FadeIn(d), [Create(b1), FadeIn(sumbox)], [Create(b2), FadeIn(seven)]])
        jump = arrow(seven, target, color=ACCENT, sw=6)
        opts = [T(s, 72, MUTED, BOLD) for s in ("8", "5", "1")]
        val = T("3", 72, ACCENT, BOLD).move_to([tx - 3.0, 0.1, 0])
        egv = chip("example value", MUTED, 16).next_to(val, DOWN, buff=0.15)
        for o in opts:
            o.move_to(val)
        vlink = arrow(target.get_top() + UP * 0.05, val, color=ACCENT, dashed=True, curve=0.3)
        self.steps("Go straight to box seven. One look, however long the shelf.",
                   [[Create(jump), target.animate.set_stroke(ACCENT, 6)], [Create(vlink), slot(opts, val), FadeIn(egv)]])
        self.beat()

        # ---- chapter 3: two keys, one shelf (no card; a flood from the box) -----
        self.chapter("One shelf, two keys", transition=flood(target, ACCENT), keep=(shelf,), card=False)
        target.set_stroke(ACCENT, 6)
        fig = tag("fig", 32, w=1.7, stroke=ACCENT).move_to([tx - 2.3, -0.1, 0])
        plum2 = tag("plum", 32, w=1.9, stroke=ACCENT).move_to([tx, -0.1, 0])
        to_a = arrow(fig.get_bottom(), target.get_top() + LEFT * 0.4, color=ACCENT)
        to_b = arrow(plum2.get_bottom(), target.get_top() + RIGHT * 0.1, color=ACCENT)
        neq = T("fig ≠ plum", 64, INK, BOLD).move_to([-3.0, 1.6, 0])
        hsh = VGroup(T("hashable", 48, ACCENT, BOLD), T("a hash that never changes", 26, MUTED)).arrange(DOWN, buff=0.12)
        hsh.move_to([-3.0, -0.2, 0]).shift(UP * 0.0)
        src = note("Python docs: hashable. Collisions: standard hash table design (external)")
        self.steps("Two keys can land on one shelf. The map keeps both and compares keys to tell them apart. "
                   "A key must be hashable: its hash never changes.",
                   [[FadeIn(fig), Create(to_a), FadeIn(plum2), Create(to_b)], [FadeIn(neq)],
                    accent_word(neq, "≠"), [FadeIn(hsh), FadeIn(src)]])
        self.beat()

        # ---- callback: the opening scene, one look ---------------------------
        self.play(*[FadeOut(m) for m in (fig, plum2, to_a, to_b, neq, hsh, src)], run_time=0.5)
        self.play(shelf.animate.scale(1 / 0.9).move_to([0, OPEN_Y, 0]), run_time=0.9)
        one = T("1 look", 72, ACCENT, BOLD).move_to([0, -2.2, 0])
        self.play(FadeIn(one), run_time=0.5)

        self.outro([], "Next time you read a dict, picture the shelf.",
                   answer="A hash turns the key into a shelf number, so lookup jumps straight there.",
                   end="Your dict is a shelf, and the key is its address.", keep=[shelf, one])
