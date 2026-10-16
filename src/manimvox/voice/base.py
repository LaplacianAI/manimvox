"""The voice interface every text-to-speech engine implements."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, Protocol

DEFAULT_VOICE = "kokoro:af_heart"


class VoiceError(Exception):
    """A voice cannot be used as asked. Never answered by switching voices silently."""


class EngineNotInstalled(VoiceError):
    def __init__(self, engine: str, extra: str):
        super().__init__(f"voice engine '{engine}' is not installed: uv tool install \"manimvox[{extra}]\"")
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


class VoiceEngine(Protocol):
    name: str
    extra: str | None
    licence: str

    def status(self) -> EngineStatus: ...

    def voices(self) -> list[str]: ...

    def prepare(self, confirm: Callable[[str], bool]) -> None: ...

    def synth(self, text: str, voice: str, speed: float, out: Path) -> None: ...
