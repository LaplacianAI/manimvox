"""Episode: title card, chapters, narration in step with the picture, recap; subtitles and layout snapshots."""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

from manim import (
    BOLD,
    DOWN,
    LEFT,
    ORIGIN,
    RIGHT,
    UL,
    UP,
    Circle,
    Create,
    Dot,
    FadeIn,
    FadeOut,
    GrowFromCenter,
    GrowFromEdge,
    Indicate,
    LaggedStart,
    Line,
    ManimColor,
    MarkupText,
    Paragraph,
    ReplacementTransform,
    Scene,
    SVGMobject,
    Text,
    Transform,
    VGroup,
    config,
    interpolate_color,
    smooth,
)

from ..voice import VoiceError, spoken_form, synth_cached
from ._context import NOTTS, PROJECT, STEM, THEME, VOICE
from .colours import ACCENT, BG, INK, LINE, MUTED, PANEL, TEAL
from .components import box, bullets, heading
from .text import STAGE_BOTTOM, STAGE_TOP, P, T

config.background_color = BG
WORDS_PER_SECOND = 2.6
STAGE = [-6.6, STAGE_BOTTOM, 6.6, STAGE_TOP]


def _require_words(spoken):
    if not spoken.strip():
        raise VoiceError("empty narration line: every say/steps/narrate needs words to speak")


