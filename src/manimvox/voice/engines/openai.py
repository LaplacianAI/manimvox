"""OpenAI text-to-speech over HTTPS. Needs OPENAI_API_KEY; narration text goes to OpenAI."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Mapping
from pathlib import Path

from ..base import EngineStatus, VoiceEngine, VoiceError
from ..convert import pcm16_to_wav
from ..http import request

URL = "https://api.openai.com/v1/audio/speech"
DEFAULT_MODEL = "gpt-4o-mini-tts"
LEGACY_MODELS = ("tts-1", "tts-1-hd")
LEGACY_VOICES = ("alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer")
VOICES = LEGACY_VOICES + ("ballad", "verse", "marin", "cedar")
MAX_CHARS = 4096
KEY_VAR = "OPENAI_API_KEY"


def split_voice(voice: str) -> tuple[str, str]:
    model, sep, name = voice.rpartition("/")
    return (model if sep else DEFAULT_MODEL), name


class OpenAIEngine(VoiceEngine):
    name = "openai"
    extra = "cloud"
    default_voice = "alloy"
    online = "OpenAI"
    licence = ("OpenAI API terms; paid per character; the usage policy asks you to tell viewers "
               "the voice is AI-generated")

    def __init__(self, env: Mapping[str, str] = os.environ, sleep: Callable[[float], None] = time.sleep) -> None:
        self._env, self._sleep = env, sleep

    def _key(self) -> str:
        key = (self._env.get(KEY_VAR) or "").strip()
        if not key:
            raise VoiceError(f"set {KEY_VAR} to use openai voices (narration text is sent to OpenAI), "
                             "or choose an offline voice with --voice")
        return key

    def status(self) -> EngineStatus:
        if not (self._env.get(KEY_VAR) or "").strip():
            return EngineStatus(False, f"needs {KEY_VAR}")
        return EngineStatus(True, f"online; {KEY_VAR} is set")

    def voices(self) -> list[str]:
        return list(VOICES)

    def describe_voices(self) -> list[tuple[str, str]]:
        return [(v, "" if v in LEGACY_VOICES else "gpt-4o-mini-tts only") for v in VOICES]

    def voice_key(self, voice: str) -> str:
        return "/".join(split_voice(voice))

    def prepare(self, voice: str, confirm, root) -> None:
        self._key()
        model, name = split_voice(voice)
        if model in LEGACY_MODELS and name not in LEGACY_VOICES:
            raise VoiceError(f"{model} has no voice '{name}' (it has {', '.join(LEGACY_VOICES)})")

    def synth(self, text: str, voice: str, speed: float, out: Path) -> None:
        if len(text) > MAX_CHARS:
            raise VoiceError(f"a narration line is {len(text)} characters; OpenAI takes at most {MAX_CHARS}")
        key = self._key()
        model, name = split_voice(voice)
        body: dict[str, object] = {"model": model, "voice": name, "input": text, "response_format": "pcm"}
        if model in LEGACY_MODELS:
            if speed != 1.0:
                body["speed"] = speed
        elif speed != 1.0:
            body["instructions"] = f"Speak at about {speed:g} times your normal pace."
        try:
            pcm = request("OpenAI", "POST", URL, body=json.dumps(body).encode("utf-8"), sleep=self._sleep,
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                          secrets=[key])
        except VoiceError as e:
            if "HTTP 401" in str(e):
                raise VoiceError(f"OpenAI rejected the key in {KEY_VAR} (HTTP 401)") from None
            raise
        pcm16_to_wav(pcm, 24000, out)
