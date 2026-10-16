"""Synthesis cached by engine, voice, speed and spoken text, so a re-render never pays twice."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import soundfile as sf

from .base import VoiceError, VoiceSpec
from .registry import get_engine


def synth_cached(spec: VoiceSpec, spoken: str, speed: float, cache_dir: Path) -> tuple[Path, float]:
    if not spoken.strip():
        raise VoiceError("empty narration line: every say/steps/narrate needs words to speak")
    key = hashlib.sha1(f"{spec.engine}|{spec.voice}|{speed}|{spoken}".encode()).hexdigest()[:16]
    path = Path(cache_dir) / f"{key}.wav"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{key}.{os.getpid()}.tmp.wav")
        try:
            get_engine(spec.engine).synth(spoken, spec.voice, speed, tmp)
            os.replace(tmp, path)
        finally:
            tmp.unlink(missing_ok=True)
    info = sf.info(str(path))
    return path, info.frames / info.samplerate
