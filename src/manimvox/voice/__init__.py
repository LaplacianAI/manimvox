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

from .engines.edge import EdgeEngine

register("edge", EdgeEngine)

from .engines.elevenlabs import ElevenLabsEngine

register("elevenlabs", ElevenLabsEngine)

from .engines.f5 import F5Engine

register("f5", F5Engine)

from .engines.kokoro import KokoroEngine

register("kokoro", KokoroEngine)

from .engines.openai import OpenAIEngine

register("openai", OpenAIEngine)

from .engines.piper import PiperEngine

register("piper", PiperEngine)

from .engines.say import SayEngine

register("say", SayEngine)

from .engines.xtts import XTTSEngine

register("xtts", XTTSEngine)

__all__ = [
    "DEFAULT_VOICE",
    "EdgeEngine",
    "ElevenLabsEngine",
    "EngineNotInstalled",
    "EngineStatus",
    "F5Engine",
    "FakeEngine",
    "KokoroEngine",
    "OpenAIEngine",
    "PiperEngine",
    "SayEngine",
    "UnknownEngine",
    "VoiceEngine",
    "VoiceError",
    "VoiceSpec",
    "XTTSEngine",
    "clone_reference",
    "engine_names",
    "get_engine",
    "parse_voice",
    "register",
    "resolve_voice",
    "spoken_form",
    "synth_cached",
]
