"""Speed ramps (timeline.Clock, sound.ramp_span): keyframes in JSON and Python, the time map both ways, a ramped
clip's length, frames taken from the right second of the file, and its sound: as long as the picture, pitch kept,
and the same in a window as in the whole film."""
import json
import shutil

import av
import numpy as np
import pytest

from manimvox.edit import Clip, Timeline
from manimvox.edit.render import render_edit
from manimvox.edit.timeline import Clock, parse, seconds_of, to_dict, validate
from manimvox.post.audio import RATE, read_audio

from .test_edit_render import FIXTURE, peak_freq

FPS = 10


def ease(f):
    return f * f * (3 - 2 * f)


def test_a_ramp_parses_and_round_trips():
    tl = parse({"segments": [{"clip": "a.mp4", "speed": [[1, 1], [2.5, 0.5], [4, 2]]}]})
    assert tl.segments[0].speed == ((1.0, 1.0), (2.5, 0.5), (4.0, 2.0))
    assert parse(json.loads(json.dumps(to_dict(tl)))) == tl
    same = parse({"segments": [{"clip": "a.mp4", "speed": [[0, 2], [3, 2]]}]})
    assert same.segments[0].speed == 2.0  # one speed throughout is not a ramp
    assert validate(Timeline(segments=[Clip("a.mp4", speed=((0, 1), (1, 3)))])).segments[0].speed == ((0, 1), (1, 3))


@pytest.mark.parametrize(("speed", "message"), [
    ([[0, 1]], "a ramp of at least two"),
    ([[0, 1], [0, 2]], r"speed\[1\]: keyframe times must rise"),
    ([[0, 1], [1, 9]], r"speed\[1\]\[1\] must be a number from 0.25 to 4"),
    ([[0, 1, 2], [1, 2]], "a ramp of at least two"),
    (5, "speed must be a number from 0.25 to 4"),
])
def test_a_bad_ramp_names_the_field(speed, message):
    with pytest.raises(ValueError, match=message):
        parse({"segments": [{"clip": "a.mp4", "speed": speed}]})


def test_one_speed_is_plain_arithmetic():
    c = Clock(2.0, 8.0, 2.0)
    assert not c.ramp and c.seconds == 3.0 and c.source(1.5) == 5.0 and c.output(5.0) == 1.5


def test_a_ramp_integrates_one_over_speed_and_holds_past_its_keys():
    c = Clock(0.0, 3.0, ((0.0, 1.0), (1.0, 2.0)))
    s = np.linspace(0, 1, 100001)
    want = np.trapezoid(1 / (1 + ease(s)), s) + 2.0 / 2.0  # eased 1 -> 2 over a second, then held at 2
    assert c.seconds == pytest.approx(want, abs=1e-5)
    assert c.rate(0.5) == pytest.approx(1.5) and c.rate(2.5) == 2.0 and c.rate(-1) == 1.0
    u = np.linspace(0, c.seconds, 50)
    assert np.all(np.diff(c.source(u)) > 0)
    assert np.allclose(c.output(c.source(u)), u, atol=1e-6)
    assert seconds_of(Clip("a.mp4", end=3.0, speed=((0.0, 1.0), (1.0, 2.0))), None) == c.seconds


# ---------------------------------------------------------------- render

def clock_footage(path, seconds=6.0, freq=1000.0):
    """Frame i is grey level 4i, so a frame says which second of the file it is; under it a steady tone."""
    c = av.open(str(path), "w")
    v = c.add_stream("libx264", rate=FPS)
    v.width, v.height, v.pix_fmt = 160, 90, "yuv420p"
    v.options = {"crf": "0"}
    a = c.add_stream("aac", rate=RATE, layout="mono")
    for i in range(round(seconds * FPS)):
        img = np.full((90, 160, 3), 4 * i, np.uint8)
        for p in v.encode(av.VideoFrame.from_ndarray(img, format="rgb24")):
            c.mux(p)
    for p in v.encode():
        c.mux(p)
    t = np.arange(round(seconds * RATE)) / RATE
    fr = av.AudioFrame.from_ndarray((0.3 * np.sin(2 * np.pi * freq * t)).astype(np.float32).reshape(1, -1),
                                    format="flt", layout="mono")
    fr.sample_rate = RATE
    for p in a.encode(fr):
        c.mux(p)
    for p in a.encode():
        c.mux(p)
    c.close()


RAMP = [[0.5, 1.0], [2.5, 3.0], [4.0, 0.5]]


@pytest.fixture
def project(tmp_path):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    (d / "footage").mkdir()
    clock_footage(d / "footage" / "clock.mp4")
    (d / "edits").mkdir()
    (d / "edits" / "r.json").write_text(json.dumps({"size": [320, 180], "fps": FPS, "segments": [
        {"clip": "footage/clock.mp4", "start": 0.5, "end": 5.5, "speed": RAMP}]}))
    return d


def test_a_ramped_clip_shows_the_right_second_and_keeps_its_sound_in_step_and_pitch(project):
    r = render_edit(project, "r", sheets=False)
    clock = Clock(0.5, 5.5, tuple(tuple(k) for k in RAMP))
    assert r.seconds == pytest.approx(round(clock.seconds * FPS) / FPS, abs=0.11)
    with av.open(r.video) as c:
        levels = [float(f.to_ndarray(format="rgb24")[90, 160].mean()) for f in c.decode(video=0)]
    want = [4 * int(clock.source(k / FPS) * FPS + 1e-6) for k in range(len(levels))]
    assert np.max(np.abs(np.array(levels) - np.array(want))) <= 6  # within about one source frame
    x = read_audio(r.video).mean(axis=0)
    assert abs(x.shape[0] / RATE - len(levels) / FPS) < 0.05
    for a in (0.2, clock.output(2.5) - 0.2, r.seconds - 0.5):  # slow, fast and slowed again
        assert abs(peak_freq(x, a, a + 0.3) - 1000) < 30
    rms = [float(np.sqrt(np.mean(x[int(t * RATE):int((t + 0.1) * RATE)] ** 2))) for t in np.arange(0.2, 2.5, 0.1)]
    assert min(rms) > 0.5 * max(rms)  # no holes where the blocks join


def test_a_window_of_a_ramp_matches_the_whole(project):
    whole = read_audio(render_edit(project, "r", sheets=False).video).mean(axis=0)
    part = read_audio(render_edit(project, "r", start=1.0, end=2.0, sheets=False).video).mean(axis=0)
    a = int(1.0 * RATE)
    n = min(part.shape[0], int(0.9 * RATE))
    assert np.corrcoef(whole[a + 2000:a + n], part[2000:n])[0, 1] > 0.95
