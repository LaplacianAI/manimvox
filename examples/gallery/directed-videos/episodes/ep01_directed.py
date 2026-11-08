from manimvox.kit import *
from manimvox.scenes import screenshot

SHOTS = "research/screens/"
PAD = 0.3  # silence after each line: the kit's 0.7 s default leaves dead air in a 65 s video


class Ep01(Episode):
    EP = 1
    TITLE = "Directed videos, not templates"
    TAGLINE = "The kit now lets each video choose its own opening, seams and ending"
    NCHAP = 3
    CHROME = ()  # clean frame: no header label, no progress bar

    def shot(self, name, width, at):
        """A real frame from a gallery video, with a hairline border so a light frame sits on the dark ground."""
        clip = screenshot(SHOTS + name, width=width).move_to(at)
        return clip

    def line(self, text, *anims, **kw):
        self.say(text, *anims, pad=PAD, **kw)

    def build(self):
        # Cold open: frame 0 is the problem, two old videos with the same shape, large.
        W, Y = 6.3, -0.5
        pos_a, pos_b = [-3.5, Y, 0], [3.5, Y, 0]
        a_title, a_chap, a_end = (self.shot(f, W, pos_a) for f in ("old-a-title.png", "old-a-chapter.png", "old-a-recap.png"))
        b_title, b_chap, b_end = (self.shot(f, W, pos_b) for f in ("old-b-title.png", "old-b-chapter.png", "old-b-ending.png"))
        rim_a = Rectangle(width=W, height=a_title.height).set_stroke(LINE, 2).move_to(pos_a)
        rim_b = Rectangle(width=W, height=b_title.height).set_stroke(LINE, 2).move_to(pos_b)
        names = VGroup(T("Made by your agent", 18, MUTED).next_to(rim_a, DOWN, buff=0.18),
                       T("Install manimvox and make a video", 18, MUTED).next_to(rim_b, DOWN, buff=0.18))
        self.add(a_title, b_title, rim_a, rim_b, names)
        self.line("Two manimvox videos, on two different subjects.", Indicate(names[0], color=ACCENT),
                  Indicate(names[1], color=ACCENT))
        self.line("The same title card. The same faded number.",
                  FadeOut(a_title), FadeIn(a_chap), FadeOut(b_title), FadeIn(b_chap), run_time=0.5)
        self.line("The same kind of ending.", FadeOut(a_chap), FadeIn(a_end), FadeOut(b_chap), FadeIn(b_end),
                  run_time=0.5)
        self.intro("Pull request thirty-seven lets each video choose its own shape.",
                   card=False)

        # 1 Why: three hard-coded layouts, one large panel. Seam: dive into the old card.
        self.chapter("Why", "Here is why.",
                     transition=zoom_through(a_end, run_time=0.8), number=False, card=False)
        why = code(
            'def intro(self, narration, tts=None, question=None):\n'
            'num = T(f"{self._chap_i:02d}", 150, ACCENT, BOLD).set_opacity(0.16)\n'
            'h = heading("Recap") if recap else None',
            size=24, w=12.8, line_spacing=1.0, dots=False).move_to([0, 0.4, 0])
        caps = [T(t, 30, MUTED) for t in ("the title card", "the faded chapter number", "the recap")]
        for c in caps:
            c.move_to([0, -1.55, 0])
        bar = why.row(0)
        self.steps("The kit drew each of these itself, the same way, whatever the subject.",
                   [[FadeIn(why), FadeIn(bar), FadeIn(caps[0])],
                    [bar.animate.move_to(why.row(1)), FadeOut(caps[0]), FadeIn(caps[1])],
                    [bar.animate.move_to(why.row(2)), FadeOut(caps[1]), FadeIn(caps[2])]], pad=PAD)

        # 2 What changed: one call on the left, a real frame on the right, three beats. Seam: red flood off the old code.
        self.chapter("What changed", "Now, each is an option.", transition=flood(why, ERROR, run_time=0.9), number=False, card=False)
        cpos, spos = [-3.9, 0.1, 0], [2.9, 0.1, 0]
        calls = [
            ('self.intro(\n    narration,\n    card=False,\n)', 2),
            ('self.chapter(\n    "Title",\n    card=False,\n    transition=iris(box),\n)', 2),
            ('self.outro(\n    [], narration,\n    answer="...",\n    keep=[shelf],\n)', 3),
        ]
        panels = [code(src, size=24, w=5.4, line_spacing=1.0, dots=False).move_to(cpos) for src, _ in calls]
        bars = [p.row(k) for p, (_, k) in zip(panels, calls)]
        frames = [self.shot(f, 7.3, spos) for f in ("new-open.png", "new-middle.png", "new-ending.png")]
        rim = Rectangle(width=7.3, height=frames[0].height).set_stroke(LINE, 2).move_to(spos)
        src_tag = T("frames from “How a hash map finds a key”, made with this PR", 16, MUTED)
        src_tag.next_to(rim, DOWN, buff=0.18)
        self.line("Now the opening can skip the card: the first frame is the subject.",
                  FadeIn(panels[0]), FadeIn(bars[0]), FadeIn(frames[0]), FadeIn(rim), FadeIn(src_tag))
        self.line("Chapters can skip theirs, and move with a transition.",
                  ReplacementTransform(panels[0], panels[1]), ReplacementTransform(bars[0], bars[1]),
                  FadeOut(frames[0]), FadeIn(frames[1]))
        self.line("And the ending can answer over the opening's picture.",
                  ReplacementTransform(panels[1], panels[2]), ReplacementTransform(bars[1], bars[2]),
                  FadeOut(frames[1]), FadeIn(frames[2]))
        chip_ = chip("defaults unchanged", OK, 22, filled=False).move_to([cpos[0], -2.4, 0])
        self.line("Leave them out, and existing videos render exactly as before.", FadeIn(chip_, shift=UP * 0.2))

        # 3 How agents use it. Seam: an iris closes on the ending frame.
        self.chapter("Direction", "One more change.", transition=iris(frames[2], run_time=0.8), number=False, card=False)
        items = VGroup(*[T(t, 44, INK, BOLD) for t in ("Three storylines, one chosen", "One look, one accent",
                                                       "A transition for every seam", "A list of tells to avoid")])
        items.arrange(DOWN, aligned_edge=LEFT, buff=0.6).move_to([0.6, 0.1, 0])
        rule = Line(items.get_corner(UL) + LEFT * 0.4 + UP * 0.1, items.get_corner(DL) + LEFT * 0.4 + DOWN * 0.1)
        rule.set_stroke(ACCENT, 6)
        self.steps("Before drawing anything, the agent now writes a direction: it weighs three storylines, "
                   "settles on one look, plans every seam, and lists the tells to avoid.",
                   [[GrowFromEdge(rule, UP), words_in(items[0])], [words_in(items[1])], [words_in(items[2])],
                    [words_in(items[3])]], pad=PAD)

        # Ending: the old title card beside the new opening; the answer goes over them.
        old = self.shot("old-a-title.png", 5.6, [-3.1, -1.5, 0])
        new = self.shot("new-open.png", 5.6, [3.1, -1.5, 0])
        rims = VGroup(Rectangle(width=5.6, height=old.height).set_stroke(LINE, 2).move_to(old),
                      Rectangle(width=5.6, height=new.height).set_stroke(LINE, 2).move_to(new))
        lab = VGroup(T("old kit", 16, MUTED).next_to(old, DOWN, buff=0.12),
                     T("with this PR", 16, MUTED).next_to(new, DOWN, buff=0.12))
        self.play(FadeOut(items), FadeOut(rule), FadeIn(old), FadeIn(new), FadeIn(rims), FadeIn(lab), run_time=0.5)
        self.outro([], "Read the direction step, then make yours.",
                   answer="The same kit. Now each video chooses its own shape.",
                   keep=[old, new, rims, lab],
                   end=["Read the direction step", "skills/manimvox-creative/references/direction.md"])
