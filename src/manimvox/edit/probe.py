"""What a media file holds, read with PyAV and Pillow: no system ffmpeg or ffprobe needed."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

ALPHA_FORMATS = ("rgba", "argb", "bgra", "abgr", "yuva", "gbrap", "ya")  # pixel formats that carry transparency
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


@dataclass(frozen=True)
class Media:
    path: str
    kind: str  # "video", "audio" or "image"
    seconds: float | None  # None for an image
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    audio: bool = False
    rate: int | None = None  # the first audio stream's sample rate
    channels: int | None = None
    alpha: bool = False  # an image (or a video's pixel format) with transparency

    def describe(self) -> str:
        parts = [self.kind]
        if self.width:
            parts.append(f"{self.width}x{self.height}")
        if self.fps:
            parts.append(f"{self.fps:g} fps")
        if self.seconds is not None:
            s = self.seconds
            parts.append(f"{int(s // 60)}:{s % 60:05.2f}")
        if self.kind == "video":
            parts.append(f"sound {self.channels} ch at {self.rate} Hz" if self.audio else "no sound")
        elif self.kind == "audio":
            parts.append(f"{self.channels} ch at {self.rate} Hz")
        if self.alpha:
            parts.append("transparent")
        return ", ".join(parts)


class MediaError(ValueError):
    """A file that is missing, or that neither PyAV nor Pillow can read."""


def probe(path) -> Media:
    p = Path(path)
    if not p.is_file():
        raise MediaError(f"{p} not found")
    if p.suffix.lower() in IMAGE_SUFFIXES:
        from PIL import Image, UnidentifiedImageError

        try:
            with Image.open(p) as img:
                alpha = img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)
                return Media(str(p), "image", None, img.width, img.height, alpha=alpha)
        except (UnidentifiedImageError, OSError) as e:
            raise MediaError(f"cannot read {p.name} as an image: {e}") from e
    import av

    try:
        with av.open(str(p)) as c:
            v = c.streams.video[0] if c.streams.video else None
            a = c.streams.audio[0] if c.streams.audio else None
            if v is None and a is None:
                raise MediaError(f"{p.name} has no picture or sound")
            seconds = _length(c, v or a)
            if v is not None:
                fmt = v.codec_context.pix_fmt or ""
                return Media(str(p), "video", seconds, v.codec_context.width, v.codec_context.height,
                             float(Fraction(v.average_rate or 30)), a is not None,
                             a.codec_context.sample_rate if a else None, a.layout.nb_channels if a else None,
                             alpha=fmt.startswith(ALPHA_FORMATS))
            return Media(str(p), "audio", seconds, audio=True, rate=a.codec_context.sample_rate,
                         channels=a.layout.nb_channels)
    except MediaError:
        raise
    except (av.error.FFmpegError, OSError) as e:
        raise MediaError(f"cannot read {p.name}: {e}") from e


def _length(c, stream) -> float:
    if stream.duration is not None and stream.time_base is not None:
        return float(stream.duration * stream.time_base)
    if c.duration:
        return c.duration / 1_000_000
    # no duration in the header (some WebM and MKV files): find the last timestamp
    last = 0.0
    for pkt in c.demux(stream):
        if pkt.pts is not None and pkt.time_base is not None:
            last = max(last, float((pkt.pts + (pkt.duration or 0)) * pkt.time_base))
    return last
