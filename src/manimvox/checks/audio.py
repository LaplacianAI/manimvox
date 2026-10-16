"""Audio check: every narration line must be audible in the final file. Frames cannot show a dropped line."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import av
import numpy as np

RATE = 8000
SILENT_RMS = 60  # of 32768; speech sits in the thousands
_CUE = re.compile(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)\n(.+?)(?:\n\n|\Z)", re.DOTALL)


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


@dataclass
class AudioReport:
    total: int
    silent: list[Cue] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and not self.silent

    def __str__(self) -> str:
        if self.error:
            return f"audio check: FAILED  {self.error}"
        if not self.silent:
            return f"audio check: ok  ({self.total} lines, all audible)"
        rows = [f"audio check: FAILED  {len(self.silent)} of {self.total} lines are silent"]
        for c in self.silent:
            rows.append(f"    {int(c.start) // 60}:{int(c.start) % 60:02d}-{int(c.end) // 60}:{int(c.end) % 60:02d}"
                        f"  {c.text[:78]}")
        return "\n".join(rows)


def read_cues(srt: Path) -> list[Cue]:
    out = []
    for m in _CUE.finditer(Path(srt).read_text(encoding="utf-8")):
        g = [int(x) for x in m.groups()[:8]]
        out.append(Cue(g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000,
                       g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000, " ".join(m.group(9).split())))
    return out


def _pcm(video: Path) -> np.ndarray | None:
    with av.open(str(video)) as c:
        if not c.streams.audio:
            return None
        res = av.AudioResampler(format="s16", layout="mono", rate=RATE)
        chunks = []
        for frame in c.decode(c.streams.audio[0]):
            for f in res.resample(frame):
                chunks.append(f.to_ndarray().reshape(-1))
        for f in res.resample(None):
            chunks.append(f.to_ndarray().reshape(-1))
    return np.concatenate(chunks).astype(np.float64) if chunks else np.zeros(0)


def check_audio(video: Path, srt: Path) -> AudioReport:
    if not Path(srt).exists():
        return AudioReport(0, error=f"no subtitles at {srt}; render writes them beside the video")
    cues = read_cues(srt)
    pcm = _pcm(video)
    if pcm is None:
        return AudioReport(len(cues), error=f"{Path(video).name} has no audio track")
    silent = []
    for c in cues:
        span = pcm[int((c.start + 0.15) * RATE):int((c.end - 0.15) * RATE)]
        rms = float(np.sqrt((span ** 2).mean())) if len(span) else 0.0
        if rms < SILENT_RMS:
            silent.append(c)
    return AudioReport(len(cues), silent)
