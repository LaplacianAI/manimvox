import pytest
import soundfile as sf

from manimvox.voice import (
    DEFAULT_VOICE,
    EngineNotInstalled,
    UnknownEngine,
    VoiceError,
    VoiceSpec,
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
    assert 'uv tool install "manimvox[piper]"' in str(e)


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
