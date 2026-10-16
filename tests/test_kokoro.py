import hashlib

import pytest

from manimvox.voice import VoiceError, get_engine
from manimvox.voice import kokoro as kk


@pytest.fixture
def fake_models(tmp_path, monkeypatch):
    """Two tiny stand-in model files with their real-looking metadata swapped for test hashes."""
    monkeypatch.setenv("MANIMVOX_CACHE", str(tmp_path))
    blobs = {"kokoro-v1.0.onnx": b"onnx-bytes", "voices-v1.0.bin": b"voice-bytes"}
    monkeypatch.setattr(kk, "MODELS", {n: (hashlib.sha256(b).hexdigest(), len(b)) for n, b in blobs.items()})
    calls = []

    def fetch(url, dest):
        calls.append(url)
        dest.write_bytes(blobs[url.rsplit("/", 1)[1]])

    return blobs, calls, fetch


def test_declined_download_raises_and_names_yes(fake_models):
    _, calls, fetch = fake_models
    with pytest.raises(VoiceError, match="--yes"):
        kk.ensure_models(lambda prompt: False, fetch)
    assert calls == []


def test_accepted_download_writes_and_marks_files(fake_models):
    blobs, calls, fetch = fake_models
    d = kk.ensure_models(lambda prompt: True, fetch)
    assert sorted(p.name for p in d.iterdir() if not p.name.endswith(".sha256")) == sorted(blobs)
    assert len(calls) == 2
    calls.clear()
    kk.ensure_models(lambda prompt: pytest.fail("asked again"), fetch)  # already present: no prompt, no fetch
    assert calls == []


def test_checksum_mismatch_deletes_file(fake_models):
    def bad_fetch(url, dest):
        dest.write_bytes(b"tampered")

    with pytest.raises(VoiceError, match="checksum"):
        kk.ensure_models(lambda p: True, bad_fetch)
    assert not any(kk.model_dir().glob("*.onnx"))


def test_network_failure_is_a_voice_error_and_leaves_no_part_file(fake_models):
    def dropped_fetch(url, dest):
        dest.write_bytes(b"partial")
        raise OSError("network down")

    with pytest.raises(VoiceError, match="could not download"):
        kk.ensure_models(lambda p: True, dropped_fetch)
    assert not list(kk.model_dir().glob("*.part"))


def test_prompt_states_size_and_place(fake_models):
    _, _, fetch = fake_models
    seen = []
    kk.ensure_models(lambda prompt: seen.append(prompt) or True, fetch)
    assert "MB" in seen[0] and str(kk.model_dir()) in seen[0]


def test_cache_root_per_os(tmp_path):
    assert kk.cache_root({"MANIMVOX_CACHE": str(tmp_path)}, "win32") == tmp_path
    assert kk.cache_root({"LOCALAPPDATA": str(tmp_path)}, "win32") == tmp_path / "manimvox"
    assert kk.cache_root({"XDG_CACHE_HOME": str(tmp_path)}, "linux") == tmp_path / "manimvox"
    assert kk.cache_root({}, "darwin").parts[-2:] == (".cache", "manimvox")


def test_status_reports_missing_models(fake_models):
    st = get_engine("kokoro").status()
    assert not st.ready and ("model" in st.detail or "manimvox[kokoro]" in st.detail)


@pytest.mark.kokoro
def test_real_kokoro_speaks(tmp_path):
    import soundfile as sf

    out = tmp_path / "a.wav"
    get_engine("kokoro").synth("Hello from manimvox.", "af_heart", 1.0, out)
    data, sr = sf.read(out)
    assert sr == 24000 and len(data) / sr > 0.8
