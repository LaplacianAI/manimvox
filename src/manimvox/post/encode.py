"""Read video frames, and write an H.264/AAC MP4 frame by frame with its audio kept in step."""
from __future__ import annotations

import contextlib
from collections.abc import Iterator
from fractions import Fraction
from pathlib import Path

import av
import numpy as np

from .audio import RATE
from .options import PostError

AAC_FRAME = 1024


def video_info(path: Path) -> tuple[int, int, Fraction]:
    """Width, height and frame rate of the first video stream."""
    try:
        with av.open(str(path)) as c:
            if not c.streams.video:
                raise PostError(f"{Path(path).name} has no video")
            s = c.streams.video[0]
            return s.codec_context.width, s.codec_context.height, Fraction(s.average_rate or 30)
    except (av.error.FFmpegError, OSError) as e:
        raise PostError(f"cannot read {Path(path).name}: {e}") from e


def frame_count(path: Path) -> int:
    """How many frames the first video stream holds, counted from its packets (one frame each), not estimated
    from the container's duration."""
    try:
        with av.open(str(path)) as c:
            if not c.streams.video:
                raise PostError(f"{Path(path).name} has no video")
            return sum(1 for p in c.demux(c.streams.video[0]) if p.size)
    except (av.error.FFmpegError, OSError) as e:
        raise PostError(f"cannot read {Path(path).name}: {e}") from e


def frames(path: Path, size: tuple[int, int] | None = None) -> Iterator[tuple[float, np.ndarray]]:
    """(time in seconds, RGB frame) for every frame of `path`, scaled to `size` if it differs."""
    try:
        with av.open(str(path)) as c:
            s = c.streams.video[0]
            for f in c.decode(s):
                t = float(f.pts * s.time_base) if f.pts is not None else 0.0
                if size and (f.width, f.height) != size:
                    f = f.reformat(width=size[0], height=size[1])
                yield t, f.to_ndarray(format="rgb24")
    except (av.error.FFmpegError, OSError) as e:
        raise PostError(f"cannot read {Path(path).name}: {e}") from e


class Writer:
    """RGB frames in through `add`, float stereo audio in through `audio`. After each frame, queued audio is
    encoded up to the video's time; `sync` pads or cuts the queue so the audio ends where the video does."""

    def __init__(self, dst: Path, size: tuple[int, int], fps, crf: int = 18):
        self.fps = Fraction(fps).limit_denominator(1001)
        self.c = av.open(str(dst), "w")
        self.v = self.c.add_stream("libx264", rate=self.fps)
        self.v.width, self.v.height = size
        self.v.pix_fmt = "yuv420p"
        self.v.options = {"crf": str(crf), "preset": "medium"}
        self.a = self.c.add_stream("aac", rate=RATE, layout="stereo")
        self.a.bit_rate = 192_000
        self.frames = 0
        self.written = 0  # audio samples encoded
        self._queue = np.zeros((2, 0), np.float32)

    def _video_samples(self) -> int:
        return round(self.frames * RATE / self.fps)

    def add(self, rgb: np.ndarray) -> None:
        f = av.VideoFrame.from_ndarray(np.ascontiguousarray(rgb), format="rgb24")
        f.pts = self.frames  # count frames: the source's time base and pts gaps never reach the encoder
        f.time_base = 1 / self.fps  # one tick a frame; PyAV 18 has no codec time base before the first encode
        self.frames += 1
        for p in self.v.encode(f):
            self.c.mux(p)
        self._drain(self._video_samples())

    def audio(self, samples: np.ndarray) -> None:
        self._queue = np.concatenate([self._queue, np.asarray(samples, np.float32)], axis=1)

    def sync(self) -> None:
        want = self._video_samples() - self.written
        have = self._queue.shape[1]
        if have < want:
            self._queue = np.concatenate([self._queue, np.zeros((2, want - have), np.float32)], axis=1)
        else:
            self._queue = self._queue[:, :max(0, want)]

    def _encode(self, chunk: np.ndarray) -> None:
        fr = av.AudioFrame.from_ndarray(np.ascontiguousarray(chunk), format="fltp", layout="stereo")
        fr.sample_rate = RATE
        fr.pts = self.written
        fr.time_base = Fraction(1, RATE)
        self.written += chunk.shape[1]
        for p in self.a.encode(fr):
            self.c.mux(p)

    def _drain(self, upto: int) -> None:
        while self._queue.shape[1] >= AAC_FRAME and self.written + AAC_FRAME <= upto:
            self._encode(self._queue[:, :AAC_FRAME])
            self._queue = self._queue[:, AAC_FRAME:]

    def close(self) -> None:
        self.sync()
        while self._queue.shape[1]:
            n = min(AAC_FRAME, self._queue.shape[1])
            self._encode(self._queue[:, :n])
            self._queue = self._queue[:, n:]
        for p in self.v.encode():
            self.c.mux(p)
        for p in self.a.encode():
            self.c.mux(p)
        self.c.close()

    def abort(self) -> None:
        with contextlib.suppress(Exception):  # the file is deleted next; a failed close changes nothing
            self.c.close()
