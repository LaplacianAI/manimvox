"""Multi-camera sync: recordings of one moment lined up by their sound.

Each file's loudness, every 10 ms, is high-passed (its slow level taken out, so only the rise and fall of speech,
claps and knocks remain) and cross-correlated with the first camera's by FFT. The peak is the offset; how far it
stands above the next-best peak, more than a second away, is the confidence. Below `CONFIDENT` the files are not
lined up, rather than lined up wrong. Results are cached in build/edit/sync/.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .sound import envelope_db

HOP = 0.01  # s: loudness is measured this often
FLOOR = -70.0  # dB: quieter than this is silence
CONFIDENT = 1.5  # the peak must stand this many times above any other more than a second away
MIN_OVERLAP = 3.0  # s: two recordings must share at least this much sound


class SyncError(ValueError):
    """Two recordings that could not be lined up by their sound; the message says why and what to do."""


@dataclass(frozen=True)
class Offset:
    """`seconds`: where the other file's start falls on the first file's clock (negative: it started earlier).
    `confidence`: the peak over the next-best one."""
    seconds: float
    confidence: float


def _signal(path: Path) -> np.ndarray:
    env = np.maximum(envelope_db(path, hop=HOP), FLOOR)
    if env.size < 10:
        return np.zeros(0)
    k = np.ones(101) / 101  # a second's average: the slow level
    slow = np.convolve(np.pad(env, 50, mode="edge"), k, mode="valid")
    x = env - slow
    sd = float(x.std())
    return x / sd if sd > 1e-6 else np.zeros_like(x)


def _key(a: Path, b: Path) -> str:
    sa, sb = a.stat(), b.stat()
    raw = f"1|{a.resolve()}|{sa.st_size}|{sa.st_mtime_ns}|{b.resolve()}|{sb.st_size}|{sb.st_mtime_ns}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def find_offset(root: Path, first: Path, other: Path) -> Offset:
    """Where `other` starts on `first`'s clock. Raises SyncError when the sound does not say clearly."""
    cache = Path(root) / "build" / "edit" / "sync" / f"{_key(first, other)}.json"
    if cache.is_file():
        d = json.loads(cache.read_text())
        return Offset(d["seconds"], d["confidence"])
    a, b = _signal(first), _signal(other)
    for path, x in ((first, a), (other, b)):
        if not x.any():
            raise SyncError(f"{path.name} has no sound to line it up by; give its offset by hand")
    n = 1 << int(np.ceil(np.log2(a.size + b.size)))
    corr = np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(b, n)), n)
    lags = np.arange(n)
    lags[lags > n // 2] -= n  # corr[L] = sum a[t + L] b[t]: other's frame t is first's frame t + L
    overlap = np.minimum(a.size, lags + b.size) - np.maximum(0, lags)
    need = min(MIN_OVERLAP / HOP, 0.5 * min(a.size, b.size))
    corr = np.where(overlap >= need, corr, 0.0)  # summed, not averaged: a sliver of overlap must not win by chance
    i = int(np.argmax(corr))
    best = corr[i]
    far = np.abs(lags - lags[i]) > round(1.0 / HOP)
    runner = float(corr[far].max(initial=0.0))
    confidence = float(best / runner) if runner > 0 else float("inf")
    if not best > 0 or confidence < CONFIDENT:
        raise SyncError(f"the sound of {other.name} does not line up clearly with {first.name} (confidence "
                        f"{confidence:.2f}, needs {CONFIDENT}); give its offset by hand, or clap on camera")
    m1, m0, p1 = corr[i - 1], corr[i], corr[(i + 1) % n]
    d = m1 - 2 * m0 + p1
    frac = 0.0 if abs(d) < 1e-12 else 0.5 * (m1 - p1) / d
    out = Offset(round(float((lags[i] + frac) * HOP), 4), round(min(confidence, 1e6), 2))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"seconds": out.seconds, "confidence": out.confidence}))
    return out
