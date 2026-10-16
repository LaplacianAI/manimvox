"""Contact sheets: frames sampled every N seconds, tiled 3×3 per image. Code that runs is not a video that reads."""
from __future__ import annotations

from pathlib import Path

import av
from PIL import Image

PAD = 6


def _samples(video: Path, every: float, width: int) -> list[Image.Image]:
    try:
        container = av.open(str(video))
    except (av.error.InvalidDataError, av.error.FFmpegError) as e:
        raise ValueError(f"no video frames in {video}: {e}") from e
    with container:
        if not container.streams.video:
            raise ValueError(f"no video frames in {video}")
        stream = container.streams.video[0]
        frames, next_t = [], 0.0
        for frame in container.decode(stream):
            t = float(frame.pts * stream.time_base) if frame.pts is not None else 0.0
            if t + 1e-6 >= next_t:
                img = frame.to_image()
                img = img.resize((width, round(img.height * width / img.width)))
                frames.append(img)
                next_t += every
    if not frames:
        raise ValueError(f"no video frames in {video}")
    return frames


def contact_sheets(video: Path, out_dir: Path, every: float = 5.0, grid: int = 3, width: int = 640) -> list[Path]:
    frames = _samples(Path(video), every, width)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("s_*.png"):
        old.unlink()
    fw, fh = frames[0].size
    per = grid * grid
    paths = []
    for k in range(0, len(frames), per):
        chunk = frames[k:k + per]
        rows = (len(chunk) + grid - 1) // grid
        sheet = Image.new("RGB", (grid * fw + (grid - 1) * PAD, rows * fh + (rows - 1) * PAD), "white")
        for i, img in enumerate(chunk):
            sheet.paste(img, ((i % grid) * (fw + PAD), (i // grid) * (fh + PAD)))
        p = out_dir / f"s_{k // per + 1:02d}.png"
        sheet.save(p)
        paths.append(p)
    return paths
