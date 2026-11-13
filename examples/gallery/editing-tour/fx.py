"""The edit's code hooks, named in edits/tour.json as "fx.py:name": an effect on every frame of a clip, a segment
made by code, and graphics drawn over the picture each frame."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from manimvox.edit import frames
from manimvox.edit.timeline import Clock

W, H = 1920, 1080
INK, ACCENT, BG = (230, 238, 242), (79, 195, 201), (14, 24, 34)


def _font(size):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default(size)


_VIG: dict = {}


def vignette(rgb, t):
    """Darken the corners a little, so the eye stays on the speaker: an effect, run on every frame."""
    h, w = rgb.shape[:2]
    if (h, w) not in _VIG:
        y, x = np.ogrid[-1:1:h * 1j, -1:1:w * 1j]
        _VIG[(h, w)] = (1 - 0.35 * np.clip(np.hypot(x, y * 0.8) - 0.45, 0, None) ** 1.5)[..., None]
    return (rgb * _VIG[(h, w)]).astype(np.uint8)


def countdown():
    """3, 2, 1: a segment made by code, frame by frame, each number with a ring that sweeps round."""
    big = _font(260)

    def draw(t):
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        n = 3 - int(t // 0.8)
        k = (t % 0.8) / 0.8
        box = (W / 2 - 230, H / 2 - 230, W / 2 + 230, H / 2 + 230)
        d.ellipse(box, outline=(54, 80, 95), width=10)
        d.arc(box, -90, -90 + 360 * k, fill=ACCENT, width=14)
        d.text((W / 2, H / 2), str(max(1, n)), font=big, fill=INK, anchor="mm")
        return img

    return frames(draw, 2.4)


RAMP = [(31.0, 1.0), (32.0, 0.3), (35.5, 0.3), (36.5, 1.0)]  # the demolition's speed keyframes, as in the edit


def speed_meter(t):
    """A small gauge of the playback speed, drawn each frame over the ramped demolition: graphics by code."""
    clock = Clock(29.0, 40.0, tuple(RAMP))  # the demolition clip's own time, as the renderer keeps it
    v = float(clock.rate(clock.source(t)))
    img = Image.new("RGBA", (520, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, 519, 119), radius=18, fill=(*BG, 200))
    d.text((24, 22), "speed", font=_font(30), fill=(147, 167, 180, 255))
    d.rounded_rectangle((24, 70, 496, 92), radius=11, fill=(54, 80, 95, 255))
    d.rounded_rectangle((24, 70, 24 + max(22, 472 * v), 92), radius=11, fill=(*ACCENT, 255))
    d.text((496, 22), f"{v:.2f}x", font=_font(34), fill=(*INK, 255), anchor="ra")
    return img
