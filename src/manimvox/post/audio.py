"""Audio for post: any file as float stereo, a music bed ducked under the narration, peaks kept in range."""
from __future__ import annotations

from pathlib import Path

import av
import numpy as np

from .options import PostError

RATE = 48000
CTRL = 100  # the ducking gain is worked out 100 times a second, then interpolated to every sample


def read_audio(path: Path, rate: int = RATE) -> np.ndarray:
    """Every sample of the first audio stream in `path` as float32 stereo, shape (2, n), at `rate`."""
    chunks = []
    try:
        with av.open(str(path)) as c:
            if not c.streams.audio:
                return np.zeros((2, 0), np.float32)
            # libswresample upmixes mono to stereo 3 dB down; resample mono as mono and copy it to both sides
            mono = c.streams.audio[0].layout.nb_channels == 1
            res = av.AudioResampler(format="fltp", layout="mono" if mono else "stereo", rate=rate)
            for frame in c.decode(c.streams.audio[0]):
                chunks += [f.to_ndarray() for f in res.resample(frame)]
            chunks += [f.to_ndarray() for f in res.resample(None)]
            if mono:
                chunks = [np.repeat(x, 2, axis=0) for x in chunks]
    except (av.error.FFmpegError, OSError) as e:
        raise PostError(f"cannot read audio from {Path(path).name}: {e}") from e
    return np.concatenate(chunks, axis=1).astype(np.float32) if chunks else np.zeros((2, 0), np.float32)


def gain(db: float) -> float:
    return 10.0 ** (db / 20.0)


def duck_curve(n: int, cues, duck_db: float, rate: int = RATE, ramp: float = 0.3) -> np.ndarray:
    """Per-sample gain over `n` samples: 1 where nobody speaks, gain(duck_db) through every cue, sliding
    down over `ramp` seconds before a cue and back up over `ramp` seconds after it."""
    m = int(np.ceil(n / rate * CTRL)) + 1
    speaking = np.zeros(m, np.float32)
    for c in cues:
        speaking[max(0, int(c.start * CTRL)):max(0, min(m, int(np.ceil(c.end * CTRL)) + 1))] = 1.0
    k = max(1, round(ramp * CTRL / 2))
    box = np.ones(2 * k + 1, np.float32)
    held = (np.convolve(speaking, box, mode="same") > 0).astype(np.float32)  # each cue widened by k on both sides
    soft = np.convolve(held, box / box.size, mode="same")  # then its edges sloped over 2k
    ctrl = 1.0 + soft * (gain(duck_db) - 1.0)
    return np.interp(np.arange(n) * (CTRL / rate), np.arange(m), ctrl).astype(np.float32)


def music_bed(music: np.ndarray, n: int, cues, music_db: float, duck_db: float, rate: int = RATE,
              fade_in: float = 1.0, fade_out: float = 2.0) -> np.ndarray:
    """`music` looped or cut to `n` samples, at `music_db`, ducked under every cue, faded in and out."""
    if music.shape[1] == 0:
        raise PostError("the music file has no audio")
    bed = np.tile(music, (1, -(-n // music.shape[1])))[:, :n]
    env = duck_curve(n, cues, duck_db, rate) * gain(music_db)
    fi, fo = min(n, int(fade_in * rate)), min(n, int(fade_out * rate))
    env[:fi] *= np.linspace(0.0, 1.0, fi, dtype=np.float32)
    env[n - fo:] *= np.linspace(1.0, 0.0, fo, dtype=np.float32)
    return (bed * env).astype(np.float32)


def limit(x: np.ndarray, ceiling: float = 0.98) -> np.ndarray:
    """`x`, scaled down only if a sample would clip."""
    peak = float(np.abs(x).max()) if x.size else 0.0
    return x * (ceiling / peak) if peak > ceiling else x
