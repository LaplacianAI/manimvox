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
VOICE_URL = "https://api.elevenlabs.io/v1/voices/{voice_id}"
VOICES_URL = "https://api.elevenlabs.io/v2/voices"
DEFAULT_MODEL = "eleven_multilingual_v2"
SPEED_RANGE = (0.7, 1.2)
KEY_VAR = "ELEVENLABS_API_KEY"
MAX_VOICE_PAGES = 100
UNREADABLE_VOICE_LIST = "ElevenLabs returned an unreadable voice list"
ENDLESS_VOICE_LIST = "ElevenLabs kept paging the voice list; try again later"


MISSING_PERMISSION = "missing the permission "  # ElevenLabs' wording for a restricted key


class MissingPermission(VoiceError):
    """The key is valid but restricted, and this call needs a permission it lacks."""


def split_voice(voice: str) -> tuple[str, str]:
    model, sep, vid = voice.rpartition("/")
    return (model if sep else DEFAULT_MODEL), vid


def _read_voice_page(body: bytes) -> tuple[list[tuple[str, str]], str | None, bool]:
    """One page of GET /v2/voices -> (rows, next_page_token, has_more). Anything off-shape is a VoiceError."""
    try:
        page = json.loads(body)
    except ValueError:  # JSONDecodeError and UnicodeDecodeError both
        raise VoiceError(UNREADABLE_VOICE_LIST) from None
    if not isinstance(page, dict) or not isinstance(page.get("voices"), list):
        raise VoiceError(UNREADABLE_VOICE_LIST)
    rows: list[tuple[str, str]] = []
    for v in page["voices"]:
        if not isinstance(v, dict) or not isinstance(v.get("voice_id"), str) or not v["voice_id"]:
            raise VoiceError(UNREADABLE_VOICE_LIST)
        name = v.get("name")
        rows.append((v["voice_id"], name if isinstance(name, str) else ""))
    token = page.get("next_page_token")
    if token is not None and not isinstance(token, str):
        raise VoiceError(UNREADABLE_VOICE_LIST)
    return rows, token, bool(page.get("has_more"))


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

    def _call(self, method: str, url: str, body: bytes | None = None, *, resumable: bool = True) -> bytes:
        key = self._key()
        headers = {"xi-api-key": key, "Content-Type": "application/json"}
        try:
            return request("ElevenLabs", method, url, headers=headers, body=body, sleep=self._sleep, secrets=[key],
                           resumable=resumable)
        except VoiceError as e:
            if "HTTP 401" in str(e) and MISSING_PERMISSION in str(e):
                # a restricted key: it works, but not for this call. Name the permission, not a bad key.
                perm = (str(e).partition(MISSING_PERMISSION)[2].split() or ["needed"])[0]
                raise MissingPermission(f"the key in {KEY_VAR} lacks the ElevenLabs permission {perm}; "
                                        "give it that permission in the ElevenLabs API key settings") from None
            if "HTTP 401" in str(e):
                raise VoiceError(f"ElevenLabs rejected the key in {KEY_VAR} (HTTP 401)") from None
            raise

    def status(self) -> EngineStatus:
        if not (self._env.get(KEY_VAR) or "").strip():
            return EngineStatus(False, f"needs {KEY_VAR}")
        return EngineStatus(True, f"online; {KEY_VAR} is set")

    def describe_voices(self) -> list[tuple[str, str]]:
        if self._list is None:
            rows: list[tuple[str, str]] = []
            token: str | None = None
            seen: set[str] = set()
            for _ in range(MAX_VOICE_PAGES):
                q = {"page_size": "100"} | ({"next_page_token": token} if token else {})
                url = f"{VOICES_URL}?{urllib.parse.urlencode(q)}"
                page_rows, token, has_more = _read_voice_page(self._call("GET", url, resumable=False))
                rows += page_rows
                if not has_more or not token:
                    break
                if token in seen:
                    raise VoiceError(ENDLESS_VOICE_LIST)
                seen.add(token)
            else:
                raise VoiceError(ENDLESS_VOICE_LIST)
            self._list = sorted(rows, key=lambda r: r[1].lower())
        return self._list

    def voices(self) -> list[str]:
        return [v for v, _ in self.describe_voices()]

    def voice_key(self, voice: str) -> str:
        return "/".join(split_voice(voice))

    def prepare(self, voice: str, confirm, root) -> None:
        self._key()
        model, vid = split_voice(voice)
        if not model or not vid:
            raise VoiceError(f"elevenlabs voice '{voice}' needs a voice id (and a model before the slash, if any); "
                             "see `manimvox voices elevenlabs`")
        try:
            self._call("GET", VOICE_URL.format(voice_id=urllib.parse.quote(vid, safe="")), resumable=False)
        except MissingPermission:
            return  # a key restricted to speech can't look the voice up; the first line will show if it's wrong
        except VoiceError as e:
            if "HTTP 404" in str(e):
                raise VoiceError(f"no ElevenLabs voice '{vid}'; see `manimvox voices elevenlabs`") from None
            raise

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
