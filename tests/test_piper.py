import hashlib
import json
import sys
import types

import numpy as np
import pytest
import soundfile as sf

from manimvox.voice import EngineNotInstalled, VoiceError
from manimvox.voice.download import RemoteFile
from manimvox.voice.engines import piper as pp

ONNX, CONF = b"onnx-model", b'{"audio": {"sample_rate": 22050}}'


def _index():
    def f(data):
        return {"size_bytes": len(data), "md5_digest": hashlib.md5(data).hexdigest()}
    return {"en_US-amy-medium": {
        "key": "en_US-amy-medium", "quality": "medium",
        "language": {"name_english": "English", "country_english": "United States"},
        "files": {"en/en_US/amy/medium/en_US-amy-medium.onnx": f(ONNX),
                  "en/en_US/amy/medium/en_US-amy-medium.onnx.json": f(CONF),
                  "en/en_US/amy/medium/MODEL_CARD": f(b"card")}}}


@pytest.fixture
def hub(tmp_path, monkeypatch):
    """A cache dir, a pinned index that matches our fake one, and a fetch that serves both."""
    monkeypatch.setenv("MANIMVOX_CACHE", str(tmp_path / "cache"))
    idx = json.dumps(_index()).encode()
    monkeypatch.setattr(pp, "INDEX", RemoteFile("voices.json", f"{pp.BASE}/voices.json",
                                                 hashlib.sha256(idx).hexdigest(), len(idx)))
    served = {"voices.json": idx, "en_US-amy-medium.onnx": ONNX, "en_US-amy-medium.onnx.json": CONF}
    urls = []

    def fetch(url, dest):
        urls.append(url)
        dest.write_bytes(served[url.rsplit("/", 1)[1]])

    return fetch, urls


@pytest.fixture
def stub_piper(monkeypatch):
    calls = {"load": [], "config": []}

    class Voice:
        @classmethod
        def load(cls, model_path, config_path=None, **kw):
            calls["load"].append(str(model_path))
            return cls()

        def synthesize_wav(self, text, wav_file, syn_config=None, **kw):
            calls["config"].append(syn_config)
            wav_file.setnchannels(1), wav_file.setsampwidth(2), wav_file.setframerate(22050)
            wav_file.writeframes(np.full(22050, 500, dtype="<i2").tobytes())

    class Config:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    monkeypatch.setitem(sys.modules, "piper", types.SimpleNamespace(PiperVoice=Voice, SynthesisConfig=Config))
    return calls


def test_not_installed_names_the_extra(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "piper", None)  # import piper → ImportError
    e = pp.PiperEngine()
    assert not e.status().ready and "manimvox[piper]" in e.status().detail
    with pytest.raises(EngineNotInstalled, match=r"manimvox\[piper\]"):
        e.prepare("en_US-amy-medium", lambda p: True, tmp_path)


def test_index_pinned_to_a_revision():
    assert pp.REV in pp.INDEX.url and len(pp.REV) == 40 and pp.INDEX.algo == "sha256"


def test_voice_files_pick_model_and_config_with_md5():
    files = pp.voice_files(_index(), "en_US-amy-medium")
    assert [f.name for f in files] == ["en_US-amy-medium.onnx", "en_US-amy-medium.onnx.json"]
    assert all(f.algo == "md5" and f.url.startswith(pp.BASE) for f in files)


def test_unknown_key_suggests_close_ones():
    with pytest.raises(VoiceError, match=r"no Piper voice 'en_US-amy-medum'.*en_US-amy-medium"):
        pp.voice_files(_index(), "en_US-amy-medum")


def test_prepare_downloads_index_without_asking_and_voice_after_asking(hub, stub_piper, tmp_path):
    fetch, urls = hub
    prompts = []
    pp.PiperEngine(fetch=fetch).prepare("en_US-amy-medium", lambda p: prompts.append(p) or True, tmp_path)
    assert len(prompts) == 1 and "Piper voice en_US-amy-medium" in prompts[0]
    assert [u.rsplit("/", 1)[1] for u in urls] == ["voices.json", "en_US-amy-medium.onnx", "en_US-amy-medium.onnx.json"]


def test_declined_voice_download_names_yes(hub, stub_piper, tmp_path):
    fetch, _ = hub
    with pytest.raises(VoiceError, match="--yes"):
        pp.PiperEngine(fetch=fetch).prepare("en_US-amy-medium", lambda p: False, tmp_path)


def test_synth_uses_length_scale_and_writes_wav(hub, stub_piper, tmp_path):
    fetch, _ = hub
    e = pp.PiperEngine(fetch=fetch)
    e.prepare("en_US-amy-medium", lambda p: True, tmp_path)
    e.synth("hello", "en_US-amy-medium", 1.25, tmp_path / "a.wav")
    assert stub_piper["config"][-1].length_scale == pytest.approx(0.8)
    assert stub_piper["load"][-1].endswith("en_US-amy-medium.onnx")
    info = sf.info(str(tmp_path / "a.wav"))
    assert (info.channels, info.subtype) == (1, "PCM_16")


def test_synth_before_prepare_says_how(hub, stub_piper, tmp_path):
    with pytest.raises(VoiceError, match="voices --prepare piper:en_US-amy-medium"):
        pp.PiperEngine().synth("hi", "en_US-amy-medium", 1.0, tmp_path / "a.wav")


def test_local_model_needs_its_json(stub_piper, tmp_path):
    (tmp_path / "voices").mkdir()
    (tmp_path / "voices" / "me.onnx").write_bytes(ONNX)
    with pytest.raises(VoiceError, match=r"me\.onnx\.json"):
        pp.PiperEngine().prepare("voices/me.onnx", lambda p: pytest.fail("asked"), tmp_path)
    (tmp_path / "voices" / "me.onnx.json").write_bytes(CONF)
    pp.PiperEngine().prepare("voices/me.onnx", lambda p: pytest.fail("asked"), tmp_path)


def test_voices_come_from_the_cached_index(hub, stub_piper, tmp_path):
    fetch, _ = hub
    e = pp.PiperEngine(fetch=fetch)
    assert e.voices() == []  # nothing cached, and listing never downloads
    e.prepare("en_US-amy-medium", lambda p: True, tmp_path)
    assert e.voices() == ["en_US-amy-medium"]
    assert e.describe_voices() == [("en_US-amy-medium", "English (United States), medium")]


@pytest.mark.piper
def test_real_piper_speaks(tmp_path):
    e = pp.PiperEngine()
    e.prepare("en_US-lessac-medium", lambda p: True, tmp_path)
    e.synth("Hello from manimvox.", "en_US-lessac-medium", 1.0, tmp_path / "a.wav")
    assert sf.info(str(tmp_path / "a.wav")).duration > 0.5
