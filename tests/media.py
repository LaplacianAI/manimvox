"""Make small test videos with PyAV (bundled with Manim): no system ffmpeg needed."""
from pathlib import Path

import av
import numpy as np
import pytest


def make_mp3(path: Path, seconds: float = 1.0, rate: int = 24000) -> Path:
    try:
        av.codec.Codec("mp3", "w")
    except Exception:  # noqa: BLE001 - any failure to open the encoder means this build has none
        pytest.skip("this PyAV build has no MP3 encoder")
    c = av.open(str(path), "w")
    s = c.add_stream("mp3", rate=rate, layout="mono")
    t = np.arange(int(seconds * rate)) / rate
    fr = av.AudioFrame.from_ndarray((0.3 * np.sin(2 * np.pi * 220 * t) * 32767).astype(np.int16).reshape(1, -1),
                                    format="s16", layout="mono")
    fr.sample_rate = rate
    for p in s.encode(fr):
        c.mux(p)
    for p in s.encode():
        c.mux(p)
    c.close()
    return path


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


def make_mp4(path: Path, seconds: float, fps: int = 10, size=(320, 180), audio=None, rate: int = 24000,
             shade=None, layout: str = "mono", audio_seconds: float | None = None) -> Path:
    """An H.264/AAC MP4 like the ones manimvox renders. `audio` is mono float samples at `rate`
    (default: a 220 Hz tone; `audio_seconds` makes it shorter than the picture, as Manim's narration is), copied to both channels if `layout` is "stereo"; `shade(i)` is frame i's grey level (default: a ramp)."""
    if audio is None:
        t = np.arange(int((seconds if audio_seconds is None else audio_seconds) * rate)) / rate
        audio = 0.3 * np.sin(2 * np.pi * 220 * t)
    shade = shade or (lambda i: 20 * (i % 10))
    c = av.open(str(path), "w")
    vs = c.add_stream("libx264", rate=fps)
    vs.width, vs.height, vs.pix_fmt = size[0], size[1], "yuv420p"
    a = c.add_stream("aac", rate=rate, layout=layout)
    for i in range(int(seconds * fps)):
        img = np.full((size[1], size[0], 3), shade(i), dtype=np.uint8)
        for p in vs.encode(av.VideoFrame.from_ndarray(img, format="rgb24")):
            c.mux(p)
    for p in vs.encode():
        c.mux(p)
    mono = np.asarray(audio, np.float32).reshape(1, -1)
    if layout == "stereo":
        fr = av.AudioFrame.from_ndarray(np.repeat(mono, 2, axis=0), format="fltp", layout="stereo")
    else:
        fr = av.AudioFrame.from_ndarray(mono, format="flt", layout="mono")
    fr.sample_rate = rate
    for p in a.encode(fr):
        c.mux(p)
    for p in a.encode():
        c.mux(p)
    c.close()
    return path
