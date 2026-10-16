"""Kokoro-82M through kokoro-onnx: the default, offline voice."""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path

import numpy as np
import soundfile as sf

from .base import EngineNotInstalled, EngineStatus, VoiceError

MODEL_BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
MODELS: dict[str, tuple[str, int]] = {
    "kokoro-v1.0.onnx": ("7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5", 325532387),
    "voices-v1.0.bin": ("bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d", 28214398),
}


def cache_root(env: Mapping[str, str] = os.environ, platform: str = sys.platform) -> Path:
    if env.get("MANIMVOX_CACHE"):
        return Path(env["MANIMVOX_CACHE"])
    if platform.startswith("win") and env.get("LOCALAPPDATA"):
        return Path(env["LOCALAPPDATA"]) / "manimvox"
    if env.get("XDG_CACHE_HOME"):
        return Path(env["XDG_CACHE_HOME"]) / "manimvox"
    return Path.home() / ".cache" / "manimvox"


def model_dir() -> Path:
    return cache_root() / "kokoro"


def _fetch(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f, length=1 << 20)


def _ok(path: Path, sha: str, size: int) -> bool:
    mark = path.with_name(path.name + ".sha256")
    return (
        path.exists()
        and path.stat().st_size == size
        and mark.exists()
        and mark.read_text(encoding="utf-8").strip() == sha
    )


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_models(confirm: Callable[[str], bool], fetch: Callable[[str, Path], None] = _fetch) -> Path:
    d = model_dir()
    missing = [n for n, (sha, size) in MODELS.items() if not _ok(d / n, sha, size)]
    if not missing:
        return d
    mb = sum(MODELS[n][1] for n in missing) / 1e6
    if not confirm(f"Download the Kokoro voice model ({mb:.0f} MB) into {d}?"):
        raise VoiceError(
            "the Kokoro model is needed: rerun with --yes to download it, or choose another voice with --voice"
        )
    d.mkdir(parents=True, exist_ok=True)
    for n in missing:
        sha, _ = MODELS[n]
        tmp = d / f"{n}.part"
        try:
            fetch(f"{MODEL_BASE}/{n}", tmp)
            if _sha256(tmp) != sha:
                raise VoiceError(f"checksum mismatch for {n}; the download was discarded, try again")
            os.replace(tmp, d / n)
            (d / f"{n}.sha256").write_text(sha, encoding="utf-8")
        finally:
            tmp.unlink(missing_ok=True)
    return d


class KokoroEngine:
    name = "kokoro"
    extra = "kokoro"
    licence = "Kokoro-82M weights Apache-2.0; kokoro-onnx MIT (verify upstream before release)"

    def __init__(self) -> None:
        self._k = None

    def _models_ready(self) -> bool:
        return all(_ok(model_dir() / n, sha, size) for n, (sha, size) in MODELS.items())

    def status(self) -> EngineStatus:
        try:
            import kokoro_onnx  # noqa: F401
        except ImportError:
            return EngineStatus(False, 'not installed: uv tool install "manimvox[kokoro]"')
        if not self._models_ready():
            return EngineStatus(False, f"model files not downloaded ({model_dir()}); a render will offer to")
        return EngineStatus(True, f"models in {model_dir()}")

    def prepare(self, confirm: Callable[[str], bool]) -> None:
        try:
            import kokoro_onnx  # noqa: F401
        except ImportError as e:
            raise EngineNotInstalled("kokoro", "kokoro") from e
        ensure_models(confirm)

    def voices(self) -> list[str]:
        if not self._models_ready():
            return []
        return sorted(np.load(model_dir() / "voices-v1.0.bin").files)

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
