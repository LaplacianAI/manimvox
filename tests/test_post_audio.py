import itertools
import json
import shutil
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from manimvox.checks.audio import Cue
from manimvox.post.audio import RATE, duck_curve, gain, limit, music_bed, read_audio
from manimvox.post.options import PostError, PostOptions, parse_post
from manimvox.project import ProjectError, load_project
from tests.media import make_video

FIXTURE = Path(__file__).parent / "fixtures" / "hello"


def test_no_post_means_nothing_to_do():
    assert parse_post(None) == PostOptions() and not PostOptions().active


def test_post_reads_every_field():
    p = parse_post({"music": "bed.wav", "music_db": -20, "duck_db": -10, "captions": "burn",
                    "end_card": ["Sources: FACTS.md", "Made with manimvox"], "card_seconds": 2})
    assert p == PostOptions(Path("bed.wav"), -20.0, -10.0, "burn", ("Sources: FACTS.md", "Made with manimvox"), 2.0)
    assert p.active


@pytest.mark.parametrize("raw,msg", [
    ({"musik": "x"}, "unknown key 'musik'"),
    ({"captions": "open"}, "captions"),
    ({"music_db": 3}, "music_db"),
    ({"duck_db": True}, "duck_db"),
    ({"card_seconds": 0.5}, "card_seconds"),
    ({"end_card": ["x"] * 5}, "end_card"),
    ({"end_card": [""]}, "end_card"),
    ({"music": ""}, "music"),
    ([], "must be an object"),
])
def test_bad_post_is_refused(raw, msg):
    with pytest.raises(ValueError, match=msg):
        parse_post(raw)


def test_project_carries_its_post_options(tmp_path):
    d = tmp_path / "p"
    shutil.copytree(FIXTURE, d)
    conf = json.loads((d / "series.json").read_text(encoding="utf-8"))
    conf["post"] = {"music": "bed.wav", "end_card": "Thanks for watching"}
    (d / "series.json").write_text(json.dumps(conf), encoding="utf-8")
    assert load_project(d).post == PostOptions(music=Path("bed.wav"), end_card=("Thanks for watching",))
    conf["post"] = {"captions": "loud"}
    (d / "series.json").write_text(json.dumps(conf), encoding="utf-8")
    with pytest.raises(ProjectError, match=r"series\.json.*captions"):
        load_project(d)


def test_read_audio_resamples_to_stereo_48k(tmp_path):
    f = tmp_path / "m.wav"
    t = np.arange(22050) / 22050
    sf.write(str(f), (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32), 22050)
    a = read_audio(f)
    assert a.shape[0] == 2 and abs(a.shape[1] - RATE) < 200
    assert np.allclose(a[0], a[1]) and 0.3 < np.abs(a).max() < 0.6


def test_read_audio_of_a_video_without_sound_is_empty(tmp_path):
    v = make_video(tmp_path / "v.mkv", 1.0)
    assert read_audio(v).shape == (2, 0)


def test_read_audio_of_garbage_is_a_post_error(tmp_path):
    f = tmp_path / "x.wav"
    f.write_bytes(b"not audio at all")
    with pytest.raises(PostError, match="x.wav"):
        read_audio(f)


def test_duck_curve_is_low_through_each_cue_and_slopes_outside():
    n = 5 * RATE
    g = duck_curve(n, [Cue(2.0, 3.0, "line")], -12.0)
    at = lambda s: float(g[int(s * RATE)])
    assert at(0.5) == pytest.approx(1.0) and at(4.5) == pytest.approx(1.0)
    for s in (2.0, 2.5, 2.99):
        assert at(s) == pytest.approx(gain(-12.0), abs=1e-3)
    ramp = [at(1.65 + 0.05 * k) for k in range(7)]
    assert all(a >= b for a, b in itertools.pairwise(ramp)) and ramp[0] > ramp[-1]


def test_music_bed_loops_a_short_file():
    music = np.full((2, RATE // 2), 0.5, np.float32)
    bed = music_bed(music, 4 * RATE, [], music_db=-6.0, duck_db=-12.0)
    assert bed.shape == (2, 4 * RATE)
    assert bed[0, int(1.5 * RATE)] == pytest.approx(0.5 * gain(-6.0), rel=1e-3)
    assert bed[0, 0] == 0.0 and abs(bed[0, -1]) < 1e-3


def test_music_bed_cuts_a_long_file_and_ducks_under_cues():
    music = np.full((2, 10 * RATE), 0.5, np.float32)
    bed = music_bed(music, 6 * RATE, [Cue(2.0, 3.0, "x")], music_db=-6.0, duck_db=-12.0)
    assert bed.shape == (2, 6 * RATE)
    assert bed[0, int(2.5 * RATE)] == pytest.approx(0.5 * gain(-18.0), rel=1e-2)


def test_music_bed_needs_sound():
    with pytest.raises(PostError, match="no audio"):
        music_bed(np.zeros((2, 0), np.float32), RATE, [], -16.0, -12.0)


def test_limit_only_scales_down_what_would_clip():
    loud = np.array([[2.0, -1.0], [0.5, 0.0]], np.float32)
    assert np.abs(limit(loud)).max() == pytest.approx(0.98)
    quiet = np.array([[0.5, -0.2]], np.float32)
    assert np.array_equal(limit(quiet), quiet)
