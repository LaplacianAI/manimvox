import sys
import types

import numpy as np
import pytest
import soundfile as sf

from manimvox.voice import EngineNotInstalled, VoiceError
from manimvox.voice.engines import xtts as xt


@pytest.fixture
def stub_tts(monkeypatch, tmp_path):
    monkeypatch.setenv("MANIMVOX_CACHE", str(tmp_path / "cache"))
    monkeypatch.delenv("COQUI_TOS_AGREED", raising=False)
    calls = {"init": [], "tts": [], "tos": []}

    class TTS:
        def __init__(self, model_name, **kw):
            import os
            calls["init"].append(model_name)
            calls["tos"].append(os.environ.get("COQUI_TOS_AGREED"))

        def to(self, device):
            return self

        def tts_to_file(self, text, speaker_wav=None, language=None, file_path=None, **kw):
            calls["tts"].append(dict(text=text, speaker_wav=speaker_wav, language=language, **kw))
            sf.write(file_path, np.zeros(24000, dtype=np.float32), 24000, format="WAV", subtype="FLOAT")

    api = types.ModuleType("TTS.api")
    api.TTS = TTS
    monkeypatch.setitem(sys.modules, "TTS", types.ModuleType("TTS"))
    monkeypatch.setitem(sys.modules, "TTS.api", api)
    rec = tmp_path / "me.wav"
    sf.write(str(rec), np.zeros(24000 * 8, dtype=np.int16), 24000, format="WAV", subtype="PCM_16")
    return calls, rec


def test_flagged_non_commercial():
    assert xt.XTTSEngine.noncommercial and "Coqui Public Model License" in xt.XTTSEngine.licence


def test_not_installed(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "TTS.api", None)
    with pytest.raises(EngineNotInstalled, match=r"manimvox\[xtts\]"):
        xt.XTTSEngine().prepare("clone=me.wav", lambda p: True, tmp_path)


def test_prepare_resolves_against_root(stub_tts, tmp_path):
    with pytest.raises(VoiceError, match="not found"):
        xt.XTTSEngine().prepare("clone=voices/none.wav", lambda p: True, tmp_path)
    xt.XTTSEngine().prepare("clone=me.wav", lambda p: True, tmp_path)  # tmp_path/me.wav exists


def test_declined_licence_downloads_nothing(stub_tts, tmp_path):
    calls, _ = stub_tts
    with pytest.raises(VoiceError, match=r"--yes.*non-commercial"):
        xt.XTTSEngine().prepare("clone=me.wav", lambda p: False, tmp_path)
    assert calls["init"] == [] and not xt.accepted_marker().exists()


def test_accept_loads_model_once_with_tos_and_remembers(stub_tts, tmp_path):
    calls, _ = stub_tts
    prompts = []
    xt.XTTSEngine().prepare("clone=me.wav", lambda p: prompts.append(p) or True, tmp_path)
    assert "Coqui Public Model License" in prompts[0] and "GB" in prompts[0]
    assert calls["init"] == [xt.MODEL] and calls["tos"] == ["1"]
    assert xt.accepted_marker().exists()
    import os
    assert os.environ.get("COQUI_TOS_AGREED") is None  # restored after loading
    xt.XTTSEngine().prepare("clone=me.wav", lambda p: pytest.fail("asked again"), tmp_path)


def test_synth_before_acceptance_says_how(stub_tts, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(VoiceError, match="voices --prepare xtts"):
        xt.XTTSEngine().synth("hi", "clone=me.wav", 1.0, tmp_path / "a.wav")


def test_synth_clones_with_speed_and_writes_16_bit(stub_tts, tmp_path, monkeypatch):
    calls, rec = stub_tts
    monkeypatch.chdir(tmp_path)  # the Manim subprocess runs in the project root
    e = xt.XTTSEngine()
    e.prepare("clone=me.wav", lambda p: True, tmp_path)
    e.synth("Hello.", "clone=me.wav", 1.1, tmp_path / "a.wav")
    assert calls["tts"][-1] == {"text": "Hello.", "speaker_wav": str(rec), "language": "en", "speed": 1.1}
    assert sf.info(str(tmp_path / "a.wav")).subtype == "PCM_16"


def test_voice_key_changes_with_recording(stub_tts, tmp_path, monkeypatch):
    _, rec = stub_tts
    monkeypatch.chdir(tmp_path)
    e = xt.XTTSEngine()
    k1 = e.voice_key("clone=me.wav")
    sf.write(str(rec), np.ones(24000, dtype=np.int16), 24000, format="WAV", subtype="PCM_16")
    assert e.voice_key("clone=me.wav") != k1 and k1.startswith("clone=")


def test_status_not_installed_when_spec_absent(monkeypatch):
    monkeypatch.setattr(xt.importlib.util, "find_spec", lambda name: None)
    st = xt.XTTSEngine().status()
    assert not st.ready and "manimvox[xtts]" in st.detail


def test_status_treats_broken_spec_as_not_installed(monkeypatch):
    def boom(name):
        raise ValueError("TTS.__spec__ is None")
    monkeypatch.setattr(xt.importlib.util, "find_spec", boom)
    assert not xt.XTTSEngine().status().ready


def test_status_never_imports_tts_api(monkeypatch, tmp_path):
    monkeypatch.setenv("MANIMVOX_CACHE", str(tmp_path / "cache"))
    monkeypatch.delitem(sys.modules, "TTS.api", raising=False)
    monkeypatch.setattr(xt.importlib.util, "find_spec", lambda name: object())
    assert xt.XTTSEngine().status().ready
    assert "TTS.api" not in sys.modules
