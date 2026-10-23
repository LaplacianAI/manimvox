"""Sarvam AI (Bulbul) text-to-speech over HTTPS, for Indian languages. Needs SARVAM_API_KEY; narration text goes to Sarvam.

A voice is `[model/]speaker[@language]`: `shubh`, `anushka@hi-IN`, `bulbul:v4-flash/simran_en_customer`.
With no model, the model whose catalogue has the speaker is used; with no language, en-IN.
"""

from __future__ import annotations

import base64
import binascii
import difflib
import json
import os
import time
from collections.abc import Callable, Mapping
from pathlib import Path

from ..base import EngineStatus, VoiceEngine, VoiceError
from ..convert import wav_bytes_to_wav
from ..http import request

URL = "https://api.sarvam.ai/text-to-speech"
KEY_VAR = "SARVAM_API_KEY"
DEFAULT_MODEL = "bulbul:v3"
DEFAULT_LANGUAGE = "en-IN"
SAMPLE_RATE = 24000
LANGUAGES = ("bn-IN", "en-IN", "gu-IN", "hi-IN", "kn-IN", "ml-IN", "mr-IN", "od-IN", "pa-IN", "ta-IN", "te-IN")
SPEAKERS = {
    "bulbul:v3": ("shubh", "aditya", "ritu", "priya", "neha", "rahul", "pooja", "rohan", "simran", "kavya", "amit",
                  "dev", "ishita", "shreya", "ratan", "varun", "manan", "sumit", "roopa", "kabir", "aayan",
                  "ashutosh", "advait", "anand", "tanya", "tarun", "sunny", "mani", "gokul", "vijay", "shruti",
                  "suhani", "mohit", "kavitha", "rehan", "soham", "rupali"),
    "bulbul:v2": ("anushka", "manisha", "vidya", "arya", "abhilash", "karun", "hitesh"),
}
# bulbul:v4-flash has 200+ persona voices (`<name>_<language>_<style>`); Sarvam checks those names itself
OPEN_MODELS = ("bulbul:v4-flash",)
MODELS = tuple(SPEAKERS) + OPEN_MODELS
MAX_CHARS = {"bulbul:v2": 1500}
DEFAULT_MAX_CHARS = 2500
PACE = {"bulbul:v2": (0.3, 3.0)}
DEFAULT_PACE = (0.5, 2.0)


def split_voice(voice: str) -> tuple[str, str, str]:
    """`[model/]speaker[@language]` -> (model, speaker, language). `v3` is short for `bulbul:v3`."""
    rest, sep, lang = voice.rpartition("@")
    if not sep:
        rest, lang = voice, DEFAULT_LANGUAGE
    model, sep, speaker = rest.rpartition("/")
    speaker = speaker.strip().lower()
    model = model.strip().lower()
    if not sep:
        model = next((m for m, names in SPEAKERS.items() if speaker in names), DEFAULT_MODEL)
    elif model and not model.startswith("bulbul:"):
        model = f"bulbul:{model}"
    return model, speaker, lang.strip()


class SarvamEngine(VoiceEngine):
    name = "sarvam"
    extra = "cloud"
    default_voice = "shubh"
    online = "Sarvam AI"
    licence = "Sarvam AI terms; paid per character"

    def __init__(self, env: Mapping[str, str] = os.environ, sleep: Callable[[float], None] = time.sleep) -> None:
        self._env, self._sleep = env, sleep

    def _key(self) -> str:
        key = (self._env.get(KEY_VAR) or "").strip()
        if not key:
            raise VoiceError(f"set {KEY_VAR} to use sarvam voices (narration text is sent to Sarvam AI), "
                             "or choose an offline voice with --voice")
        return key

    def status(self) -> EngineStatus:
        if not (self._env.get(KEY_VAR) or "").strip():
            return EngineStatus(False, f"needs {KEY_VAR}")
        return EngineStatus(True, f"online; {KEY_VAR} is set")

    def voices(self) -> list[str]:
        return list(SPEAKERS[DEFAULT_MODEL]) + [f"bulbul:v2/{s}" for s in SPEAKERS["bulbul:v2"]]

    def describe_voices(self) -> list[tuple[str, str]]:
        rows = [(v, "") for v in self.voices()]
        langs = ", ".join(LANGUAGES)
        rows.append(("bulbul:v4-flash/<name>_<lang>_<style>", "200+ persona voices; see Sarvam's voice list"))
        rows.append(("<voice>@<language>", f"en-IN by default; any of {langs}"))
        return rows

    def voice_key(self, voice: str) -> str:
        model, speaker, lang = split_voice(voice)
        return f"{model}/{speaker}@{lang}"

    def prepare(self, voice: str, confirm, root) -> None:
        self._key()
        model, speaker, lang = split_voice(voice)
        if not model or not speaker:
            raise VoiceError(f"sarvam voice '{voice}' needs a speaker (and a model before the slash, if any); "
                             "see `manimvox voices sarvam`")
        if model not in MODELS:
            raise VoiceError(f"no Sarvam model '{model}' (there are {', '.join(MODELS)})")
        if lang not in LANGUAGES:
            near = difflib.get_close_matches(lang, LANGUAGES, n=3)
            raise VoiceError(f"Sarvam has no language '{lang}'" + (f" (did you mean {', '.join(near)}?)" if near
                             else f"; it has {', '.join(LANGUAGES)}"))
        names = SPEAKERS.get(model)
        if names is not None and speaker not in names:
            near = difflib.get_close_matches(speaker, names, n=3)
            raise VoiceError(f"{model} has no speaker '{speaker}'" + (f" (did you mean {', '.join(near)}?)" if near
                             else "") + "; see `manimvox voices sarvam`")

    def synth(self, text: str, voice: str, speed: float, out: Path) -> None:
        model, speaker, lang = split_voice(voice)
        limit = MAX_CHARS.get(model, DEFAULT_MAX_CHARS)
        if len(text) > limit:
            raise VoiceError(f"a narration line is {len(text)} characters; Sarvam {model} takes at most {limit}")
        lo, hi = PACE.get(model, DEFAULT_PACE)
        if not lo <= speed <= hi:
            raise VoiceError(f"Sarvam {model} speaks at speed {lo}–{hi}; series.json has {speed}")
        key = self._key()
        body = {"text": text, "model": model, "speaker": speaker, "language_code": lang, "pace": speed,
                "speech_sample_rate": SAMPLE_RATE, "output_audio_codec": "wav"}
        try:
            reply = request("Sarvam", "POST", URL, body=json.dumps(body).encode("utf-8"), sleep=self._sleep,
                            headers={"api-subscription-key": key, "Content-Type": "application/json"},
                            secrets=[key])
        except VoiceError as e:
            if "HTTP 401" in str(e) or "HTTP 403" in str(e):
                raise VoiceError(f"Sarvam rejected the key in {KEY_VAR} (HTTP 401/403)") from None
            raise
        try:
            audios = json.loads(reply)["audios"]
            wav = base64.b64decode(audios[0], validate=True)
        except (ValueError, KeyError, IndexError, TypeError, binascii.Error):
            raise VoiceError("Sarvam returned an unreadable reply (no audio in it)") from None
        wav_bytes_to_wav(wav, out)
