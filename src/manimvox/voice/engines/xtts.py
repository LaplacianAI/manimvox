"""XTTS-v2 (coqui-tts): clones a voice from a short recording. Offline after a ~1.9 GB download.
The model's licence (Coqui Public Model License) allows non-commercial use only."""

from __future__ import annotations

import contextlib
import importlib.util
import os
from collections.abc import Iterator
from pathlib import Path

import soundfile as sf

from ..base import EngineNotInstalled, EngineStatus, VoiceEngine, VoiceError, clone_reference
from ..download import engine_dir, file_digest

MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"


def accepted_marker() -> Path:
    return engine_dir("xtts") / "licence-accepted"


@contextlib.contextmanager
def tos_agreed() -> Iterator[None]:
    """coqui-tts asks on stdin unless COQUI_TOS_AGREED=1; set it only while loading, then restore."""
    old = os.environ.get("COQUI_TOS_AGREED")
    os.environ["COQUI_TOS_AGREED"] = "1"
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("COQUI_TOS_AGREED", None)
        else:
            os.environ["COQUI_TOS_AGREED"] = old


def _installed() -> bool:
    """Detect coqui-tts without importing it (that would pull in torch)."""
    try:
        return importlib.util.find_spec("TTS") is not None
    except (ImportError, ValueError):
        return False


def _api():
    try:
        from TTS.api import TTS
    except ImportError as e:
        raise EngineNotInstalled("xtts", "xtts") from e
    return TTS


class XTTSEngine(VoiceEngine):
    name = "xtts"
    extra = "xtts"
    default_voice = "clone=voice.wav"
    noncommercial = True
    licence = "coqui-tts MPL-2.0; XTTS-v2 model under the Coqui Public Model License (non-commercial use only)"

    def __init__(self) -> None:
        self._tts = None

    def status(self) -> EngineStatus:
        if not _installed():
            return EngineStatus(False, 'not installed: uv tool install "manimvox[xtts]"')
        if not accepted_marker().exists():
            return EngineStatus(True, "model downloads on first use (asks first); voice is clone=<speaker.wav>")
        return EngineStatus(True, "model ready; voice is clone=<speaker.wav>")

    def voice_key(self, voice: str) -> str:
        return "clone=" + file_digest(clone_reference(voice), "sha256")[:16]

    def _load(self):
        if self._tts is None:
            TTS = _api()
            with tos_agreed():
                tts = TTS(MODEL)
            try:
                import torch
                tts = tts.to("cuda" if torch.cuda.is_available() else "cpu")
            except ImportError:
                pass
            self._tts = tts
        return self._tts

    def prepare(self, voice: str, confirm, root: Path) -> None:
        _api()
        clone_reference(voice, root)
        if accepted_marker().exists():
            return
        if not confirm("Download the XTTS-v2 model (about 1.9 GB) and accept its licence, the Coqui Public "
                       "Model License, which allows non-commercial use only?"):
            raise VoiceError("XTTS-v2 needs its model and licence: rerun with --yes to accept (non-commercial "
                             "use only), or choose another voice with --voice")
        self._load()
        accepted_marker().parent.mkdir(parents=True, exist_ok=True)
        accepted_marker().write_text(MODEL, encoding="utf-8")

    def synth(self, text: str, voice: str, speed: float, out: Path) -> None:
        if not accepted_marker().exists():
            raise VoiceError("XTTS-v2 is not set up; run `manimvox render` (it asks) or "
                             "`manimvox voices --prepare xtts:clone=<speaker.wav>`")
        ref = clone_reference(voice)  # cwd = project root inside Manim
        raw = out.with_name(out.stem + ".raw.wav")
        try:
            self._load().tts_to_file(text=text, speaker_wav=str(ref), language="en", file_path=str(raw), speed=speed)
            data, sr = sf.read(str(raw), dtype="int16")
            sf.write(str(out), data if data.ndim == 1 else data.mean(axis=1).astype("int16"), sr,
                     format="WAV", subtype="PCM_16")
        finally:
            raw.unlink(missing_ok=True)
