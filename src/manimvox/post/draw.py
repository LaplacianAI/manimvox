"""Pictures post draws with pycairo in the theme's font and colours: caption plates and full-frame cards."""
from __future__ import annotations

import math
from dataclasses import dataclass

import cairo
import numpy as np

from .._cairo import hex_rgb, surface_rgba, wrap


@dataclass(frozen=True)
class Overlay:
    """A caption plate: its RGBA pixels and the frame position of their top-left corner."""

    x: int
    y: int
    rgba: np.ndarray

    def blend(self, frame: np.ndarray) -> None:
        """Draw onto an (h, w, 3) uint8 frame, in place."""
        h, w = self.rgba.shape[:2]
        region = frame[self.y:self.y + h, self.x:self.x + w]
        a = self.rgba[:region.shape[0], :region.shape[1], 3:4].astype(np.float32) / 255.0
        src = self.rgba[:region.shape[0], :region.shape[1], :3]
        region[:] = (region * (1.0 - a) + src * a + 0.5).astype(np.uint8)


def _face(ctx: cairo.Context, theme, bold: bool = False) -> None:
    ctx.select_font_face(theme.font, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)


def _rounded(ctx: cairo.Context, w: float, h: float, r: float) -> None:
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(w - r, r, r, -math.pi / 2, 0)
    ctx.arc(w - r, h - r, r, 0, math.pi / 2)
    ctx.arc(r, h - r, r, math.pi / 2, math.pi)
    ctx.arc(r, r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def caption_overlay(text: str, frame_w: int, frame_h: int, theme) -> Overlay:
    """One subtitle as a plate centred near the bottom of the frame, wrapped to two lines where it fits."""
    max_w = 0.8 * frame_w
    probe = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    _face(probe, theme)
    words = " ".join(str(text).split())
    size = frame_h * 0.034
    while True:
        probe.set_font_size(size)
        lines = wrap(probe, words, max_w) or [""]
        widest = max(probe.text_extents(s).x_advance for s in lines)
        if (len(lines) <= 2 and widest <= max_w) or size <= frame_h * 0.022:
            break
        size *= 0.92
    ascent, _descent, line_h = probe.font_extents()[:3]
    pad = round(size * 0.45)
    pw = max(1, int(min(frame_w, widest + 2 * pad)))
    ph = max(1, int(min(frame_h, len(lines) * line_h + 2 * pad)))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, pw, ph)
    ctx = cairo.Context(surf)
    _rounded(ctx, pw, ph, size * 0.4)
    ctx.set_source_rgba(*hex_rgb(theme["bg"]), 0.82)
    ctx.fill()
    _face(ctx, theme)
    ctx.set_font_size(size)
    ctx.set_source_rgb(*hex_rgb(theme["ink"]))
    for i, s in enumerate(lines):
        ctx.move_to((pw - ctx.text_extents(s).x_advance) / 2, pad + ascent + i * line_h)
        ctx.show_text(s)
    x = (frame_w - pw) // 2
    y = min(frame_h - ph, max(0, int(frame_h * 0.925) - ph))
    return Overlay(x, y, surface_rgba(surf))


def card_image(title: str | None, lines, w: int, h: int, theme) -> np.ndarray:
    """A full frame on the theme's background: a bold title over an accent rule, then the lines in muted text."""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(*hex_rgb(theme["bg"]))
    ctx.paint()
    rows = []  # (text, size, colour, bold)
    if title:
        rows.append((title, h * 0.062, theme["ink"], True))
    rows += [(s, h * 0.036, theme["muted"] if title else theme["ink"], False) for s in lines]
    rule_gap = h * 0.05 if title else 0.0
    total = sum(r[1] * 1.5 for r in rows) + rule_gap
    y = (h - total) / 2
    for i, (text, size, colour, bold) in enumerate(rows):
        _face(ctx, theme, bold)
        ctx.set_font_size(size)
        tw = ctx.text_extents(text).x_advance
        if tw > 0.86 * w:
            size *= 0.86 * w / tw
            ctx.set_font_size(size)
            tw = ctx.text_extents(text).x_advance
        y += size * 1.5
        ctx.set_source_rgb(*hex_rgb(colour))
        ctx.move_to((w - tw) / 2, y - size * 0.4)
        ctx.show_text(text)
        if i == 0 and title:
            ctx.set_source_rgb(*hex_rgb(theme["accent"]))
            ctx.set_line_width(max(1.0, h * 0.006))
            ctx.move_to(w * 0.44, y + rule_gap * 0.35)
            ctx.line_to(w * 0.56, y + rule_gap * 0.35)
            ctx.stroke()
            y += rule_gap
    return np.ascontiguousarray(surface_rgba(surf)[..., :3])
