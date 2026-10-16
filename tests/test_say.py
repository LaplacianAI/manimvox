import subprocess
import sys

import numpy as np
import pytest
import soundfile as sf

from manimvox.voice import VoiceError
from manimvox.voice.engines.say import SayEngine, parse_voice_list

LIST = """Albert              en_US    # Hello! My name is Albert.
Bad News            en_US    # The light you see at the end of the tunnel is the headlamp of a fast approaching train.
Eddy (English (US)) en_US    # Hello! My name is Eddy.
Samantha            en_US    # Hello! My name is Samantha.
Amélie              fr_CA    # Bonjour! Je m’appelle Amélie.
"""


class FakeRun:
    def __init__(self):
        self.calls = []

    def __call__(self, cmd, **kw):
        self.calls.append((cmd, kw))
        if cmd[:3] == ["say", "-v", "?"]:
            return subprocess.CompletedProcess(cmd, 0, stdout=LIST, stderr="")
        out = cmd[cmd.index("-o") + 1]
        sf.write(out, np.zeros(2400, dtype=np.int16), 24000, format="WAV", subtype="PCM_16")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")


def test_parse_voice_list_keeps_spaces_and_parentheses():
    names = [n for n, _ in parse_voice_list(LIST)]
    assert names == ["Albert", "Bad News", "Eddy (English (US))", "Samantha", "Amélie"]
    assert parse_voice_list(LIST)[4] == ("Amélie", "fr_CA")


def test_not_on_macos_says_so():
    e = SayEngine(run=FakeRun(), platform="linux")
    st = e.status()
    assert not st.ready and "macOS only" in st.detail
    with pytest.raises(VoiceError, match="macOS only"):
        e.prepare("Samantha", lambda p: True, None)


def test_prepare_rejects_unknown_voice_with_suggestions():
    with pytest.raises(VoiceError, match=r"no voice 'Samanta'.*Samantha"):
        SayEngine(run=FakeRun(), platform="darwin").prepare("Samanta", lambda p: True, None)


def test_synth_command_rate_and_stdin(tmp_path):
    run = FakeRun()
    SayEngine(run=run, platform="darwin").synth("-dash first", "Bad News", 1.2, tmp_path / "a.wav")
    cmd, kw = run.calls[-1]
    assert cmd == ["say", "-v", "Bad News", "-r", "210", "-o", str(tmp_path / "a.wav"),
                   "--file-format=WAVE", "--data-format=LEI16@24000", "-f", "-"]
    assert kw["input"] == "-dash first" and kw["encoding"] == "utf-8"
    assert sf.info(str(tmp_path / "a.wav")).samplerate == 24000


def test_synth_failure_is_a_voice_error(tmp_path):
    def failing(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Voice `X' not found.")

    with pytest.raises(VoiceError, match="say failed.*not found"):
        SayEngine(run=failing, platform="darwin").synth("hi", "X", 1.0, tmp_path / "a.wav")


@pytest.mark.skipif(sys.platform != "darwin", reason="say is macOS only")
def test_real_say_writes_mono_16_bit(tmp_path):
    e = SayEngine()
    e.prepare("Samantha", lambda p: True, None)
    e.synth("Hello from manimvox.", "Samantha", 1.0, tmp_path / "a.wav")
    info = sf.info(str(tmp_path / "a.wav"))
    assert (info.channels, info.subtype, info.samplerate) == (1, "PCM_16", 24000) and info.duration > 0.5
