"""Make small test videos with PyAV (bundled with Manim): no system ffmpeg needed."""
from pathlib import Path

import av
import numpy as np


def make_video(path: Path, seconds: float, fps: int = 10, size=(320, 180), audio=None, rate: int = 8000) -> Path:
    c = av.open(str(path), "w", format="matroska")
    vs = c.add_stream("mpeg4", rate=fps)
    vs.width, vs.height, vs.pix_fmt = size[0], size[1], "yuv420p"
    a_s = c.add_stream("pcm_s16le", rate=rate, layout="mono") if audio is not None else None
    for i in range(int(seconds * fps)):
        shade = int(255 * i / max(1, seconds * fps - 1))
        img = np.full((size[1], size[0], 3), shade, dtype=np.uint8)
        for p in vs.encode(av.VideoFrame.from_ndarray(img, format="rgb24")):
            c.mux(p)
    for p in vs.encode():
        c.mux(p)
    if a_s is not None:
        pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16).reshape(1, -1)
        fr = av.AudioFrame.from_ndarray(pcm, format="s16", layout="mono")
        fr.sample_rate = rate
        for p in a_s.encode(fr):
            c.mux(p)
        for p in a_s.encode():
            c.mux(p)
    c.close()
    return path
