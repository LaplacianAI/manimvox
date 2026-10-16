"""Engine lookup by name. Engines import their heavy dependencies lazily."""

from __future__ import annotations

from collections.abc import Callable

from .base import UnknownEngine, VoiceEngine

_FACTORIES: dict[str, Callable[[], VoiceEngine]] = {}
_LIVE: dict[str, VoiceEngine] = {}


def register(name: str, factory: Callable[[], VoiceEngine]) -> None:
    _FACTORIES[name] = factory


def engine_names() -> list[str]:
    return sorted(_FACTORIES)


def get_engine(name: str) -> VoiceEngine:
    if name not in _FACTORIES:
        raise UnknownEngine(f"unknown voice engine '{name}' (known: {', '.join(engine_names())})")
    if name not in _LIVE:
        _LIVE[name] = _FACTORIES[name]()
    return _LIVE[name]
