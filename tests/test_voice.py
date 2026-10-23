from pathlib import Path

import pytest
import soundfile as sf

from manimvox.voice import (
    DEFAULT_VOICE,
    EngineNotInstalled,
    UnknownEngine,
    VoiceEngine,
    VoiceError,
    VoiceSpec,
    clone_reference,
    get_engine,
    parse_voice,
    resolve_voice,
    synth_cached,
)


def test_parse_voice_engine_and_voice():
    assert parse_voice("piper:en_US-amy-medium") == VoiceSpec("piper", "en_US-amy-medium")


def test_parse_voice_keeps_colons_in_voice():
    assert parse_voice("xtts:clone=a:b.wav") == VoiceSpec("xtts", "clone=a:b.wav")


def test_bare_id_from_explainer_playlist_means_kokoro():
    assert parse_voice("af_heart") == VoiceSpec("kokoro", "af_heart")


@pytest.mark.parametrize("bad", ["", "  ", ":x", "kokoro:"])
def test_parse_voice_rejects_empty_parts(bad):
    with pytest.raises(VoiceError, match="engine:voice"):
        parse_voice(bad)


def test_resolve_precedence():
    env = {"MANIMVOX_VOICE": "say:Samantha"}
    assert str(resolve_voice("fake:tone", "kokoro:am_adam", env)) == "fake:tone"
    assert str(resolve_voice(None, "kokoro:am_adam", env)) == "kokoro:am_adam"
    assert str(resolve_voice(None, None, env)) == "say:Samantha"
    assert str(resolve_voice(None, None, {})) == DEFAULT_VOICE


def test_unknown_engine_lists_known():
    with pytest.raises(UnknownEngine, match="fake"):
        get_engine("nope")


def test_engine_not_installed_message_names_extra():
    e = EngineNotInstalled("piper", "piper")
    assert 'uv tool install --force "manimvox[kokoro,piper]"' in str(e)


def test_fake_tone_is_cached_and_timed(tmp_path):
    spec = parse_voice("fake:tone")
    p1, d1 = synth_cached(spec, "one two three four five six seven eight", 1.0, tmp_path)
    p2, _ = synth_cached(spec, "one two three four five six seven eight", 1.0, tmp_path)
    assert p1 == p2 and d1 == pytest.approx(8 / 2.6, abs=0.01)
    data, sr = sf.read(p1)
    assert sr == 24000 and abs(data).max() > 0.1


def test_cache_key_changes_with_voice_speed_and_text(tmp_path):
    a, _ = synth_cached(parse_voice("fake:tone"), "hello there", 1.0, tmp_path)
    b, _ = synth_cached(parse_voice("fake:silence"), "hello there", 1.0, tmp_path)
    c, _ = synth_cached(parse_voice("fake:tone"), "hello there", 1.2, tmp_path)
    d, _ = synth_cached(parse_voice("fake:tone"), "hello again", 1.0, tmp_path)
    assert len({a, b, c, d}) == 4


@pytest.mark.parametrize("blank", ["", "   ", "\n"])
def test_blank_line_is_an_error(tmp_path, blank):
    with pytest.raises(VoiceError, match="empty narration line"):
        synth_cached(parse_voice("fake:tone"), blank, 1.0, tmp_path)


def test_no_temp_files_left_behind(tmp_path):
    synth_cached(parse_voice("fake:tone"), "hello", 1.0, tmp_path)
    assert not list(tmp_path.glob("*.tmp.wav"))


def test_engine_base_defaults():
    e = VoiceEngine()
    assert e.online == "" and e.noncommercial is False
    assert e.voice_key("x") == "x"
    assert e.prepare("x", lambda p: True, Path(".")) is None


def test_describe_voices_defaults_to_blank_descriptions():
    class Two(VoiceEngine):
        def voices(self):
            return ["a", "b"]

    assert Two().describe_voices() == [("a", ""), ("b", "")]


def test_cache_key_uses_voice_key(tmp_path, monkeypatch):
    monkeypatch.setattr(type(get_engine("fake")), "voice_key", lambda self, v: "same")
    a, _ = synth_cached(parse_voice("fake:tone"), "hello there", 1.0, tmp_path)
    b, _ = synth_cached(parse_voice("fake:silence"), "hello there", 1.0, tmp_path)
    assert a == b  # the key came from voice_key, not the raw voice string


def test_clone_reference_relative_to_root(tmp_path):
    (tmp_path / "voices").mkdir()
    rec = tmp_path / "voices" / "me.wav"
    rec.write_bytes(b"RIFF")
    assert clone_reference("clone=voices/me.wav", tmp_path) == rec
    assert clone_reference(f"clone={rec}") == rec


@pytest.mark.parametrize("bad, msg", [
    ("me.wav", "clone=<speaker.wav>"),
    ("clone=", "needs a path"),
    ("clone=missing.wav", "not found"),
])
def test_clone_reference_errors(tmp_path, bad, msg):
    with pytest.raises(VoiceError, match=msg):
        clone_reference(bad, tmp_path)


ALL = ["edge", "elevenlabs", "f5", "fake", "kokoro", "openai", "piper", "say", "xtts"]


def test_every_spec_engine_is_registered():
    from manimvox.voice import engine_names
    assert engine_names() == ALL


@pytest.mark.parametrize("name", ALL)
def test_every_engine_states_licence_extra_and_default(name):
    e = get_engine(name)
    assert e.name == name and e.licence and e.default_voice
    assert e.extra in (None, "kokoro", "piper", "edge", "cloud", "xtts", "f5")
    st = e.status()  # never raises, never touches the network
    assert isinstance(st.ready, bool) and st.detail
