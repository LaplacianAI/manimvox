"""Synthesis cached by engine, voice, speed and spoken text, so a re-render never pays twice."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import soundfile as sf

from .base import VoiceError, VoiceSpec
from .loudness import CEILING_DB, level_file
from .registry import get_engine


def _write_once(path: Path, make) -> None:
    """Run make(tmp) and move the result to `path`, so a crash or a parallel render never leaves half a file."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.stem}.{os.getpid()}.tmp.wav")
    try:
        make(tmp)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def synth_cached(spec: VoiceSpec, spoken: str, speed: float, cache_dir: Path,
                 loudness: float | None = None) -> tuple[Path, float]:
    """The line's audio and its length. With `loudness` (LUFS), a levelled copy of the cached line: the line as
    the engine returned it stays cached under the same key as before, so a new target never pays for it again."""
    if not spoken.strip():
        raise VoiceError("empty narration line: every say/steps/narrate needs words to speak")
    engine = get_engine(spec.engine)
    key = hashlib.sha1(f"{spec.engine}|{engine.voice_key(spec.voice)}|{speed}|{spoken}".encode()).hexdigest()[:16]
    path = Path(cache_dir) / f"{key}.wav"
    _write_once(path, lambda tmp: engine.synth(spoken, spec.voice, speed, tmp))
    if loudness is not None:
        raw, path = path, path.with_name(f"{key}_{loudness:g}LUFS_{CEILING_DB:g}dBTP.wav")  # a new level, a new file
        _write_once(path, lambda tmp: level_file(raw, tmp, loudness))
    info = sf.info(str(path))
    return path, info.frames / info.samplerate
