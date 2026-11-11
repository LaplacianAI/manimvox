"""Sound for the renderer: a span of a file's sound, sped up or slowed with its pitch kept, envelopes at seams,
and the levelled mix. All float32 stereo, shape (2, n), at the post RATE."""
from __future__ import annotations

import math
from pathlib import Path

import av
import numpy as np

from ..post.audio import RATE
from ..voice.loudness import integrated_loudness, true_peak

EDGE = 0.03  # s: every cut fades its sound over 30 ms, so a seam never clicks


def samples(seconds: float) -> int:
    return max(0, round(seconds * RATE))


def read_span(path: Path, start: float = 0.0, end: float | None = None) -> np.ndarray:
    """The sound of `path` from `start` to `end` seconds (None: its end); silence if it has none."""
    with av.open(str(path)) as c:
        if not c.streams.audio:
            return np.zeros((2, 0 if end is None else samples(end - start)), np.float32)
        s = c.streams.audio[0]
        mono = s.layout.nb_channels == 1
        res = av.AudioResampler(format="fltp", layout="mono" if mono else "stereo", rate=RATE)
        if start > 0:
            c.seek(max(0, int(start / s.time_base)), stream=s, backward=True)
        want = None if end is None else samples(end - start)
        chunks, skip, have, first = [], 0, 0, True
        for frame in c.decode(s):
            if first:  # the seek lands at or before `start`: drop what comes before it
                t0 = float(frame.pts * s.time_base) if frame.pts is not None else 0.0
                skip = max(0, samples(start - t0))
                first = False
            for r in res.resample(frame):
                x = r.to_ndarray()
                if skip:
                    cut = min(skip, x.shape[1])
                    x, skip = x[:, cut:], skip - cut
                chunks.append(x)
                have += x.shape[1]
            if want is not None and have >= want:
                break
        else:
            chunks += [r.to_ndarray() for r in res.resample(None)]
    x = np.concatenate(chunks, axis=1).astype(np.float32) if chunks else np.zeros((1 if mono else 2, 0), np.float32)
    if mono:
        x = np.repeat(x, 2, axis=0)
    return fit_length(x, want) if want is not None else x


def envelope_db(path: Path, start: float = 0.0, end: float | None = None, hop: float = 0.01,
                rate: int = 16000) -> np.ndarray:
    """Loudness in dB every `hop` seconds of `path` from `start` to `end`: the sound decoded at `rate` Hz mono
    and measured as it streams, so a long file never sits in memory. Frame k covers start + k * hop."""
    step = max(1, round(hop * rate))
    out: list[float] = []
    rest = np.zeros(0, np.float32)
    with av.open(str(path)) as c:
        if not c.streams.audio:
            return np.zeros(0)
        s = c.streams.audio[0]
        res = av.AudioResampler(format="flt", layout="mono", rate=rate)
        if start > 0:
            c.seek(max(0, int(start / s.time_base)), stream=s, backward=True)
        skip, first = 0, True
        want = None if end is None else round((end - start) / hop)
        for frame in c.decode(s):
            if first:
                t0 = float(frame.pts * s.time_base) if frame.pts is not None else 0.0
                skip = max(0, round((start - t0) * rate))
                first = False
            for r in res.resample(frame):
                x = r.to_ndarray().reshape(-1)
                if skip:
                    cut = min(skip, x.shape[0])
                    x, skip = x[cut:], skip - cut
                rest = np.concatenate([rest, x])
                n = rest.shape[0] // step
                if n:
                    blocks = rest[:n * step].reshape(n, step)
                    out.extend(20 * np.log10(np.sqrt(np.mean(blocks.astype(np.float64) ** 2, axis=1)) + 1e-9))
                    rest = rest[n * step:]
            if want is not None and len(out) >= want:
                break
    db = np.asarray(out)
    return db[:want] if want is not None else db


def fit_length(x: np.ndarray, n: int) -> np.ndarray:
    if x.shape[1] >= n:
        return x[:, :n]
    return np.pad(x, ((0, 0), (0, n - x.shape[1])))


def _tempo_steps(speed: float) -> list[float]:
    """atempo factors whose product is `speed`, each within the 0.5 to 2 every FFmpeg build accepts."""
    steps = []
    while speed > 2.0:
        steps.append(2.0)
        speed /= 2.0
    while speed < 0.5:
        steps.append(0.5)
        speed /= 0.5
    return [*steps, speed]


def stretch(x: np.ndarray, speed: float) -> np.ndarray:
    """`x` played at `speed` with its pitch kept (FFmpeg's atempo), exactly len/speed samples long."""
    n = round(x.shape[1] / speed)
    if abs(speed - 1.0) < 1e-9 or x.shape[1] == 0:
        return fit_length(x, n)
    g = av.filter.Graph()
    node = g.add_abuffer(sample_rate=RATE, format="fltp", layout="stereo", time_base=f"1/{RATE}")
    for f in _tempo_steps(speed):
        nxt = g.add("atempo", f"{f:.6f}")
        node.link_to(nxt)
        node = nxt
    fmt = g.add("aformat", f"sample_fmts=fltp:channel_layouts=stereo:sample_rates={RATE}")  # the sink packs otherwise
    node.link_to(fmt)
    sink = g.add("abuffersink")
    fmt.link_to(sink)
    g.configure()
    out = []

    def drain():
        while True:
            try:
                out.append(g.pull().to_ndarray())
            except (av.BlockingIOError, av.error.EOFError):
                return

    for i in range(0, x.shape[1], 4096):
        fr = av.AudioFrame.from_ndarray(np.ascontiguousarray(x[:, i:i + 4096]), format="fltp", layout="stereo")
        fr.sample_rate, fr.pts = RATE, i
        g.push(fr)
        drain()
    g.push(None)
    drain()
    y = np.concatenate(out, axis=1).astype(np.float32) if out else np.zeros((2, 0), np.float32)
    return fit_length(y, n)


