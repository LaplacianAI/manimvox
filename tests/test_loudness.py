import json
import math

import numpy as np
import pytest
import soundfile as sf

from manimvox.project import ProjectError, load_project
from manimvox.voice import get_engine, parse_voice, synth_cached
from manimvox.voice import loudness as L

RATE = 24000


def tone(seconds, amplitude, rate=RATE, f=997.0):
    t = np.arange(int(seconds * rate)) / rate
    return amplitude * np.sin(2 * np.pi * f * t)


def speechlike(seconds, amplitude, rate=RATE, seed=0):
    """Bursts of a few tones with gaps, peaky like speech: a crest factor far above a sine's."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * rate)) / rate
    x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f in (140, 280, 900, 2400)) / 4
    envelope = (np.sin(2 * np.pi * 3 * t) > 0.3) * (1 + 3 * (rng.random(len(t)) > 0.999))
    return amplitude * x * envelope


def test_full_scale_997_hz_sine_is_minus_3_lufs():
    # BS.1770's calibration point: a 0 dBFS 997 Hz sine in one channel reads -3.01 LUFS. The K-weighting here is
    # designed for any rate (as pyloudnorm does), not copied from the standard's 48 kHz table: about 0.05 dB lower
    assert L.integrated_loudness(tone(3, 1.0), RATE) == pytest.approx(-3.01, abs=0.1)
    assert L.integrated_loudness(tone(3, 0.1), RATE) == pytest.approx(-23.01, abs=0.1)


@pytest.mark.parametrize("rate", [16000, 22050, 24000, 44100, 48000])
def test_the_meter_works_at_every_engine_rate(rate):
    assert L.integrated_loudness(tone(2, 1.0, rate), rate) == pytest.approx(-3.01, abs=0.1)


@pytest.mark.parametrize("make, label", [(lambda: speechlike(3, 0.9), "loud"), (lambda: speechlike(3, 0.01), "quiet"),
                                         (lambda: tone(0.25, 0.05), "shorter than one 400 ms block")])
def test_a_line_is_levelled_to_the_target_under_the_peak_ceiling(make, label):
    y = L.level(make(), RATE, -16.0)
    assert L.integrated_loudness(y, RATE) == pytest.approx(-16.0, abs=L.TOLERANCE + 0.05), label
    assert 20 * math.log10(L.true_peak(y).max()) <= L.CEILING_DB + 0.01, label


def test_silence_is_left_alone():
    x = np.zeros(RATE)
    assert L.integrated_loudness(x, RATE) == -math.inf
    assert np.array_equal(L.level(x, RATE, -16.0), x)


def test_the_limiter_leaves_a_line_already_under_the_ceiling_untouched():
    x = tone(1, 0.5)
    assert np.array_equal(L.limit(x, RATE), x)


def test_level_file_writes_mono_16_bit(tmp_path):
    src = tmp_path / "in.wav"
    sf.write(str(src), np.stack([speechlike(2, 0.05)] * 2, axis=1), RATE, subtype="FLOAT")
    L.level_file(src, tmp_path / "out.wav", -16.0)
    info = sf.info(str(tmp_path / "out.wav"))
    assert (info.channels, info.subtype, info.samplerate) == (1, "PCM_16", RATE)


def test_the_cache_levels_a_copy_and_never_synthesises_twice(tmp_path, monkeypatch):
    engine = type(get_engine("fake"))
    calls = []
    real = engine.synth
    monkeypatch.setattr(engine, "synth", lambda self, *a: calls.append(a) or real(self, *a))
    spec = parse_voice("fake:tone")
    raw, d0 = synth_cached(spec, "hello there", 1.0, tmp_path)
    a, d1 = synth_cached(spec, "hello there", 1.0, tmp_path, -16.0)
    b, _ = synth_cached(spec, "hello there", 1.0, tmp_path, -20.0)
    assert len(calls) == 1  # one line, three levels, one call to the voice service
    assert len({raw, a, b}) == 3 and raw.name == a.name.split("_")[0] + ".wav"
    assert d0 == pytest.approx(d1)
    x, rate = sf.read(str(a))
    assert L.integrated_loudness(x, rate) == pytest.approx(-16.0, abs=0.2)
    assert not list(tmp_path.glob("*.tmp.wav"))


def test_without_a_target_the_cache_returns_the_line_as_the_engine_made_it(tmp_path):
    a, _ = synth_cached(parse_voice("fake:tone"), "hello there", 1.0, tmp_path)
    b, _ = synth_cached(parse_voice("fake:tone"), "hello there", 1.0, tmp_path, None)
    assert a == b and list(tmp_path.glob("*.wav")) == [a]


def write(tmp_path, **extra):
    (tmp_path / "series.json").write_text(json.dumps({"series": "S", **extra}), encoding="utf-8")


def test_loudness_defaults_to_minus_16_and_null_turns_it_off(tmp_path):
    write(tmp_path)
    assert load_project(tmp_path).loudness == L.DEFAULT_LOUDNESS == -16.0
    write(tmp_path, loudness=None)
    assert load_project(tmp_path).loudness is None
    write(tmp_path, loudness=-23)
    assert load_project(tmp_path).loudness == -23.0


@pytest.mark.parametrize("bad", [0, -60, "loud", True, [-16]])
def test_loudness_outside_the_range_is_refused(tmp_path, bad):
    write(tmp_path, loudness=bad)
    with pytest.raises(ProjectError, match="'loudness' must be a level in LUFS from -40 to -5"):
        load_project(tmp_path)
