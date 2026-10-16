import numpy as np
import pytest
import soundfile as sf

from manimvox.voice import VoiceError, http
from manimvox.voice.engines import openai as oa
from tests.http_fakes import Server

PCM = (np.ones(24000, dtype="<i2") * 800).tobytes()
KEY = {"OPENAI_API_KEY": "sk-test-SECRET"}


@pytest.fixture
def server(monkeypatch):
    def install(*replies, **kw):
        s = Server(*replies, **kw)
        monkeypatch.setattr(http, "_urlopen", s)
        return s
    return install


@pytest.mark.parametrize("voice, split", [("alloy", ("gpt-4o-mini-tts", "alloy")),
                                          ("tts-1-hd/onyx", ("tts-1-hd", "onyx"))])
def test_split_voice(voice, split):
    assert oa.split_voice(voice) == split


def test_status_and_prepare_need_the_key():
    e = oa.OpenAIEngine(env={})
    assert not e.status().ready and "OPENAI_API_KEY" in e.status().detail
    with pytest.raises(VoiceError, match="set OPENAI_API_KEY"):
        e.prepare("alloy", lambda p: True, None)


def test_new_voice_on_legacy_model_is_rejected():
    with pytest.raises(VoiceError, match="tts-1 has no voice 'marin'"):
        oa.OpenAIEngine(env=KEY).prepare("tts-1/marin", lambda p: True, None)


def test_synth_request_for_gpt_4o_mini_tts(server, tmp_path):
    s = server(PCM)
    oa.OpenAIEngine(env=KEY, sleep=lambda t: None).synth("Hello.", "alloy", 1.0, tmp_path / "a.wav")
    req = s.requests[0]
    assert req.full_url == oa.URL and req.get_header("Authorization") == "Bearer sk-test-SECRET"
    assert s.json_body() == {"model": "gpt-4o-mini-tts", "voice": "alloy", "input": "Hello.", "response_format": "pcm"}
    assert sf.info(str(tmp_path / "a.wav")).samplerate == 24000


def test_speed_goes_to_speed_on_legacy_and_to_instructions_on_new(server, tmp_path):
    s = server(PCM, PCM)
    e = oa.OpenAIEngine(env=KEY, sleep=lambda t: None)
    e.synth("Hi.", "tts-1/alloy", 1.2, tmp_path / "a.wav")
    e.synth("Hi.", "alloy", 1.2, tmp_path / "b.wav")
    assert s.json_body(0)["speed"] == 1.2 and "instructions" not in s.json_body(0)
    assert "speed" not in s.json_body(1) and "1.2" in s.json_body(1)["instructions"]


def test_long_line_is_refused_before_sending(server, tmp_path):
    s = server()
    with pytest.raises(VoiceError, match="4096"):
        oa.OpenAIEngine(env=KEY).synth("x" * 4097, "alloy", 1.0, tmp_path / "a.wav")
    assert s.requests == []


def test_401_names_the_variable_not_the_key(server, tmp_path):
    server(401, error_body=b'{"error":{"message":"Incorrect API key provided: sk-test-SECRET"}}')
    with pytest.raises(VoiceError) as e:
        oa.OpenAIEngine(env=KEY, sleep=lambda t: None).synth("Hi.", "alloy", 1.0, tmp_path / "a.wav")
    assert "OPENAI_API_KEY" in str(e.value) and "sk-test-SECRET" not in str(e.value)


def test_other_refusals_scrub_the_key_from_the_detail(server, tmp_path):
    server(400, error_body=b'{"error":{"message":"bad request near sk-test-SECRET"}}')
    with pytest.raises(VoiceError, match="OpenAI refused the request") as e:
        oa.OpenAIEngine(env=KEY, sleep=lambda t: None).synth("Hi.", "alloy", 1.0, tmp_path / "a.wav")
    assert "sk-test-SECRET" not in str(e.value)


def test_voice_key_includes_model():
    e = oa.OpenAIEngine(env=KEY)
    assert e.voice_key("alloy") == "gpt-4o-mini-tts/alloy" != e.voice_key("tts-1/alloy")
