"""ElevenLabs text-to-speech over HTTPS. Needs ELEVENLABS_API_KEY; narration text goes to ElevenLabs."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
from collections.abc import Callable, Mapping
from pathlib import Path

from ..base import EngineStatus, VoiceEngine, VoiceError
from ..convert import pcm16_to_wav
from ..http import request

TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
VOICES_URL = "https://api.elevenlabs.io/v2/voices"
DEFAULT_MODEL = "eleven_multilingual_v2"
SPEED_RANGE = (0.7, 1.2)
KEY_VAR = "ELEVENLABS_API_KEY"


def split_voice(voice: str) -> tuple[str, str]:
    model, sep, vid = voice.rpartition("/")
    return (model if sep else DEFAULT_MODEL), vid


class ElevenLabsEngine(VoiceEngine):
    name = "elevenlabs"
    extra = "cloud"
    default_voice = "21m00Tcm4TlvDq8ikWAM"  # "Rachel", a long-standing premade voice
    online = "ElevenLabs"
    licence = "ElevenLabs terms; paid plans grant commercial use, the free tier requires attribution"

    def __init__(self, env: Mapping[str, str] = os.environ, sleep: Callable[[float], None] = time.sleep) -> None:
        self._env, self._sleep = env, sleep
        self._list: list[tuple[str, str]] | None = None

    def _key(self) -> str:
        key = (self._env.get(KEY_VAR) or "").strip()
        if not key:
            raise VoiceError(f"set {KEY_VAR} to use elevenlabs voices (narration text is sent to ElevenLabs), "
                             "or choose an offline voice with --voice")
        return key

    def _call(self, method: str, url: str, body: bytes | None = None) -> bytes:
        key = self._key()
        headers = {"xi-api-key": key, "Content-Type": "application/json"}
        try:
            return request("ElevenLabs", method, url, headers=headers, body=body, sleep=self._sleep, secrets=[key])
        except VoiceError as e:
            if "HTTP 401" in str(e):
                raise VoiceError(f"ElevenLabs rejected the key in {KEY_VAR} (HTTP 401)") from None
            raise

    def status(self) -> EngineStatus:
        if not (self._env.get(KEY_VAR) or "").strip():
            return EngineStatus(False, f"needs {KEY_VAR}")
        return EngineStatus(True, f"online; {KEY_VAR} is set")

    def describe_voices(self) -> list[tuple[str, str]]:
        if self._list is None:
            rows, token = [], None
            while True:
                q = {"page_size": "100"} | ({"next_page_token": token} if token else {})
                page = json.loads(self._call("GET", f"{VOICES_URL}?{urllib.parse.urlencode(q)}"))
                rows += [(v["voice_id"], v.get("name", "")) for v in page.get("voices", [])]
                token = page.get("next_page_token")
                if not page.get("has_more") or not token:
                    break
            self._list = sorted(rows, key=lambda r: r[1].lower())
        return self._list

    def voices(self) -> list[str]:
        return [v for v, _ in self.describe_voices()]

    def voice_key(self, voice: str) -> str:
        return "/".join(split_voice(voice))

    def prepare(self, voice: str, confirm, root) -> None:
        self._key()

    def synth(self, text: str, voice: str, speed: float, out: Path) -> None:
        lo, hi = SPEED_RANGE
        if not lo <= speed <= hi:
            raise VoiceError(f"ElevenLabs speaks at speed {lo}–{hi}; series.json has {speed}")
        model, vid = split_voice(voice)
        body: dict[str, object] = {"text": text, "model_id": model}
        if speed != 1.0:
            body["voice_settings"] = {"speed": speed}
        url = TTS_URL.format(voice_id=urllib.parse.quote(vid, safe="")) + "?output_format=pcm_24000"
        pcm16_to_wav(self._call("POST", url, json.dumps(body).encode("utf-8")), 24000, out)
