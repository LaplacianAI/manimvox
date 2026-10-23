import io

import numpy as np
import pytest
import soundfile as sf

from manimvox.voice import VoiceError, http
from manimvox.voice.engines import gnani as gn
from tests.http_fakes import Server

KEY = {"GNANI_API_KEY": "gn-SECRET"}


def wav(rate=24000):
    buf = io.BytesIO()
    sf.write(buf, np.full(rate, 0.1, dtype="float32"), rate, format="WAV", subtype="PCM_16")
    return buf.getvalue()


@pytest.fixture
def server(monkeypatch):
    def install(*replies, **kw):
        s = Server(*replies, **kw)
        monkeypatch.setattr(http, "_urlopen", s)
        return s
    return install


def engine():
    return gn.GnaniEngine(env=KEY, sleep=lambda t: None)


@pytest.mark.parametrize("voice, want", [
    ("Kaveri", ("timbre-v2.5", "Kaveri", "auto")),
    ("shivani@hi-IN", ("timbre-v3.0", "Shivani", "hi-IN")),
    ("v3.0/avinash@ta-IN", ("timbre-v3.0", "Avinash", "ta-IN")),
])
def test_split_voice(voice, want):
    assert gn.split_voice(voice) == want


def test_missing_key():
    e = gn.GnaniEngine(env={})
    assert "GNANI_API_KEY" in e.status().detail
    with pytest.raises(VoiceError, match="set GNANI_API_KEY"):
        e.prepare("Kaveri", lambda p: True, None)


@pytest.mark.parametrize("voice, msg", [
    ("Kaveriii", "did you mean Kaveri"),
    ("timbre-v2.5/Shivani", "Shivani is a timbre-v3.0 voice"),
    ("Kaveri@en-US", "no language 'en-US'"),
    ("timbre-v9/Kaveri", "no Gnani model"),
])
def test_prepare_refuses_bad_voices(voice, msg):
    with pytest.raises(VoiceError, match=msg):
        engine().prepare(voice, lambda p: True, None)


def test_synth_request(server, tmp_path):
    s = server(wav())
    engine().synth("Hello.", "Kaveri@en-IN", 1.1, tmp_path / "a.wav")
    req = s.requests[0]
    assert req.full_url == gn.URL and req.get_header("X-api-key-id") == "gn-SECRET"
    body = s.json_body()
    assert body["model"] == "timbre-v2.5" and body["voice"] == "Kaveri" and body["language"] == "en-IN"
    assert body["speed"] == 1.1 and body["audio_config"]["container"] == "wav"
    assert sf.info(str(tmp_path / "a.wav")).samplerate == 24000


@pytest.mark.parametrize("speed", [0.8, 1.2])
def test_speed_outside_range_is_refused(speed, tmp_path):
    with pytest.raises(VoiceError, match=r"0\.85.*1\.15"):
        engine().synth("Hi.", "Kaveri", speed, tmp_path / "a.wav")


def test_rejected_key_names_the_variable_not_the_key(server, tmp_path):
    server(403, error_body=b'{"success":false,"error":{"message":"bad key gn-SECRET"}}')
    with pytest.raises(VoiceError) as e:
        engine().synth("Hi.", "Kaveri", 1.0, tmp_path / "a.wav")
    assert "GNANI_API_KEY" in str(e.value) and "gn-SECRET" not in str(e.value)


def test_non_wav_reply_is_a_voice_error(server, tmp_path):
    server(b"<html>busy</html>")
    with pytest.raises(VoiceError, match="not a readable WAV"):
        engine().synth("Hi.", "Kaveri", 1.0, tmp_path / "a.wav")
