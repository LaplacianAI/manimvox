"""Voices: one interface, many text-to-speech engines."""

from .base import (
    DEFAULT_VOICE,
    EngineNotInstalled,
    EngineStatus,
    UnknownEngine,
    VoiceEngine,
    VoiceError,
    VoiceSpec,
    clone_reference,
    parse_voice,
    resolve_voice,
)
from .cache import synth_cached
from .engines.fake import FakeEngine
from .pron import spoken_form
from .registry import engine_names, get_engine, register

register("fake", FakeEngine)

from .engines.kokoro import KokoroEngine

register("kokoro", KokoroEngine)

from .engines.say import SayEngine

register("say", SayEngine)

__all__ = [
    "DEFAULT_VOICE",
    "EngineNotInstalled",
    "EngineStatus",
    "FakeEngine",
    "KokoroEngine",
    "SayEngine",
    "UnknownEngine",
    "VoiceEngine",
    "VoiceError",
    "VoiceSpec",
    "clone_reference",
    "engine_names",
    "get_engine",
    "parse_voice",
    "register",
    "resolve_voice",
    "spoken_form",
    "synth_cached",
]