def _ramp_at(idx: np.ndarray, start: int, length: int, up: bool) -> np.ndarray:
    """A linear ramp over samples [start, start + length), read at `idx`: 0..1 when `up`, 1..0 otherwise, and
    flat outside it (0 before an up ramp and after a down ramp)."""
    if length <= 0:
        return np.ones(idx.shape, np.float32)
    k = np.clip((idx - start) / length, 0.0, 1.0).astype(np.float32)
    return k if up else 1.0 - k


def envelope(n: int, fade_in: tuple[str, float], fade_out: tuple[str, float], i0: int = 0,
             i1: int | None = None) -> np.ndarray:
    """Gain over samples [i0, i1) of a segment `n` samples long. `fade_in` is how it begins (its transition and
    overlap) and `fade_out` how it ends (the next segment's). A fade ramps across the overlap; a dip ramps across
    the half of it on this segment's side and is silent in the other half; a cut fades over EDGE."""
    i1 = n if i1 is None else i1
    idx = np.arange(i0, i1, dtype=np.float64)
    env = np.ones(idx.shape, np.float32)
    kind, overlap = fade_in
    o = min(n, samples(overlap)) if kind != "cut" else 0
    if not o:
        env *= _ramp_at(idx, 0, min(n, samples(EDGE)), True)
    elif kind == "fade":
        env *= _ramp_at(idx, 0, o, True)
    else:
        env *= _ramp_at(idx, o // 2, o - o // 2, True)
    kind, overlap = fade_out
    o = min(n, samples(overlap)) if kind != "cut" else 0
    if not o:
        k = min(n, samples(EDGE))
        env *= _ramp_at(idx, n - k, k, False)
    elif kind == "fade":
        env *= _ramp_at(idx, n - o, o, False)
    else:
        env *= _ramp_at(idx, n - o, o // 2, False)
    return env


def add_at(bus: np.ndarray, x: np.ndarray, at: float, gain: float = 1.0) -> None:
    """Mix `x` into `bus` from `at` seconds of the bus (negative: `x` began before it), cut at its ends."""
    i = samples(at) if at >= 0 else -samples(-at)
    s = max(0, -i)
    i = max(0, i)
    k = min(x.shape[1] - s, bus.shape[1] - i)
    if k > 0:
        bus[:, i:i + k] += x[:, s:s + k] * gain


def db(v: float) -> float:
    return 10.0 ** (v / 20.0)


RAISE_AT_MOST = 12.0  # dB: footage is raised to the target at most this much, so room tone never roars
NEAR_SILENT = -50.0  # LUFS: quieter than this is left alone


def levelling_db(x: np.ndarray, target: float | None) -> tuple[float, float | None]:
    """The gain (dB) that brings footage sound `x` to `target` LUFS, and its loudness. Nothing for silence,
    near-silence or no target; a raise is capped at RAISE_AT_MOST."""
    if target is None or x.shape[1] == 0:
        return 0.0, None
    now = integrated_loudness(x.mean(axis=0), RATE)
    if not math.isfinite(now) or now < NEAR_SILENT:
        return 0.0, (now if math.isfinite(now) else None)
    return max(-30.0, min(RAISE_AT_MOST, target - now)), now


def bed_window(music: np.ndarray, at: float, until: float, t0: float, t1: float, volume_db: float,
               fade_in: float = 1.0, fade_out: float = 2.0) -> np.ndarray:
    """The part of a music bed (`music` looped from `at` to `until` seconds of the film, at `volume_db`, faded in
    and out at its own ends) that falls in [t0, t1), as a window `samples(t1 - t0)` long."""
    n = samples(t1 - t0)
    out = np.zeros((2, n), np.float32)
    lo, hi = max(at, t0), min(until, t1)
    if hi <= lo or music.shape[1] == 0:
        return out
    g0, m, total = samples(lo - at), samples(hi - lo), samples(until - at)
    m = min(m, n - samples(lo - t0))
    idx = np.arange(g0, g0 + m)
    env = (_ramp_at(idx, 0, min(total, samples(fade_in)), True)
           * _ramp_at(idx, total - min(total, samples(fade_out)), min(total, samples(fade_out)), False))
    i = samples(lo - t0)
    out[:, i:i + m] = music[:, idx % music.shape[1]] * (env * db(volume_db))
    return out


def limit_stereo(x: np.ndarray, ceiling_db: float = -1.0) -> np.ndarray:
    """`x` with its true peaks under `ceiling_db`, one gain for both channels, eased around each peak."""
    if x.shape[1] == 0:
        return x
    from ..voice.loudness import LOOKAHEAD, RELEASE, _smooth_below

    ceiling = db(ceiling_db)
    peak = np.maximum(true_peak(x[0]), true_peak(x[1]))
    if peak.max() <= ceiling:
        return x
    need = np.minimum(1.0, ceiling / np.maximum(peak, 1e-12))
    gain = _smooth_below(_smooth_below(need, max(1, int(LOOKAHEAD * RATE))), max(1, int(RELEASE * RATE)))
    return (x * np.minimum(gain, need)).astype(np.float32)
