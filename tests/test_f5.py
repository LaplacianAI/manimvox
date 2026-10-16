import sys
import types

import numpy as np
import pytest
import soundfile as sf

from manimvox.voice import EngineNotInstalled, VoiceError
from manimvox.voice.engines import f5


@pytest.fixture
def stub_f5(monkeypatch, tmp_path):
    monkeypatch.setenv("MANIMVOX_CACHE", str(tmp_path / "cache"))
    calls = {"init": [], "infer": []}

    class F5TTS:
        def __init__(self, **kw):
            calls["init"].append(kw)

        def infer(self, ref_file, ref_text, gen_text, file_wave=None, speed=1.0, **kw):
            calls["infer"].append(
                {"ref_file": ref_file, "ref_text": ref_text, "gen_text": gen_text, "speed": speed}
            )
            sf.write(file_wave, np.zeros(24000, dtype=np.float32), 24000, format="WAV", subtype="FLOAT")
            return None, 24000, None

    api = types.ModuleType("f5_tts.api")
    api.F5TTS = F5TTS
    monkeypatch.setitem(sys.modules, "f5_tts", types.ModuleType("f5_tts"))
    monkeypatch.setitem(sys.modules, "f5_tts.api", api)
    rec = tmp_path / "me.wav"
    sf.write(str(rec), np.zeros(24000 * 8, dtype=np.int16), 24000, format="WAV", subtype="PCM_16")
    return calls, rec


def test_flagged_non_commercial():
    assert f5.F5Engine.noncommercial and "CC-BY-NC" in f5.F5Engine.licence


def test_not_installed(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "f5_tts.api", None)
    with pytest.raises(EngineNotInstalled, match=r"manimvox\[f5\]"):
        f5.F5Engine().prepare("clone=me.wav", lambda p: True, tmp_path)


def test_prompt_mentions_transcriber_only_without_transcript(stub_f5, tmp_path):
    prompts = []
    f5.F5Engine().prepare("clone=me.wav", lambda p: prompts.append(p) or True, tmp_path)
    assert "speech recogniser" in prompts[0] and "CC-BY-NC" in prompts[0]


def test_model_files_go_to_the_manimvox_cache(stub_f5, tmp_path):
    calls, _ = stub_f5
    f5.F5Engine().prepare("clone=me.wav", lambda p: True, tmp_path)
    assert calls["init"][0]["hf_cache_dir"] == str(f5.accepted_marker().parent / "hf")


def test_declined(stub_f5, tmp_path):
    calls, _ = stub_f5
    with pytest.raises(VoiceError, match="--yes"):
        f5.F5Engine().prepare("clone=me.wav", lambda p: False, tmp_path)
    assert calls["init"] == []


def test_synth_passes_transcript_and_speed(stub_f5, tmp_path, monkeypatch):
    calls, rec = stub_f5
    (tmp_path / "me.txt").write_text("  This is me talking. \n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    e = f5.F5Engine()
    e.prepare("clone=me.wav", lambda p: True, tmp_path)
    e.synth("Hello.", "clone=me.wav", 0.9, tmp_path / "a.wav")
    assert calls["infer"][-1] == {"ref_file": str(rec), "ref_text": "This is me talking.", "gen_text": "Hello.",
                                  "speed": 0.9}
    assert sf.info(str(tmp_path / "a.wav")).subtype == "PCM_16"


def test_voice_key_changes_with_transcript(stub_f5, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    e = f5.F5Engine()
    k1 = e.voice_key("clone=me.wav")
    (tmp_path / "me.txt").write_text("words", encoding="utf-8")
    assert e.voice_key("clone=me.wav") != k1


def test_status_not_installed_when_spec_absent(monkeypatch):
    monkeypatch.setattr(f5.importlib.util, "find_spec", lambda name: None)
    st = f5.F5Engine().status()
    assert not st.ready and "manimvox[f5]" in st.detail


def test_status_treats_broken_spec_as_not_installed(monkeypatch):
    def boom(name):
        raise ValueError("f5_tts.__spec__ is None")

    monkeypatch.setattr(f5.importlib.util, "find_spec", boom)
    assert not f5.F5Engine().status().ready


def test_status_never_imports_f5_api(monkeypatch, tmp_path):
    monkeypatch.setenv("MANIMVOX_CACHE", str(tmp_path / "cache"))
    monkeypatch.delitem(sys.modules, "f5_tts.api", raising=False)
    monkeypatch.setattr(f5.importlib.util, "find_spec", lambda name: object())
    assert f5.F5Engine().status().ready
    assert "f5_tts.api" not in sys.modules
