import sys
import types

import pytest
import soundfile as sf

from manimvox.voice import EngineNotInstalled, VoiceError
from manimvox.voice.engines import edge as ed
from tests.media import make_mp3


@pytest.fixture
def stub_edge(monkeypatch, tmp_path):
    state = {"made": [], "fail": 0}
    src = make_mp3(tmp_path / "src.mp3")

    class Communicate:
        def __init__(self, text, voice, rate="+0%", **kw):
            state["made"].append((text, voice, rate))

        def save_sync(self, path):
            if state["fail"]:
                state["fail"] -= 1
                raise ConnectionResetError("dropped")
            with open(path, "wb") as f:
                f.write(src.read_bytes())

    async def list_voices():
        return [{"ShortName": "en-US-AriaNeural", "Locale": "en-US", "Gender": "Female"},
                {"ShortName": "en-GB-RyanNeural", "Locale": "en-GB", "Gender": "Male"}]

    monkeypatch.setitem(sys.modules, "edge_tts", types.SimpleNamespace(Communicate=Communicate, list_voices=list_voices))
    return state


@pytest.mark.parametrize("speed, arg", [(1.0, "+0%"), (1.15, "+15%"), (0.8, "-20%")])
def test_rate_arg(speed, arg):
    assert ed.rate_arg(speed) == arg


def test_not_installed(monkeypatch):
    monkeypatch.setitem(sys.modules, "edge_tts", None)
    with pytest.raises(EngineNotInstalled, match=r"manimvox\[edge\]"):
        ed.EdgeEngine().prepare("en-US-AriaNeural", lambda p: True, None)


def test_engine_is_marked_online():
    assert "Microsoft" in ed.EdgeEngine.online


def test_synth_converts_mp3_to_wav(stub_edge, tmp_path):
    ed.EdgeEngine(sleep=lambda t: None).synth("hello", "en-US-AriaNeural", 1.1, tmp_path / "a.wav")
    assert stub_edge["made"][-1] == ("hello", "en-US-AriaNeural", "+10%")
    info = sf.info(str(tmp_path / "a.wav"))
    assert (info.channels, info.subtype) == (1, "PCM_16") and info.duration > 0.5
    assert not list(tmp_path.glob("*.mp3.part")) and not list(tmp_path.glob("a.*.mp3"))


def test_transient_failure_retries(stub_edge, tmp_path):
    stub_edge["fail"] = 2
    ed.EdgeEngine(sleep=lambda t: None).synth("hello", "en-US-AriaNeural", 1.0, tmp_path / "a.wav")
    assert len(stub_edge["made"]) == 3


def test_persistent_failure_is_a_voice_error_naming_the_voice_list(stub_edge, tmp_path):
    stub_edge["fail"] = 99
    with pytest.raises(VoiceError, match=r"edge-tts failed after 4 tries.*manimvox voices edge"):
        ed.EdgeEngine(sleep=lambda t: None).synth("hello", "en-US-AriaNeural", 1.0, tmp_path / "a.wav")


def test_voices_list(stub_edge):
    e = ed.EdgeEngine(sleep=lambda t: None)
    assert e.voices() == ["en-GB-RyanNeural", "en-US-AriaNeural"]
    assert ("en-US-AriaNeural", "en-US, Female") in e.describe_voices()
