"""Write build/pad.wav: a quiet, slowly moving chord to sit under the film. Synthesised here, so the music has no
licence to credit. Run it once before rendering the edit: uv run python make_pad.py"""
from pathlib import Path

import numpy as np
import soundfile as sf

RATE, SECONDS = 48000, 90
NOTES = (110.0, 164.81, 220.0, 261.63, 329.63)  # A2 E3 A3 C4 E4: an open A minor chord


def pad() -> np.ndarray:
    t = np.arange(RATE * SECONDS) / RATE
    left, right = np.zeros_like(t), np.zeros_like(t)
    for k, f in enumerate(NOTES):
        swell = 0.6 + 0.4 * np.sin(2 * np.pi * t / (11 + 3 * k) + k)  # each note breathes at its own pace
        tone = sum(np.sin(2 * np.pi * f * h * t + k) / h**2 for h in (1, 2, 3))  # soft overtones, no edge
        left += swell * tone * (0.6 + 0.08 * k)
        right += swell * tone * (0.92 - 0.08 * k)  # the chord spread a little across the stereo field
    x = np.stack([left, right], axis=1)
    return (0.25 * x / np.abs(x).max()).astype(np.float32)


if __name__ == "__main__":
    out = Path(__file__).parent / "build" / "pad.wav"
    out.parent.mkdir(exist_ok=True)
    sf.write(str(out), pad(), RATE)
    print(f"wrote {out}")
