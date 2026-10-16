"""The voice interface every text-to-speech engine implements."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

DEFAULT_VOICE = "kokoro:af_heart"


class VoiceError(Exception):
    """A voice cannot be used as asked. Never answered by switching voices silently."""


def install_hint(extra: str) -> str:
    """How to add an extra: manimvox is not on PyPI, and --force keeps the kokoro default voice."""
    wanted = "kokoro" if extra == "kokoro" else f"kokoro,{extra}"
    return f'uv tool install --force "manimvox[{wanted}] @ git+https://github.com/LaplacianAI/manimvox"'


class EngineNotInstalled(VoiceError):
    def __init__(self, engine: str, extra: str):
        super().__init__(f"voice engine '{engine}' is not installed: {install_hint(extra)}")
        self.engine, self.extra = engine, extra


class UnknownEngine(VoiceError):
    pass


@dataclass(frozen=True)
class VoiceSpec:
    engine: str
    voice: str

    def __str__(self) -> str:
        return f"{self.engine}:{self.voice}"


def parse_voice(spec: str) -> VoiceSpec:
    s = (spec or "").strip()
    if s and ":" not in s:
        return VoiceSpec("kokoro", s)  # explainer-playlist projects stored bare Kokoro ids
    engine, _, voice = s.partition(":")
    if not engine.strip() or not voice.strip():
        raise VoiceError(f"voice '{spec}' must be engine:voice, e.g. {DEFAULT_VOICE}")
    return VoiceSpec(engine.strip().lower(), voice.strip())


def resolve_voice(flag: str | None, project_voice: str | None, env: Mapping[str, str]) -> VoiceSpec:
    for s in (flag, project_voice, env.get("MANIMVOX_VOICE"), DEFAULT_VOICE):
        if s and s.strip():
            return parse_voice(s)
    raise AssertionError("unreachable: DEFAULT_VOICE is set")


class EngineStatus(NamedTuple):
    ready: bool
    detail: str


class VoiceEngine:
    """What every engine provides. Subclasses override what differs; the defaults suit an offline engine."""

    name: str = ""
    extra: str | None = None  # the pip extra that installs it
    licence: str = ""
    default_voice: str = ""  # used by `voices --prepare ENGINE` with no voice
    online: str = ""  # the service that receives narration text; "" when nothing leaves the machine
    noncommercial: bool = False  # the model's licence forbids commercial use

    def status(self) -> EngineStatus:
        raise NotImplementedError

    def voices(self) -> list[str]:
        return []

    def describe_voices(self) -> list[tuple[str, str]]:
        return [(v, "") for v in self.voices()]

    def prepare(self, voice: str, confirm: Callable[[str], bool], root: Path) -> None:
        """Everything a render needs, checked before Manim starts. May ask (download) through `confirm`.
        prepare() checks the voice exists, for every engine: a misspelt voice is refused here, not inside Manim."""
        return

    def synth(self, text: str, voice: str, speed: float, out: Path) -> None:
        """Write a mono 16-bit WAV of `text` to `out`. Runs inside Manim (cwd = project root); never prompts."""
        raise NotImplementedError

    def voice_key(self, voice: str) -> str:
        """What the audio cache keys on. Cloning engines hash the recording so a new one is not served stale lines."""
        return voice


def clone_reference(voice: str, root: Path | None = None) -> Path:
    """`clone=path/to/speaker.wav` -> that file. A relative path is taken from `root` (default: the working directory)."""
    if not voice.startswith("clone="):
        raise VoiceError(f"a cloning voice is written clone=<speaker.wav>, got '{voice}'")
    raw = voice[len("clone="):].strip()
    if not raw:
        raise VoiceError("clone= needs a path to a short recording of the speaker (6-30 s WAV)")
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = (Path(root) if root else Path.cwd()) / p
    if not p.is_file():
        raise VoiceError(f"speaker recording not found: {p}")
    return p
