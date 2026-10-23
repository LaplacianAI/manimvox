import base64
import io
import json

import numpy as np
import pytest
import soundfile as sf

from manimvox.voice import VoiceError, http
from manimvox.voice.engines import sarvam as sv
from tests.http_fakes import Server

KEY = {"SARVAM_API_KEY": "sv-SECRET"}


def wav_reply(rate=24000, channels=1):
    buf = io.BytesIO()
    sf.write(buf, np.full((rate, channels), 0.1, dtype="float32"), rate, format="WAV", subtype="PCM_16")
    return json.dumps({"request_id": "r1", "audios": [base64.b64encode(buf.getvalue()).decode()]}).encode()


@pytest.fixture
def server(monkeypatch):
    def install(*replies, **kw):
        s = Server(*replies, **kw)
        monkeypatch.setattr(http, "_urlopen", s)
        return s
    return install


def engine():
    return sv.SarvamEngine(env=KEY, sleep=lambda t: None)


@pytest.mark.parametrize("voice, want", [
    ("shubh", ("bulbul:v3", "shubh", "en-IN")),
    ("Anushka@hi-IN", ("bulbul:v2", "anushka", "hi-IN")),
    ("v3/priya@ta-IN", ("bulbul:v3", "priya", "ta-IN")),
    ("bulbul:v4-flash/simran_en_customer", ("bulbul:v4-flash", "simran_en_customer", "en-IN")),
])
def test_split_voice(voice, want):
    assert sv.split_voice(voice) == want


def test_missing_key():
    e = sv.SarvamEngine(env={})
    assert "SARVAM_API_KEY" in e.status().detail
    with pytest.raises(VoiceError, match="set SARVAM_API_KEY"):
        e.prepare("shubh", lambda p: True, None)


@pytest.mark.parametrize("voice, msg", [
    ("shubhh", "did you mean shubh"),
    ("bulbul:v2/shubh", "bulbul:v2 has no speaker 'shubh'"),
    ("shubh@hi", "no language 'hi'"),
    ("bulbul:v9/shubh", "no Sarvam model"),
])
def test_prepare_refuses_bad_voices(voice, msg):
    with pytest.raises(VoiceError, match=msg):
        engine().prepare(voice, lambda p: True, None)


def test_prepare_accepts_any_v4_flash_persona():
    engine().prepare("bulbul:v4-flash/ishita_hi_devotional@hi-IN", lambda p: True, None)


def test_synth_request(server, tmp_path):
    s = server(wav_reply(channels=2))
    engine().synth("Namaste.", "anushka@hi-IN", 1.2, tmp_path / "a.wav")
    req = s.requests[0]
    assert req.full_url == sv.URL and req.get_header("Api-subscription-key") == "sv-SECRET"
    assert s.json_body() == {"text": "Namaste.", "model": "bulbul:v2", "speaker": "anushka",
                             "language_code": "hi-IN", "pace": 1.2, "speech_sample_rate": 24000,
                             "output_audio_codec": "wav"}
    info = sf.info(str(tmp_path / "a.wav"))
    assert (info.samplerate, info.channels, info.subtype) == (24000, 1, "PCM_16")


def test_limits_are_checked_before_sending(tmp_path):
    with pytest.raises(VoiceError, match="at most 1500"):
        engine().synth("x" * 1501, "anushka", 1.0, tmp_path / "a.wav")
    with pytest.raises(VoiceError, match=r"0\.5.*2\.0"):
        engine().synth("Hi.", "shubh", 2.5, tmp_path / "a.wav")


def test_rejected_key_names_the_variable_not_the_key(server, tmp_path):
    server(403, error_body=b'{"error":{"message":"bad key sv-SECRET"}}')
    with pytest.raises(VoiceError) as e:
        engine().synth("Hi.", "shubh", 1.0, tmp_path / "a.wav")
    assert "SARVAM_API_KEY" in str(e.value) and "sv-SECRET" not in str(e.value)


@pytest.mark.parametrize("reply", [b"<html>", b'{"audios": []}', b'{"audios": ["not base64!"]}'])
def test_unreadable_reply_is_a_voice_error(server, tmp_path, reply):
    server(reply)
    with pytest.raises(VoiceError, match="unreadable reply"):
        engine().synth("Hi.", "shubh", 1.0, tmp_path / "a.wav")