def _srt_time(t):
    ms = round(t * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


# ------------------------------------------------------------------ episode
class Episode(Scene):
    EP = 0
    TITLE = ""
    TAGLINE = ""
    NCHAP = 1
    SERIES = PROJECT.series if PROJECT else "Explained"  # as written: a brand may forbid capitals

    def construct(self):
        self._subs = []
        self._chap_i = 0
        self._chrome = []
        self._chap_label = None
        self._bar = None
        self._frames = []
        self.build()
        self._write_srt()
        self._write_layout()

    def build(self):
        raise NotImplementedError

    # -- narration ---------------------------------------------------------
    @contextmanager
    def narrate(self, text, tts=None, pad=0.3):
        """Play the voice line; animations inside the block run over it.
        On exit, waits until the line (plus `pad`) has finished."""
        spoken = spoken_form(tts or text, PROJECT.pron if PROJECT else [])
        _require_words(spoken)
        if NOTTS:
            path, dur = None, max(1.4, len(spoken.split()) / WORDS_PER_SECOND)
        else:
            speed = PROJECT.speed if PROJECT else 1.0
            cache = PROJECT.cache_dir if PROJECT else Path(".manimvox/tts")
            path, dur = synth_cached(VOICE, spoken, speed, cache)
        t0 = self.time
        if path is not None:
            # Not self.add_sound(): Manim silently drops a sound added right after an animation it
            # served from its cache (skip_animations stays set until the next play), which loses
            # whole narration lines on any re-render. The file writer has no such check.
            mgr = self._get_manager()
            mgr.file_writer.add_sound(str(path), mgr.time)
        yield dur
        self._subs.append((t0, t0 + dur, text))
        rest = dur + pad - (self.time - t0)
        if rest > 2 / config.frame_rate:
            self.wait(rest)
        self._snapshot()

    def say(self, text, *anims, run_time=1.0, tts=None, pad=0.3, lag_ratio=0.0):
        """Voice line + animations played together at its start."""
        with self.narrate(text, tts=tts, pad=pad) as dur:
            if anims:
                rt = min(run_time, max(0.4, dur))
                if lag_ratio:
                    self.play(LaggedStart(*anims, lag_ratio=lag_ratio), run_time=rt)
                else:
                    self.play(*anims, run_time=rt)

    def steps(self, text, anims, run_time=0.7, tts=None, pad=0.3, lead=0.0):
        """Voice line with `anims` spread evenly across it. Each item is an
        Animation or a list of Animations played together."""
        with self.narrate(text, tts=tts, pad=pad) as dur:
            if lead:
                self.wait(lead)
            slot = max(0.3, (dur - lead) / max(1, len(anims)))
            for a in anims:
                group = a if isinstance(a, (list, tuple)) else [a]
                rt = min(run_time, slot)
                self.play(*group, run_time=rt)
                if slot - rt > 2 / config.frame_rate:
                    self.wait(slot - rt)

    # -- structure ---------------------------------------------------------
    def stage(self):
        """Everything on screen except the header and progress bar."""
        chrome = set(map(id, self._chrome))
        return [m for m in self.mobjects if id(m) not in chrome]

    def clear(self, shift=LEFT * 0.7, run_time=0.55):
        """Transition: sweep the stage away."""
        mobs = self.stage()
        if mobs:
            self.play(*[FadeOut(m, shift=shift) for m in mobs], run_time=run_time)

    def intro(self, narration, tts=None):
        """Title card, then it settles into the persistent header."""
        series = T(self.SERIES, 20, ACCENT, BOLD)
        epno = T(f"EPISODE {self.EP:02d}", 20, MUTED, BOLD)
        top = VGroup(series, Dot(radius=0.04, color=MUTED), epno).arrange(RIGHT, buff=0.22)
        # With a mark on the right (left edge x≈2.8), the text block must stop short of it.
        wide = 8.4 if THEME.mark_svg else 11.5
        title = P(self.TITLE, 62, INK, max_w=wide, weight=BOLD)
        rule = Line(LEFT * 1.2, RIGHT * 1.2).set_stroke(ACCENT, 6)
        tag = P(self.TAGLINE, 26, MUTED, max_w=min(wide, 10.5))
        g = VGroup(top, title, rule, tag).arrange(DOWN, aligned_edge=LEFT, buff=0.38)
        g.move_to(ORIGIN).set_x(-6.0 + g.width / 2)
        motif = self.motif()
        with self.narrate(narration, tts=tts):
            self.play(Create(motif), FadeIn(top, shift=RIGHT * 0.4), run_time=0.8)
            self.play(FadeIn(title, shift=UP * 0.3), GrowFromEdge(rule, LEFT), run_time=0.9)
            self.play(FadeIn(tag, shift=UP * 0.2), run_time=0.6)
        # persistent chrome
        label = T(f"EP {self.EP:02d}  ·  {self.TITLE}", 15, MUTED, BOLD, max_w=7.5)
        label.move_to([-6.75 + label.width / 2, 3.72, 0])
        track = Line([-7.2, -3.93, 0], [7.2, -3.93, 0]).set_stroke(LINE, 5)
        bar = Line([-7.2, -3.93, 0], [-7.15, -3.93, 0]).set_stroke(ACCENT, 5)
        self.play(FadeOut(VGroup(title, rule, tag, motif), shift=LEFT * 0.6),
                  ReplacementTransform(top, label), FadeIn(track), FadeIn(bar), run_time=0.8)
        self._chrome = [label, track, bar]
        self._bar = bar

    def motif(self):
        """The title card's decoration, bottom right. The project's own mark when
        series.json gives one (theme.mark_svg, drawn in the accent), else two rings."""
        svg = THEME.mark_svg
        if svg:
            m = SVGMobject(str(PROJECT.root / svg))
            # A solid tint, not a translucent accent: edges must not show through a node.
            tint = interpolate_color(ManimColor(BG), ManimColor(ACCENT), 0.42)
            for part in m.family_members_with_points():
                filled = part.get_fill_opacity() > 0  # read before recolouring: an outline stays an outline
                part.set_fill(tint, 1 if filled else 0).set_stroke(tint, 0 if filled else 3)
            return m.scale_to_fit_height(4.2).move_to([4.9, -1.4, 0])
        ring1 = Circle(radius=3.4).set_stroke(ACCENT, 2, 0.14).move_to([5.6, -2.2, 0])
        ring2 = Circle(radius=2.2).set_stroke(TEAL, 2, 0.12).move_to([5.6, -2.2, 0])
        return VGroup(ring1, ring2)

    def chapter(self, title, narration=None, tts=None):
        """Transition into a new chapter: big title, then it docks top-right."""
        self.clear()
        self._chap_i += 1
        num = T(f"{self._chap_i:02d}", 150, ACCENT, BOLD).set_opacity(0.16)
        ttl = P(title, 52, INK, max_w=10.5, weight=BOLD, align="center")
        rule = Line(LEFT * 0.9, RIGHT * 0.9).set_stroke(ACCENT, 6).next_to(ttl, DOWN, buff=0.35)
        num.next_to(ttl, UP, buff=0.1)
        VGroup(num, ttl, rule).move_to(ORIGIN)
        anims = [FadeIn(num, scale=1.3), FadeIn(ttl, shift=UP * 0.35), GrowFromCenter(rule)]
        if narration:
            self.say(narration, *anims, run_time=0.8, tts=tts)
        else:
            self.play(*anims, run_time=0.8)
            self.wait(0.7)
        dock = T(f"{self._chap_i:02d}  {title}", 15, ACCENT, BOLD, max_w=5.5)
        dock.move_to([6.75 - dock.width / 2, 3.72, 0])
        frac = min(1.0, self._chap_i / max(1, self.NCHAP))
        new_bar = Line([-7.2, -3.93, 0], [-7.2 + 14.4 * frac, -3.93, 0]).set_stroke(ACCENT, 5)
        outs = [FadeOut(num), FadeOut(rule), ReplacementTransform(ttl, dock)]
        if self._chap_label is not None:
            outs.append(FadeOut(self._chap_label))
            self._chrome.remove(self._chap_label)
        if self._bar is not None:
            outs.append(Transform(self._bar, new_bar))
        self.play(*outs, run_time=0.7)
        self._chap_label = dock
        self._chrome.append(dock)

    def outro(self, recap, narration, next_title=None, tts=None, next_label="NEXT"):
        """Recap bullets and a pointer to the next episode. The last episode can
        point elsewhere instead: next_label="READ", next_title="docs/design.md"."""
        self.clear()
        h = heading("Recap")
        rows = bullets(recap, size=25, max_w=11.5)
        rows.next_to(h, DOWN, aligned_edge=LEFT, buff=0.5)
        group = [FadeIn(h, shift=DOWN * 0.2)] + [FadeIn(r, shift=RIGHT * 0.3) for r in rows]
        extra = None
        if next_title:
            extra = VGroup(T(next_label, 16, ACCENT, BOLD), T(next_title, 26, INK, BOLD, max_w=11)).arrange(RIGHT, buff=0.3)
            plate = box(extra.width + 0.7, extra.height + 0.5, fill=PANEL, stroke=ACCENT)
            extra = VGroup(plate, extra.move_to(plate)).move_to([0, STAGE_BOTTOM + 0.55, 0])
            group.append(FadeIn(extra, shift=UP * 0.3))
        # Wrapped bullets can run into the plate: shrink them into the space above it.
        floor = (extra.get_top()[1] if extra is not None else STAGE_BOTTOM) + 0.3
        room = rows.get_top()[1] - floor
        if rows.height > room:
            top_left = rows.get_corner(UL)
            rows.scale(room / rows.height, about_point=top_left)
        self.steps(narration, group, tts=tts)
        self.wait(0.8)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)

    # -- small helpers -----------------------------------------------------
    def swap(self, old, new, run_time=0.7):
        """Cross-fade one mobject into another at the same place."""
        self.play(FadeOut(old, shift=UP * 0.2), FadeIn(new, shift=UP * 0.2), run_time=run_time)

    def dim(self, *mobs, opacity=0.25, run_time=0.4):
        self.play(*[m.animate.set_opacity(opacity) for m in mobs], run_time=run_time)

    def pulse(self, path_mobs, color=ACCENT, run_time=1.6):
        """Send a glowing dot along a chain of mobjects (centre to centre)."""
        pts = [m.get_center() for m in path_mobs]
        dot = Dot(radius=0.11, color=color).move_to(pts[0])
        halo = Circle(radius=0.2).set_stroke(color, 3, 0.5).move_to(dot)
        halo.add_updater(lambda m: m.move_to(dot))
        self.add(halo, dot)
        seg = run_time / max(1, len(pts) - 1)
        for p, m in zip(pts[1:], path_mobs[1:]):
            self.play(dot.animate.move_to(p), run_time=seg * 0.7, rate_func=smooth)
            self.play(Indicate(m, color=color, scale_factor=1.06), run_time=seg * 0.3)
        halo.clear_updaters()
        self.play(FadeOut(dot), FadeOut(halo), run_time=0.25)

    def _stem(self) -> str:
        return STEM or f"ep{self.EP:02d}"

    def _write_srt(self):
        if NOTTS or PROJECT is None:
            return
        PROJECT.out_dir.mkdir(parents=True, exist_ok=True)
        lines = [f"{i}\n{_srt_time(a)} --> {_srt_time(b)}\n{text}\n" for i, (a, b, text) in enumerate(self._subs, 1)]
        (PROJECT.out_dir / f"{self._stem()}.srt").write_text("\n".join(lines), encoding="utf-8")

    def _snapshot(self):
        """Record every visible text box on the stage (header and progress bar excluded) for check_layout."""
        texts = []
        for top in self.stage():
            family = top.get_family()
            in_par = {id(c) for m in family if isinstance(m, Paragraph) for c in m.get_family() if c is not m}
            for m in family:
                if not isinstance(m, (Text, MarkupText, Paragraph)) or id(m) in in_par:
                    continue
                if m.get_fill_opacity() <= 0.05 or not m.family_members_with_points():  # glyph points live in submobjects
                    continue
                if isinstance(m, Paragraph):
                    if hasattr(m, "lines_text"):
                        raw = getattr(m.lines_text, "original_text", None) or m.lines_text.text
                    else:
                        raw = "paragraph"
                else:
                    raw = getattr(m, "original_text", None) or m.text
                label = " ".join(raw.split())
                box = (m.get_left()[0], m.get_bottom()[1], m.get_right()[0], m.get_top()[1])
                texts.append({"text": label, "box": [round(float(v), 3) for v in box]})
        self._frames.append({"t": round(self.time, 2), "texts": texts})

    def _write_layout(self):
        if PROJECT is None:
            return
        d = PROJECT.build_dir / self._stem()
        d.mkdir(parents=True, exist_ok=True)
        (d / "layout.json").write_text(json.dumps({"stage": STAGE, "frames": self._frames}), encoding="utf-8")
