"""A stand-in engine for tests and layout work: a tone (or silence) as long as the line would take."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import soundfile as sf

from .base import EngineStatus, VoiceError

RATE = 24000
WORDS_PER_SECOND = 2.6


class FakeEngine:
    name = "fake"
    extra = None
    licence = "MIT (part of manimvox)"

    def status(self) -> EngineStatus:
        return EngineStatus(True, "built in")

    def voices(self) -> list[str]:
        return ["tone", "silence"]

    def prepare(self, confirm: Callable[[str], bool]) -> None:
        return None

    def synth(self, text: str, voice: str, speed: float, out: Path) -> None:
        if voice not in self.voices():
            raise VoiceError(f"fake voice '{voice}' unknown (have: tone, silence)")
        seconds = max(1.4, len(text.split()) / WORDS_PER_SECOND) / speed
        t = np.arange(int(seconds * RATE)) / RATE
        wave = 0.3 * np.sin(2 * np.pi * 220 * t) if voice == "tone" else np.zeros_like(t)
        sf.write(str(out), wave.astype(np.float32), RATE, format="WAV")
