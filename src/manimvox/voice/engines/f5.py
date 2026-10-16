"""F5-TTS: clones a voice from a short recording. Offline after a ~1.3 GB download.
The pretrained weights are CC-BY-NC: non-commercial use only."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import soundfile as sf

from ..base import EngineNotInstalled, EngineStatus, VoiceEngine, VoiceError, clone_reference
from ..download import engine_dir, file_digest


def accepted_marker() -> Path:
    return engine_dir("f5") / "licence-accepted"


def transcript_for(ref: Path) -> str:
    t = ref.with_suffix(".txt")
    return t.read_text(encoding="utf-8").strip() if t.is_file() else ""


def _installed() -> bool:
    """Detect f5-tts without importing it (that would pull in torch)."""
    try:
        return importlib.util.find_spec("f5_tts") is not None
    except (ImportError, ValueError):
        return False


def _api():
    try:
        from f5_tts.api import F5TTS
    except ImportError as e:
        raise EngineNotInstalled("f5", "f5") from e
    return F5TTS


class F5Engine(VoiceEngine):
    name = "f5"
    extra = "f5"
    default_voice = "clone=voice.wav"
    noncommercial = True
    licence = "f5-tts code MIT; F5-TTS pretrained weights CC-BY-NC 4.0 (non-commercial use only)"

    def __init__(self) -> None:
        self._model = None

    def status(self) -> EngineStatus:
        if not _installed():
            return EngineStatus(False, 'not installed: uv tool install "manimvox[f5]"')
        state = "model ready" if accepted_marker().exists() else "model downloads on first use (asks first)"
        return EngineStatus(True, f"{state}; voice is clone=<speaker.wav>, transcript in <speaker>.txt")

    def voice_key(self, voice: str) -> str:
        ref = clone_reference(voice)
        text = hashlib.sha256(transcript_for(ref).encode("utf-8")).hexdigest()[:8]
        return f"clone={file_digest(ref, 'sha256')[:16]}+{text}"

    def _load(self):
        if self._model is None:
            self._model = _api()(hf_cache_dir=str(accepted_marker().parent / "hf"))
        return self._model

    def prepare(self, voice: str, confirm, root: Path) -> None:
        _api()
        ref = clone_reference(voice, root)
        if accepted_marker().exists():
            return
        extra = "" if transcript_for(ref) else (f", plus a speech recogniser to transcribe the recording "
                                                f"(put its words in {ref.with_suffix('.txt').name} to skip that)")
        if not confirm(f"Download the F5-TTS model (about 1.3 GB{extra})? Its weights are CC-BY-NC: "
                       "non-commercial use only."):
            raise VoiceError("F5-TTS needs its model: rerun with --yes to download it (non-commercial use only), "
                             "or choose another voice with --voice")
        self._load()
        accepted_marker().parent.mkdir(parents=True, exist_ok=True)
        accepted_marker().write_text("F5TTS_v1_Base", encoding="utf-8")

    def synth(self, text: str, voice: str, speed: float, out: Path) -> None:
        if not accepted_marker().exists():
            raise VoiceError("F5-TTS is not set up; run `manimvox render` (it asks) or "
                             "`manimvox voices --prepare f5:clone=<speaker.wav>`")
        ref = clone_reference(voice)  # cwd = project root inside Manim
        raw = out.with_name(out.stem + ".raw.wav")
        try:
            self._load().infer(ref_file=str(ref), ref_text=transcript_for(ref), gen_text=text,
                               file_wave=str(raw), speed=speed, show_info=lambda *a, **k: None)
            data, sr = sf.read(str(raw), dtype="int16")
            sf.write(str(out), data if data.ndim == 1 else data.mean(axis=1).astype("int16"), sr,
                     format="WAV", subtype="PCM_16")
        finally:
            raw.unlink(missing_ok=True)
