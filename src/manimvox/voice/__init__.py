"""Voices: one interface, many text-to-speech engines."""

from .base import (
    DEFAULT_VOICE,
    EngineNotInstalled,
    EngineStatus,
    UnknownEngine,
    VoiceEngine,
    VoiceError,
    VoiceSpec,
    parse_voice,
    resolve_voice,
)
from .cache import synth_cached
from .fake import FakeEngine
from .pron import spoken_form
from .registry import engine_names, get_engine, register

register("fake", FakeEngine)

__all__ = [
    "DEFAULT_VOICE",
    "EngineNotInstalled",
    "EngineStatus",
    "FakeEngine",
    "UnknownEngine",
    "VoiceEngine",
    "VoiceError",
    "VoiceSpec",
    "engine_names",
    "get_engine",
    "parse_voice",
    "register",
    "resolve_voice",
    "spoken_form",
    "synth_cached",
]
