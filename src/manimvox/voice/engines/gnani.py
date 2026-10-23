"""Gnani.ai (Vachana Timbre) text-to-speech over HTTPS, for Indian languages. Needs GNANI_API_KEY;
narration text goes to Gnani.ai.

A voice is `[model/]Name[@language]`: `Kaveri`, `Shivani@hi-IN`, `timbre-v3.0/Avinash@ta-IN`.
With no model, the model whose catalogue has the voice is used; with no language, Gnani detects it (`auto`).
"""

from __future__ import annotations

import difflib
import json
import os
import time
from collections.abc import Callable, Mapping
from pathlib import Path

from ..base import EngineStatus, VoiceEngine, VoiceError
from ..convert import wav_bytes_to_wav
from ..http import request

URL = "https://api.vachana.ai/api/v1/tts/inference"
KEY_VAR = "GNANI_API_KEY"
DEFAULT_MODEL = "timbre-v2.5"
DEFAULT_LANGUAGE = "auto"
SAMPLE_RATE = 24000
SPEED_RANGE = (0.85, 1.15)
LANGUAGES = ("auto", "hi-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "mr-IN", "pa-IN", "bn-IN", "gu-IN",
             "hi-en")
# each voice with the language it speaks best; v3.0 voices speak every language equally
VOICES = {
    "timbre-v2.5": {
        "Ambuja": "hi-IN", "Asmita": "ta-IN", "Bhavna": "hi-IN", "Brinda": "ta-IN", "Chitra": "hi-IN",
        "Deepak": "hi-IN", "Devika": "en-IN", "Dhruva": "bn-IN", "Falak": "gu-IN", "Girish": "en-IN",
        "Hemraj": "hi-IN", "Ishaan": "mr-IN", "Jalaj": "hi-IN", "Jwala": "hi-IN", "Kaveri": "en-IN",
        "Kavin": "kn-IN", "Kirra": "bn-IN", "Lavanya": "te-IN", "Lehara": "te-IN", "Mehuli": "pa-IN",
        "Nalini": "hi-IN", "Noopur": "ta-IN", "Omkar": "hi-IN", "Poorvi": "hi-en", "Pranav": "en-IN",
        "Reshma": "ml-IN", "Riyaan": "ml-IN", "Roopesh": "hi-IN", "Saanvi": "kn-IN", "Shlok": "en-IN",
        "Suhana": "te-IN", "Trisha": "ta-IN", "Trupti": "en-IN", "Urmila": "hi-IN", "Varuni": "te-IN",
        "Vedika": "ta-IN", "Veera": "gu-IN", "Vikrant": "hi-IN", "Yashvi": "hi-IN", "Yukti": "te-IN",
        "Zahira": "mr-IN", "Zayan": "pa-IN",
    },
    "timbre-v3.0": dict.fromkeys(
        ("Avinash", "Chetana", "Devansh", "Harshad", "Kalpana", "Lakshmi", "Prakash", "Riyaa", "Shivani",
         "Shubham", "Tarika", "Vasudha", "Yashraj"), "any"),
}


def split_voice(voice: str) -> tuple[str, str, str]:
    """`[model/]Name[@language]` -> (model, Name, language), with the name in the catalogue's spelling."""
    rest, sep, lang = voice.rpartition("@")
    if not sep:
        rest, lang = voice, DEFAULT_LANGUAGE
    model, sep, name = rest.rpartition("/")
    name, model = name.strip(), model.strip().lower()
    if model and not model.startswith("timbre-"):
        model = f"timbre-{model}"
    for m, names in VOICES.items():
        if (not sep or m == model) and (hit := next((n for n in names if n.lower() == name.lower()), None)):
            return m, hit, lang.strip()
    return (model if sep else DEFAULT_MODEL), name, lang.strip()


class GnaniEngine(VoiceEngine):
    name = "gnani"
    extra = "cloud"
    default_voice = "Kaveri"
    online = "Gnani.ai"
    licence = "Gnani.ai terms; paid per character"

    def __init__(self, env: Mapping[str, str] = os.environ, sleep: Callable[[float], None] = time.sleep) -> None:
        self._env, self._sleep = env, sleep

    def _key(self) -> str:
        key = (self._env.get(KEY_VAR) or "").strip()
        if not key:
            raise VoiceError(f"set {KEY_VAR} to use gnani voices (narration text is sent to Gnani.ai), "
                             "or choose an offline voice with --voice")
        return key

    def status(self) -> EngineStatus:
        if not (self._env.get(KEY_VAR) or "").strip():
            return EngineStatus(False, f"needs {KEY_VAR}")
        return EngineStatus(True, f"online; {KEY_VAR} is set")

    def voices(self) -> list[str]:
        return sorted(VOICES["timbre-v2.5"]) + [f"timbre-v3.0/{n}" for n in sorted(VOICES["timbre-v3.0"])]

    def describe_voices(self) -> list[tuple[str, str]]:
        rows = [(v, f"best in {VOICES['timbre-v2.5'][v]}" if "/" not in v else "every language")
                for v in self.voices()]
        rows.append(("<voice>@<language>", f"auto by default; also {', '.join(LANGUAGES[1:])}"))
        return rows

    def voice_key(self, voice: str) -> str:
        model, name, lang = split_voice(voice)
        return f"{model}/{name}@{lang}"

    def prepare(self, voice: str, confirm, root) -> None:
        self._key()
        model, name, lang = split_voice(voice)
        if not model or not name:
            raise VoiceError(f"gnani voice '{voice}' needs a voice name (and a model before the slash, if any); "
                             "see `manimvox voices gnani`")
        if model not in VOICES:
            raise VoiceError(f"no Gnani model '{model}' (there are {', '.join(VOICES)})")
        if name not in VOICES[model]:
            other = next((m for m, names in VOICES.items() if name.lower() in map(str.lower, names)), None)
            near = difflib.get_close_matches(name, list(VOICES[model]), n=3)
            hint = (f" ({name} is a {other} voice)" if other else
                    f" (did you mean {', '.join(near)}?)" if near else "")
            raise VoiceError(f"{model} has no voice '{name}'{hint}; see `manimvox voices gnani`")
        if lang not in LANGUAGES:
            near = difflib.get_close_matches(lang, LANGUAGES, n=3)
            raise VoiceError(f"Gnani has no language '{lang}'" + (f" (did you mean {', '.join(near)}?)" if near
                             else f"; it has {', '.join(LANGUAGES)}"))

    def synth(self, text: str, voice: str, speed: float, out: Path) -> None:
        lo, hi = SPEED_RANGE
        if not lo <= speed <= hi:
            raise VoiceError(f"Gnani speaks at speed {lo}–{hi}; series.json has {speed}")
        key = self._key()
        model, name, lang = split_voice(voice)
        body = {"text": text, "model": model, "voice": name, "language": lang, "speed": speed,
                "audio_config": {"sample_rate": SAMPLE_RATE, "num_channels": 1, "sample_width": 2,
                                 "encoding": "linear_pcm", "container": "wav"}}
        try:
            wav = request("Gnani.ai", "POST", URL, body=json.dumps(body).encode("utf-8"), sleep=self._sleep,
                          headers={"X-API-Key-ID": key, "Content-Type": "application/json"}, secrets=[key])
        except VoiceError as e:
            if "HTTP 401" in str(e) or "HTTP 403" in str(e):
                raise VoiceError(f"Gnani.ai rejected the key in {KEY_VAR}, or the account has no credits "
                                 "(HTTP 401/403)") from None
            raise
        wav_bytes_to_wav(wav, out)
