import numpy as np
import pytest
import soundfile as sf

from manimvox.voice import VoiceError
from manimvox.voice.convert import pcm16_to_wav, to_wav
from tests.media import make_mp3


def test_pcm16_to_wav(tmp_path):
    pcm = (np.ones(24000, dtype="<i2") * 1000).tobytes()
    pcm16_to_wav(pcm, 24000, tmp_path / "a.wav")
    info = sf.info(str(tmp_path / "a.wav"))
    assert (info.samplerate, info.channels, info.subtype, info.frames) == (24000, 1, "PCM_16", 24000)


def test_pcm16_drops_a_trailing_odd_byte(tmp_path):
    pcm16_to_wav(b"\x01\x00\x02", 24000, tmp_path / "a.wav")
    assert sf.info(str(tmp_path / "a.wav")).frames == 1


def test_empty_pcm_is_an_error(tmp_path):
    with pytest.raises(VoiceError, match="no audio"):
        pcm16_to_wav(b"", 24000, tmp_path / "a.wav")


def test_mp3_to_wav(tmp_path):
    to_wav(make_mp3(tmp_path / "a.mp3"), tmp_path / "a.wav")
    data, sr = sf.read(str(tmp_path / "a.wav"))
    assert sr == 24000 and data.ndim == 1 and abs(len(data) / sr - 1.0) < 0.1 and abs(data).max() > 0.1
    assert sf.info(str(tmp_path / "a.wav")).subtype == "PCM_16"


def test_garbage_is_a_voice_error(tmp_path):
    (tmp_path / "x.mp3").write_bytes(b"not audio")
    with pytest.raises(VoiceError, match="could not read audio"):
        to_wav(tmp_path / "x.mp3", tmp_path / "x.wav")
