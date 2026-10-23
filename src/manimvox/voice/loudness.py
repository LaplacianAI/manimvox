"""Even narration loudness across voices: measure a line as ITU-R BS.1770 integrated loudness (LUFS), bring it to
one target, and keep its true peaks under a ceiling. Voice services return audio at very different levels (8 dB
apart in the voice benchmark); levelled lines sound equally loud whatever the voice.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import soundfile as sf

DEFAULT_LOUDNESS = -16.0  # LUFS: a common target for speech online
LOUDNESS_RANGE = (-40.0, -5.0)
CEILING_DB = -1.5  # dBTP: true peaks stay below this after levelling, with room for AAC encoding to overshoot
BLOCK, STEP = 0.4, 0.1  # BS.1770 gating blocks: 400 ms, overlapping by 75%
ABSOLUTE_GATE, RELATIVE_GATE = -70.0, -10.0  # LUFS, LU
OVERSAMPLE = 4  # true peak is estimated on 4x oversampled audio, as BS.1770 suggests
LOOKAHEAD = 0.005  # s: the limiter starts turning down this long before a peak
RELEASE = 0.05  # s: and recovers over this long after it
MAKEUP_PASSES, TOLERANCE = 4, 0.1  # level again until within 0.1 LU of the target, at most 4 times


def _biquad(rate: int, kind: str, fc: float, q: float, gain_db: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """RBJ cookbook biquads, as BS.1770's K-weighting is specified for any sample rate (as in pyloudnorm)."""
    a = 10 ** (gain_db / 40)
    w0 = 2 * math.pi * fc / rate
    cos, alpha = math.cos(w0), math.sin(w0) / (2 * q)
    if kind == "high_shelf":
        sa = 2 * math.sqrt(a) * alpha
        b = [a * ((a + 1) + (a - 1) * cos + sa), -2 * a * ((a - 1) + (a + 1) * cos), a * ((a + 1) + (a - 1) * cos - sa)]
        den = [(a + 1) - (a - 1) * cos + sa, 2 * ((a - 1) - (a + 1) * cos), (a + 1) - (a - 1) * cos - sa]
    else:  # high_pass
        b = [(1 + cos) / 2, -(1 + cos), (1 + cos) / 2]
        den = [1 + alpha, -2 * cos, 1 - alpha]
    return np.array(b) / den[0], np.array(den) / den[0]


def _k_weighted(x: np.ndarray, rate: int) -> np.ndarray:
    from scipy.signal import lfilter

    for kind, fc, q, g in (("high_shelf", 1500.0, 1 / math.sqrt(2), 4.0), ("high_pass", 38.0, 0.5, 0.0)):
        b, a = _biquad(rate, kind, fc, q, g)
        x = lfilter(b, a, x)
    return x


def integrated_loudness(x: np.ndarray, rate: int) -> float:
    """BS.1770 integrated loudness of mono `x` (floats in -1..1), in LUFS; -inf for silence. A line shorter than
    one 400 ms block is measured as a single block."""
    y = _k_weighted(np.asarray(x, dtype=np.float64), rate)
    n, hop = int(BLOCK * rate), int(STEP * rate)
    if len(y) < n:
        z = np.array([np.mean(y**2)]) if len(y) else np.array([0.0])
    else:
        starts = range(0, len(y) - n + 1, hop)
        z = np.array([np.mean(y[s:s + n] ** 2) for s in starts])
    with np.errstate(divide="ignore"):
        lufs = -0.691 + 10 * np.log10(z)
    z = z[lufs > ABSOLUTE_GATE]
    if not len(z):
        return -math.inf
    relative = -0.691 + 10 * math.log10(np.mean(z)) + RELATIVE_GATE
    with np.errstate(divide="ignore"):
        z = z[-0.691 + 10 * np.log10(z) > relative]
    return -0.691 + 10 * math.log10(np.mean(z))


def true_peak(x: np.ndarray) -> np.ndarray:
    """|x| per sample, taken as the largest of the 4x oversampled values around it (an estimate of true peak)."""
    from scipy.signal import resample_poly

    up = np.abs(resample_poly(x, OVERSAMPLE, 1))[: len(x) * OVERSAMPLE]
    up = np.pad(up, (0, len(x) * OVERSAMPLE - len(up)))
    return np.maximum(np.abs(x), up.reshape(len(x), OVERSAMPLE).max(axis=1))


def _smooth_below(g: np.ndarray, width: int) -> np.ndarray:
    """A smooth curve that never rises above `g`: the minimum over ±width, averaged over width. Each average
    only covers minimums taken within `width` of its own sample, so it can't exceed that sample's value."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d

    return uniform_filter1d(minimum_filter1d(g, size=2 * width + 1, mode="nearest"), size=width, mode="nearest")


def limit(x: np.ndarray, rate: int, ceiling_db: float = CEILING_DB) -> np.ndarray:
    """Turn down only around peaks above the ceiling: the gain each sample needs, eased in over LOOKAHEAD and
    out over RELEASE. Quiet passages are left as they were, and no sample passes the ceiling."""
    ceiling = 10 ** (ceiling_db / 20)
    need = np.minimum(1.0, ceiling / np.maximum(true_peak(x), 1e-12))
    if need.min() >= 1.0:
        return x
    gain = _smooth_below(need, max(1, int(LOOKAHEAD * rate)))
    gain = _smooth_below(gain, max(1, int(RELEASE * rate)))
    return x * np.minimum(gain, need)  # the edges of a file are averaged over fewer samples: never above `need`


def level(x: np.ndarray, rate: int, target: float, ceiling_db: float = CEILING_DB) -> np.ndarray:
    """`x` brought to `target` LUFS, its true peaks kept under `ceiling_db`. Silence is returned unchanged."""
    now = integrated_loudness(x, rate)
    if not math.isfinite(now):
        return x
    y = x
    for _ in range(MAKEUP_PASSES):  # the limiter takes a little loudness off peaky voices: measure and make it up
        y = limit(y * 10 ** ((target - now) / 20), rate, ceiling_db)
        now = integrated_loudness(y, rate)
        if abs(target - now) <= TOLERANCE:
            break
    return y


def level_file(src: Path, out: Path, target: float) -> None:
    """Write `src` (any WAV the engines produce) to `out` as mono 16-bit WAV at `target` LUFS."""
    x, rate = sf.read(str(src), dtype="float64", always_2d=True)
    sf.write(str(out), level(x.mean(axis=1), rate, target), rate, format="WAV", subtype="PCM_16")
