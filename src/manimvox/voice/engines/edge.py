"""edge-tts: Microsoft Edge's online read-aloud voices. Free, no key; narration text goes to Microsoft."""

from __future__ import annotations

import asyncio
import difflib
import os
import time
from collections.abc import Callable
from pathlib import Path

from ..base import EngineNotInstalled, EngineStatus, VoiceEngine, VoiceError
from ..convert import to_wav
from ..http import with_retries


def rate_arg(speed: float) -> str:
    return f"{round((speed - 1.0) * 100):+d}%"


def _module():
    try:
        import edge_tts
    except ImportError as e:
        raise EngineNotInstalled("edge", "edge") from e
    return edge_tts


class EdgeEngine(VoiceEngine):
    name = "edge"
    extra = "edge"
    default_voice = "en-US-AriaNeural"
    online = "Microsoft (Edge read-aloud service)"
    licence = "edge-tts LGPL-3.0; uses Microsoft's unofficial Edge read-aloud service, whose terms apply"

    def __init__(self, sleep: Callable[[float], None] = time.sleep) -> None:
        self._sleep = sleep
        self._list: list[tuple[str, str]] | None = None

    def status(self) -> EngineStatus:
        try:
            _module()
        except EngineNotInstalled:
            return EngineStatus(False, 'not installed: uv tool install "manimvox[edge]"')
        return EngineStatus(True, "online, no key needed")

    def prepare(self, voice: str, confirm, root) -> None:
        _module()
        known = self.voices()  # one listing request, retried
        if voice not in known:
            near = difflib.get_close_matches(voice, known, n=3)
            raise VoiceError(f"no Edge voice '{voice}'" + (f" (did you mean {', '.join(near)}?)" if near else "")
                             + "; see `manimvox voices edge`")

    def describe_voices(self) -> list[tuple[str, str]]:
        if self._list is None:
            m = _module()
            rows = with_retries(lambda: asyncio.run(m.list_voices()), "edge-tts", sleep=self._sleep,
                               resumable=False)
            self._list = sorted((v["ShortName"], f"{v.get('Locale', '')}, {v.get('Gender', '')}") for v in rows)
        return self._list

    def voices(self) -> list[str]:
        return [v for v, _ in self.describe_voices()]

    def synth(self, text: str, voice: str, speed: float, out: Path) -> None:
        m = _module()
        mp3 = out.with_name(f"{out.stem}.{os.getpid()}.mp3")

        def once() -> None:
            m.Communicate(text, voice, rate=rate_arg(speed)).save_sync(str(mp3))

        try:
            try:
                with_retries(once, "edge-tts", sleep=self._sleep)
            except VoiceError as e:
                raise VoiceError(f"{e} (check the voice name with `manimvox voices edge`)") from None
            to_wav(mp3, out)
        finally:
            mp3.unlink(missing_ok=True)
