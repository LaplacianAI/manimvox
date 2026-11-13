"""Make what the edit uses besides the footage, into build/: a music bed and a whoosh (synthesised, so nothing to
credit), a badge to lay over the picture, a still of the towers before they fall (one frame of the demolition
footage), a still of the mountain to key the green-screen shoot over (one frame of the same film as the shoot), and
looks/film.cube, a warm film look. Run once before rendering: uv run python make_media.py"""
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

from manimvox.edit.picture import Reader

HERE = Path(__file__).parent
BUILD = HERE / "build"
RATE = 48000
CHROMA = HERE / "research/assets/Chroma_key_demonstration.ogv"
DEMOLITION = HERE / "research/assets/Dundee_Alexander_Street_Hilltown_Multis_Demolition_2011.webm"


def pad(seconds: float = 150) -> np.ndarray:
    """A quiet, slowly moving open chord, spread a little across the stereo field."""
    t = np.arange(round(RATE * seconds)) / RATE
    left, right = np.zeros_like(t), np.zeros_like(t)
    for k, f in enumerate((98.0, 146.83, 196.0, 246.94, 293.66)):  # G2 D3 G3 B3 D4: G major, open
        swell = 0.6 + 0.4 * np.sin(2 * np.pi * t / (11 + 3 * k) + k)
        tone = sum(np.sin(2 * np.pi * f * h * t + k) / h**2 for h in (1, 2, 3))
        left += swell * tone * (0.6 + 0.08 * k)
        right += swell * tone * (0.92 - 0.08 * k)
    x = np.stack([left, right], axis=1)
    return (0.25 * x / np.abs(x).max()).astype(np.float32)


def whoosh(seconds: float = 1.2) -> np.ndarray:
    """Filtered noise that swells and falls away, its pitch sliding down: the sound of time slowing."""
    n = round(RATE * seconds)
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 1, n)
    t = np.arange(n) / n
    out = np.zeros(n)
    y, cut = 0.0, 0.25 - 0.2 * t  # a one-pole low-pass whose cutoff falls
    for i in range(n):
        y += cut[i] * (noise[i] - y)
        out[i] = y
    env = np.sin(np.pi * np.clip(t * 1.4, 0, 1)) ** 2
    x = out * env
    x = 0.5 * x / np.abs(x).max()
    return np.stack([x, x], axis=1).astype(np.float32)


def badge() -> Image.Image:
    """A small rounded badge with the version, like a channel's mark in a corner."""
    img = Image.new("RGBA", (420, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, 419, 119), radius=26, fill=(14, 24, 34, 210), outline=(79, 195, 201, 255), width=4)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 52)
    except OSError:
        font = ImageFont.load_default(52)
    d.text((210, 60), "manimvox 0.8.5", font=font, fill=(230, 238, 242, 255), anchor="mm")
    return img


def still(path: Path, t: float) -> Image.Image:
    r = Reader(path)
    try:
        return r.at(t).to_image()
    finally:
        r.close()


def film_cube(path: Path, n: int = 17) -> None:
    """A warm film look as a 3D LUT: shadows lifted and cooled, highlights warmed, a gentle S-curve, colour eased."""
    rows = []
    for b in range(n):
        for g in range(n):
            for r in range(n):
                c = np.array([r, g, b], float) / (n - 1)
                y = c @ [0.2126, 0.7152, 0.0722]
                c = y + (c - y) * 0.9  # a little less colour
                c = 0.5 + (c - 0.5) * 1.12  # gentle contrast
                c = c + np.array([0.04, 0.015, -0.03]) * y  # warm the highlights
                c = c + np.array([-0.01, 0.0, 0.025]) * (1 - y)  # cool the shadows
                c = 0.03 + c * 0.95  # lift the blacks, like print film
                rows.append(" ".join(f"{v:.6f}" for v in np.clip(c, 0, 1)))
    path.parent.mkdir(exist_ok=True)
    path.write_text(f'TITLE "warm film"\nLUT_3D_SIZE {n}\n' + "\n".join(rows) + "\n")


if __name__ == "__main__":
    BUILD.mkdir(exist_ok=True)
    sf.write(str(BUILD / "pad.wav"), pad(), RATE)
    sf.write(str(BUILD / "whoosh.wav"), whoosh(), RATE)
    badge().save(BUILD / "badge.png")
    still(DEMOLITION, 27.0).save(BUILD / "towers.png")
    still(CHROMA, 97.0).save(BUILD / "mountain.png")
    film_cube(HERE / "looks" / "film.cube")
    print("wrote build/pad.wav, build/whoosh.wav, build/badge.png, build/towers.png, build/mountain.png and looks/film.cube")
