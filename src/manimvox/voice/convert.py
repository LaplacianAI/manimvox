"""Turn what a voice service returns into the mono 16-bit WAV the kit plays."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from .base import VoiceError


def pcm16_to_wav(pcm: bytes, rate: int, out: Path) -> None:
    n = len(pcm) // 2
    if n == 0:
        raise VoiceError("the voice service returned no audio")
    data = np.frombuffer(pcm[: n * 2], dtype="<i2")
    sf.write(str(out), data, rate, format="WAV", subtype="PCM_16")


def to_wav(src: Path, out: Path) -> None:
    """Decode any file PyAV can read (MP3 from edge-tts) into mono 16-bit WAV at its own sample rate."""
    import av

    chunks: list[np.ndarray] = []
    rate = 0
    try:
        with av.open(str(src)) as c:
            if not c.streams.audio:
                raise VoiceError(f"could not read audio from {src}: no audio stream")
            res = av.AudioResampler(format="s16", layout="mono")
            for frame in c.decode(c.streams.audio[0]):
                for f in res.resample(frame):
                    chunks.append(f.to_ndarray().reshape(-1))
                    rate = f.sample_rate
            for f in res.resample(None):
                chunks.append(f.to_ndarray().reshape(-1))
    except av.error.FFmpegError as e:
        raise VoiceError(f"could not read audio from {src}: {e}") from e
    if not chunks or not rate:
        raise VoiceError(f"could not read audio from {src}: it holds no samples")
    sf.write(str(out), np.concatenate(chunks), rate, format="WAV", subtype="PCM_16")
