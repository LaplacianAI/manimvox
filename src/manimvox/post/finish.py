"""The finished episode (`finish`) and the joined film (`concat`): Manim's render plus music, captions and cards."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .audio import RATE, limit, music_bed, read_audio
from .draw import caption_overlay, card_image
from .encode import Writer, frame_count, frames, video_info
from .options import PostError, PostOptions


def _ts(t: float) -> str:
    ms = round(t * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def srt_text(cues) -> str:
    return "\n".join(f"{i}\n{_ts(c.start)} --> {_ts(c.end)}\n{c.text}\n" for i, c in enumerate(cues, 1))


def finish(src: Path, dst: Path, cues, opts: PostOptions, theme, root: Path) -> list[str]:
    """Write `dst`: `src` with the music bed, burned captions and end card that `opts` ask for.
    Returns one line per step done. On any failure `dst` is removed."""
    w, h, fps = video_info(src)
    music = None
    if opts.music is not None:
        path = Path(root) / opts.music
        if not path.is_file():
            raise PostError(f"post.music: no file at {path}")
        music = read_audio(path)
    voice = read_audio(src)
    done = []
    out = Writer(dst, (w, h), fps)
    try:
        sound = voice
        if music is not None:
            # Manim's narration ends at the last sound, before the picture does: the bed runs the video's whole
            # length plus the end card and fades out at the very end, and the narration is padded to match.
            card_n = round(opts.card_seconds * fps) if opts.end_card else 0
            n = round((frame_count(src) + card_n) * RATE / fps)
            sound = np.pad(voice[:, :n], ((0, 0), (0, max(0, n - voice.shape[1]))))
            sound = sound + music_bed(music, n, cues, opts.music_db, opts.duck_db)
            done.append(f"music bed {opts.music.as_posix()} at {opts.music_db:g} dB, "
                        f"{opts.duck_db:g} dB more under narration")
        out.audio(limit(sound))
        overlays, k = {}, 0
        for t, rgb in frames(src):
            if opts.captions == "burn":
                while k < len(cues) and cues[k].end <= t:
                    k += 1
                if k < len(cues) and cues[k].start <= t:
                    if k not in overlays:
                        overlays = {k: caption_overlay(cues[k].text, w, h, theme)}  # only the current cue's plate is kept
                    overlays[k].blend(rgb)
            out.add(rgb)
        if music is None:  # with a bed, the sound already runs through the card; otherwise the card is silent
            out.sync()
        if opts.captions == "burn":
            done.append("captions burned in (the .srt ships too)")
        if opts.end_card:
            card = card_image(None, list(opts.end_card), w, h, theme)
            for _ in range(round(opts.card_seconds * fps)):
                out.add(card)
            done.append(f"end card, {opts.card_seconds:g} s")
        out.close()
    except BaseException:
        out.abort()
        Path(dst).unlink(missing_ok=True)
        raise
    return done


def concat(parts, dst: Path, theme, title: list[str] | None = None, end=(), card_seconds: float = 3.0) -> list[float]:
    """Join `parts` into `dst`, after a title card and before an end card (each optional; title[0] is the
    title, the rest are lines under it). Returns where each part starts in `dst`, in seconds."""
    if not parts:
        raise PostError("nothing to join")
    w, h, fps = video_info(parts[0])
    for p in parts[1:]:
        if video_info(p)[2] != fps:
            raise PostError(f"{Path(p).name} has another frame rate than {Path(parts[0]).name}; "
                            "render every part at the same quality")
    card_n = round(card_seconds * fps)
    starts = []
    out = Writer(dst, (w, h), fps)
    try:
        if title:
            img = card_image(title[0], title[1:], w, h, theme)
            for _ in range(card_n):
                out.add(img)
            out.sync()
        for p in parts:
            starts.append(float(out.frames / fps))
            out.audio(read_audio(p))
            for _t, rgb in frames(p, size=(w, h)):
                out.add(rgb)
            out.sync()
        if end:
            img = card_image(None, list(end), w, h, theme)
            for _ in range(card_n):
                out.add(img)
        out.close()
    except BaseException:
        out.abort()
        Path(dst).unlink(missing_ok=True)
        raise
    return starts
