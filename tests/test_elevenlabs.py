import json

import numpy as np
import pytest
import soundfile as sf

from manimvox.voice import VoiceError, http
from manimvox.voice.engines import elevenlabs as el
from tests.http_fakes import Server

PCM = (np.ones(24000, dtype="<i2") * 800).tobytes()
KEY = {"ELEVENLABS_API_KEY": "el-SECRET"}


@pytest.fixture
def server(monkeypatch):
    def install(*replies, **kw):
        s = Server(*replies, **kw)
        monkeypatch.setattr(http, "_urlopen", s)
        return s
    return install


def test_missing_key():
    e = el.ElevenLabsEngine(env={})
    assert "ELEVENLABS_API_KEY" in e.status().detail
    with pytest.raises(VoiceError, match="set ELEVENLABS_API_KEY"):
        e.prepare("abc", lambda p: True, None)


@pytest.mark.parametrize("speed", [0.5, 1.3])
def test_speed_outside_range_is_refused(speed, tmp_path):
    with pytest.raises(VoiceError, match=r"0\.7.*1\.2"):
        el.ElevenLabsEngine(env=KEY).synth("hi", "abc", speed, tmp_path / "a.wav")


def test_synth_request(server, tmp_path):
    s = server(PCM)
    el.ElevenLabsEngine(env=KEY, sleep=lambda t: None).synth("Hello.", "abc123", 1.1, tmp_path / "a.wav")
    req = s.requests[0]
    assert req.full_url == el.TTS_URL.format(voice_id="abc123") + "?output_format=pcm_24000"
    assert req.get_header("Xi-api-key") == "el-SECRET"
    assert s.json_body() == {"text": "Hello.", "model_id": "eleven_multilingual_v2", "voice_settings": {"speed": 1.1}}
    assert sf.info(str(tmp_path / "a.wav")).samplerate == 24000


def test_speed_one_sends_no_voice_settings(server, tmp_path):
    s = server(PCM)
    el.ElevenLabsEngine(env=KEY, sleep=lambda t: None).synth("Hi.", "eleven_v3/abc", 1.0, tmp_path / "a.wav")
    assert s.json_body() == {"text": "Hi.", "model_id": "eleven_v3"}


def test_voices_follow_pages(server):
    page1 = {"voices": [{"voice_id": "v1", "name": "Rachel"}], "has_more": True, "next_page_token": "t2"}
    page2 = {"voices": [{"voice_id": "v2", "name": "Adam"}], "has_more": False}
    s = server(json.dumps(page1).encode(), json.dumps(page2).encode())
    rows = el.ElevenLabsEngine(env=KEY, sleep=lambda t: None).describe_voices()
    assert rows == [("v2", "Adam"), ("v1", "Rachel")]
    assert "next_page_token=t2" in s.requests[1].full_url


def test_401_names_the_variable_not_the_key(server, tmp_path):
    server(401, error_body=b'{"detail":"invalid key el-SECRET"}')
    with pytest.raises(VoiceError) as e:
        el.ElevenLabsEngine(env=KEY, sleep=lambda t: None).synth("Hi.", "abc", 1.0, tmp_path / "a.wav")
    assert "ELEVENLABS_API_KEY" in str(e.value) and "el-SECRET" not in str(e.value)


def test_other_refusals_scrub_the_key_from_the_detail(server, tmp_path):
    server(400, error_body=b'{"detail":"bad request near el-SECRET"}')
    with pytest.raises(VoiceError, match="ElevenLabs refused the request") as e:
        el.ElevenLabsEngine(env=KEY, sleep=lambda t: None).synth("Hi.", "abc", 1.0, tmp_path / "a.wav")
    assert "el-SECRET" not in str(e.value)
