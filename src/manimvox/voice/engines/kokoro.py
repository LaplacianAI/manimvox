"""Kokoro-82M through kokoro-onnx: the default, offline voice."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import soundfile as sf

from ..base import EngineNotInstalled, EngineStatus, VoiceEngine, VoiceError
from ..download import RemoteFile, cache_root, ensure_files, fetch, verified

__all__ = ["MODELS", "MODEL_BASE", "KokoroEngine", "cache_root", "ensure_models", "model_dir"]

MODEL_BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
MODELS: dict[str, tuple[str, int]] = {
    "kokoro-v1.0.onnx": ("7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5", 325532387),
    "voices-v1.0.bin": ("bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d", 28214398),
}


def model_dir() -> Path:
    return cache_root() / "kokoro"


def _files() -> list[RemoteFile]:
    return [RemoteFile(n, f"{MODEL_BASE}/{n}", sha, size) for n, (sha, size) in MODELS.items()]


def ensure_models(confirm: Callable[[str], bool], fetch: Callable[[str, Path], None] = fetch) -> Path:
    return ensure_files(model_dir(), _files(), confirm, "the Kokoro voice model", fetch)


class KokoroEngine(VoiceEngine):
    name = "kokoro"
    extra = "kokoro"
    licence = "Kokoro-82M weights Apache-2.0; kokoro-onnx MIT (verify upstream before release)"
    default_voice = "af_heart"

    def __init__(self) -> None:
        self._k = None
        self._voices: list[str] | None = None

    def _models_ready(self) -> bool:
        return all(verified(model_dir() / f.name, f) for f in _files())

    def status(self) -> EngineStatus:
        try:
            import kokoro_onnx  # noqa: F401
        except ImportError:
            return EngineStatus(False, 'not installed: uv tool install "manimvox[kokoro]"')
        if not self._models_ready():
            return EngineStatus(False, f"model files not downloaded ({model_dir()}); a render will offer to")
        return EngineStatus(True, f"models in {model_dir()}")

    def prepare(self, voice: str, confirm: Callable[[str], bool], root: Path) -> None:
        try:
            import kokoro_onnx  # noqa: F401
        except ImportError as e:
            raise EngineNotInstalled("kokoro", "kokoro") from e
        ensure_models(confirm)
        have = self.voices()
        if voice not in have:
            raise VoiceError(f"Kokoro has no voice '{voice}' (e.g. {', '.join(have[:6])}); see `manimvox voices kokoro`")

    def voices(self) -> list[str]:
        if self._voices is None:
            if not self._models_ready():
                return []  # never cache an empty list: the models may arrive later in this process
            with np.load(model_dir() / "voices-v1.0.bin") as z:
                self._voices = sorted(z.files)
        return self._voices

    def synth(self, text: str, voice: str, speed: float, out: Path) -> None:
        try:
            from kokoro_onnx import Kokoro
        except ImportError as e:
            raise EngineNotInstalled("kokoro", "kokoro") from e
        if not self._models_ready():
            raise VoiceError(
                "Kokoro model files are missing; run `manimvox render` or "
                "`manimvox voices --prepare kokoro` to download them"
            )
        have = self.voices()
        if voice not in have:
            raise VoiceError(f"Kokoro has no voice '{voice}' (e.g. {', '.join(have[:6])})")
        if self._k is None:
            d = model_dir()
            self._k = Kokoro(str(d / "kokoro-v1.0.onnx"), str(d / "voices-v1.0.bin"))
        samples, sr = self._k.create(text, voice=voice, speed=speed, lang="en-us")
        sf.write(str(out), samples, sr, format="WAV")
