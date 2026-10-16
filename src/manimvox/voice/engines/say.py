"""macOS `say`: built-in system voices, no download, no key. macOS only."""

from __future__ import annotations

import difflib
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from ..base import EngineStatus, VoiceEngine, VoiceError

WPM = 175  # a natural narration pace; speed scales it
# One space may separate a long name from its locale ("Eddy (English (US)) en_US"), so the gap is \s+, not \s{2,}.
_LINE = re.compile(r"^(.+?)\s+([A-Za-z]{2,3}_[A-Za-z0-9]+)\s+#")


def parse_voice_list(text: str) -> list[tuple[str, str]]:
    out = []
    for line in text.splitlines():
        m = _LINE.match(line)
        if m:
            out.append((m.group(1).strip(), m.group(2)))
    return out


class SayEngine(VoiceEngine):
    name = "say"
    extra = None
    default_voice = "Samantha"
    noncommercial = True
    licence = ("macOS system voices under the macOS software licence, which limits voice output to "
               "personal, non-commercial use (verify against your macOS version)")

    def __init__(self, run: Callable = subprocess.run, platform: str = sys.platform) -> None:
        self._run, self._platform = run, platform
        self._list: list[tuple[str, str]] | None = None

    def _available(self) -> str | None:
        if self._platform != "darwin":
            return "the say engine is macOS only; choose another voice with --voice (e.g. kokoro:af_heart)"
        if self._run is subprocess.run and shutil.which("say") is None:
            return "the `say` command is not on PATH"
        return None

    def status(self) -> EngineStatus:
        why = self._available()
        return EngineStatus(False, why.replace("the say engine is ", "")) if why else EngineStatus(True, "built into macOS")

    def describe_voices(self) -> list[tuple[str, str]]:
        if self._available():
            return []
        if self._list is None:
            r = self._run(["say", "-v", "?"], capture_output=True, text=True, encoding="utf-8", check=False)
            self._list = parse_voice_list(r.stdout or "")
        return self._list

    def voices(self) -> list[str]:
        return [n for n, _ in self.describe_voices()]

    def prepare(self, voice: str, confirm, root) -> None:
        why = self._available()
        if why:
            raise VoiceError(why)
        have = self.voices()
        if voice not in have:
            near = difflib.get_close_matches(voice, have, n=3)
            raise VoiceError(f"say has no voice '{voice}'" + (f" (did you mean {', '.join(near)}?)" if near else "")
                             + "; see `manimvox voices say`")

    def synth(self, text: str, voice: str, speed: float, out: Path) -> None:
        cmd = ["say", "-v", voice, "-r", str(round(WPM * speed)), "-o", str(out),
               "--file-format=WAVE", "--data-format=LEI16@24000", "-f", "-"]
        r = self._run(cmd, input=text, capture_output=True, text=True, encoding="utf-8", check=False)
        if r.returncode != 0:
            raise VoiceError(f"say failed for voice '{voice}': {(r.stderr or r.stdout).strip()[:300]}")
