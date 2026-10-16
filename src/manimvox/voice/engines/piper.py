"""Piper: fast, offline neural voices. Voice models download on first use from the pinned Piper index."""

from __future__ import annotations

import difflib
import json
import wave
from collections.abc import Callable
from pathlib import Path

from ..base import EngineNotInstalled, EngineStatus, VoiceEngine, VoiceError, install_hint
from ..download import RemoteFile, engine_dir, ensure_files, fetch, file_digest, verified

REV = "c10ece1aade47bb51c153c893d14e5bf8e5b7117"  # rhasspy/piper-voices, 2026-09-17
BASE = f"https://huggingface.co/rhasspy/piper-voices/resolve/{REV}"
INDEX = RemoteFile("voices.json", f"{BASE}/voices.json",
                   "b63d7a8663eb8bcf73d6545f1f7e4b49f9bcd2019e4fb6bd48e81642df183eed", 245852)


def voice_dir() -> Path:
    return engine_dir("piper")


def voice_files(index: dict, key: str) -> list[RemoteFile]:
    entry = index.get(key)
    if entry is None:
        near = difflib.get_close_matches(key, list(index), n=3)
        raise VoiceError(f"no Piper voice '{key}'" + (f" (did you mean {', '.join(near)}?)" if near else "")
                         + "; see `manimvox voices piper`")
    files = []
    for path, meta in sorted(entry["files"].items()):
        name = Path(path).name
        if name == "MODEL_CARD":  # the voice's licence, kept beside it so the engine's licence pointer is true
            name = f"{key}.MODEL_CARD"
        elif not path.endswith((".onnx", ".onnx.json")):
            continue
        files.append(RemoteFile(name, f"{BASE}/{path}", meta["md5_digest"], meta["size_bytes"], "md5"))
    return files


def _installed() -> bool:
    try:
        import piper  # noqa: F401
    except ImportError:
        return False
    return True


class PiperEngine(VoiceEngine):
    name = "piper"
    extra = "piper"
    default_voice = "en_US-libritts_r-medium"  # CC BY 4.0 (lessac's Blizzard licence is not clearly commercial)
    licence = "piper-tts GPL-3.0-or-later (optional extra); each voice has its own licence, saved beside it as <voice>.MODEL_CARD"

    def __init__(self, fetch: Callable[[str, Path], None] = fetch) -> None:
        self._fetch = fetch
        self._loaded: dict[str, object] = {}

    def _index(self, download: bool) -> dict | None:
        p = voice_dir() / INDEX.name
        if not verified(p, INDEX):
            if not download:
                return None
            ensure_files(voice_dir(), [INDEX], lambda prompt: True, "the Piper voice list", self._fetch)
        return json.loads(p.read_text(encoding="utf-8"))

    @staticmethod
    def _local(voice: str, root: Path | None) -> Path | None:
        if not voice.endswith(".onnx"):
            return None
        p = Path(voice).expanduser()
        return p if p.is_absolute() else (Path(root) if root else Path.cwd()) / p

    def status(self) -> EngineStatus:
        if not _installed():
            return EngineStatus(False, f"not installed: {install_hint('piper')}")
        have = len(list(voice_dir().glob("*.onnx"))) if voice_dir().exists() else 0
        return EngineStatus(True, f"{have} voice(s) downloaded in {voice_dir()}; others download on first use")

    def describe_voices(self) -> list[tuple[str, str]]:
        idx = self._index(download=False) or {}
        return [(k, f"{v['language']['name_english']} ({v['language']['country_english']}), {v['quality']}")
                for k, v in sorted(idx.items())]

    def voices(self) -> list[str]:
        return [k for k, _ in self.describe_voices()]

    def prepare(self, voice: str, confirm: Callable[[str], bool], root: Path) -> None:
        if not _installed():
            raise EngineNotInstalled("piper", "piper")
        local = self._local(voice, root)
        if local is not None:
            for p in (local, local.with_name(local.name + ".json")):
                if not p.is_file():
                    raise VoiceError(f"Piper model file not found: {p}")
            return
        files = voice_files(self._index(download=True), voice)
        ensure_files(voice_dir(), files, confirm, f"the Piper voice {voice}", self._fetch)

    def _model(self, voice: str) -> Path:
        local = self._local(voice, None)  # synth runs with cwd = project root
        if local is not None:
            return local
        idx = self._index(download=False)
        files = voice_files(idx, voice) if idx else []
        needed = [f for f in files if not f.name.endswith(".MODEL_CARD")]  # voices fetched before cards still work
        if not needed or not all(verified(voice_dir() / f.name, f) for f in needed):
            raise VoiceError(f"Piper voice '{voice}' is not downloaded; run `manimvox render` (it asks) or "
                             f"`manimvox voices --prepare piper:{voice}`")
        return voice_dir() / f"{voice}.onnx"

    def voice_key(self, voice: str) -> str:
        local = self._local(voice, None)  # cwd = project root; a replaced file at the same path is a new voice
        if local is not None and local.is_file():
            return f"{voice}@{file_digest(local, 'sha256')[:16]}"
        return voice

    def synth(self, text: str, voice: str, speed: float, out: Path) -> None:
        try:
            from piper import PiperVoice, SynthesisConfig
        except ImportError as e:
            raise EngineNotInstalled("piper", "piper") from e
        model = self._model(voice)
        key = str(model)
        if key not in self._loaded:
            self._loaded[key] = PiperVoice.load(key)
        with wave.open(str(out), "wb") as wf:
            self._loaded[key].synthesize_wav(text, wf, syn_config=SynthesisConfig(length_scale=1.0 / speed))
