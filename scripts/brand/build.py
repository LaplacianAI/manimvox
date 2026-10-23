"""Rebuild the brand images in docs/assets from docs/assets/logo.svg and the blocks' demos.

    uv run python scripts/brand/build.py

Writes docs/assets/demo.gif (the logo animating in, then a montage of four block demos; the README and the
docs home page show it) and docs/assets/social-preview.png (upload it under Settings, General, Social preview).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[1] / "docs" / "assets"
MONTAGE = ["surface-plot", "request-flow", "bar-ranking", "code-diff"]
SIZE, FPS = (640, 360), 15
CLIP_FRAMES, HOLD_FRAMES = 36, 12  # each demo sped up to about 2.4 s, then its finished picture for 0.8 s


def frames(mp4: Path):
    import av
    from PIL import Image

    with av.open(str(mp4)) as c:
        return [f.to_image().convert("RGB").resize(SIZE, Image.LANCZOS) for f in c.decode(video=0)]


def manim(scene: str, work: Path, *args: str, env: dict | None = None) -> None:
    cmd = [sys.executable, "-m", "manim", *args, "--media_dir", str(work / "media"), str(HERE / "scenes.py"), scene]
    subprocess.run(cmd, check=True, cwd=work, env={**os.environ, **(env or {})})


def main() -> None:
    from PIL import Image

    from manimvox import blocks

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        manim("Intro", work, "-q", "l", "-r", f"{SIZE[0]},{SIZE[1]}", "--fps", str(FPS))
        intro = frames(next((work / "media").rglob("Intro.mp4")))
        seq, stills = list(intro), []
        for name in MONTAGE:
            mp4, _ = blocks.render_demo(blocks.get_block(name), work / "demos")
            fr = frames(mp4)
            fr = fr[int(len(fr) * 0.12):]  # skip the fade-in from black
            picked = [fr[round(i * (len(fr) - 1) / (CLIP_FRAMES - 1))] for i in range(CLIP_FRAMES)]
            stills.append(picked[24])
            seq += picked + [fr[-1]] * HOLD_FRAMES
        seq += [intro[-1]] * FPS  # back on the logo, so the loop restarts cleanly
        pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in seq]
        pal[0].save(ASSETS / "demo.gif", save_all=True, append_images=pal[1:], duration=1000 // FPS, loop=0,
                    optimize=True, disposal=1)

        tiles = Image.new("RGB", (SIZE[0] * 2, SIZE[1] * 2))
        for k, im in enumerate(stills):
            tiles.paste(im, ((k % 2) * SIZE[0], (k // 2) * SIZE[1]))
        tiles.save(work / "tiles.png")
        manim("Card", work, "-s", "-q", "h", "-r", "1280,640", "--format", "png", env={"MANIMVOX_BRAND_TILES": str(work / "tiles.png")})
        shutil.copyfile(next((work / "media").rglob("Card*.png")), ASSETS / "social-preview.png")
    for f in ("demo.gif", "social-preview.png"):
        print(f"wrote docs/assets/{f} ({(ASSETS / f).stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
