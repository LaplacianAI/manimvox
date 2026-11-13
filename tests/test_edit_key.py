"""Green screen (manimvox.edit.key): the matte, its soft edge, spill, the backing found by itself, the field in JSON
and Python, and a render with a keyed subject over the main track."""
import json
import shutil

import av
import numpy as np
import pytest

from manimvox.edit import Inset, Key, Timeline, Title
from manimvox.edit.check import check_edit
from manimvox.edit.key import key_color, keyed
from manimvox.edit.render import render_edit
from manimvox.edit.timeline import parse, to_dict, validate

from .test_edit_render import FIXTURE, footage

GREEN = (0, 177, 64)
RED = (210, 40, 40)


def screen(h=60, w=80, backing=GREEN, subject=RED) -> np.ndarray:
    """A backing with a subject square in the middle."""
    a = np.zeros((h, w, 3), np.uint8)
    a[:] = backing
    a[h // 4:3 * h // 4, w // 4:3 * w // 4] = subject
    return a


def test_the_backing_goes_and_the_subject_stays():
    a = screen()
    out = keyed(a, Key("#00b140"), key_color(Key("#00b140"), a))
    assert out.shape == (60, 80, 4)
    assert out[2, 2, 3] == 0 and out[30, 40, 3] == 255
    assert tuple(out[30, 40, :3]) == RED  # no spill to take out of red


def test_auto_finds_the_backing_from_the_border():
    a = screen(backing=(10, 70, 200))
    c = key_color(Key(), a)
    assert np.allclose(c * 255, (10, 70, 200), atol=1)
    rgba = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])  # an RGBA frame, as the renderer reads
    assert np.allclose(key_color(Key(), rgba), c)
    out = keyed(a, Key(), c)
    assert out[0, 0, 3] == 0 and out[30, 40, 3] == 255


def test_the_edge_is_soft_over_the_softness():
    ramp = np.zeros((1, 11, 3), np.uint8)
    for i in range(11):  # from the backing to grey, step by step
        ramp[0, i] = np.rint(np.array(GREEN) * (1 - i / 10) + np.array([128, 128, 128]) * i / 10)
    k = Key("#00b140", similarity=0.05, softness=0.3)
    alpha = keyed(ramp, k, key_color(k, ramp))[0, :, 3].astype(int)
    assert alpha[0] == 0 and alpha[-1] > alpha[5] > 0
    assert np.all(np.diff(alpha) >= 0)
    hard = Key("#00b140", similarity=0.15, softness=0)
    assert set(keyed(ramp, hard, key_color(hard, ramp))[0, :, 3]) <= {0, 255}


def test_spill_is_taken_out_of_the_backing_channel():
    a = np.array([[[150, 190, 120]]], np.uint8)  # skin lit green by the screen
    full = keyed(a, Key("#00b140", spill=1), key_color(Key("#00b140"), a))[0, 0]
    assert full[1] == 150  # green brought down to the brighter of red and blue
    assert keyed(a, Key("#00b140", spill=0), key_color(Key("#00b140"), a))[0, 0, 1] == 190
    blue = np.array([[[120, 130, 200]]], np.uint8)
    out = keyed(blue, Key("#0047bb", spill=1), key_color(Key("#0047bb"), blue))[0, 0]
    assert out[2] == 130 and out[1] == 130  # a blue screen's spill is in blue


def test_an_alpha_already_there_is_kept():
    rgba = np.dstack([screen(), np.full((60, 80), 100, np.uint8)])
    out = keyed(rgba, Key("#00b140"), key_color(Key("#00b140"), rgba))
    assert out[30, 40, 3] == 100 and out[2, 2, 3] == 0


# ---------------------------------------------------------------- the field

@pytest.mark.parametrize(("raw", "key"), [
    (True, Key()),
    ("auto", Key()),
    ("green", Key("#00b140")),
    ("#112233", Key("#112233")),
    ({"color": "blue", "spill": 0.2}, Key("#0047bb", spill=0.2)),
])
def test_key_parses_its_shortcuts_and_round_trips(raw, key):
    tl = parse({"segments": [{"title": "Hi"}], "overlays": [{"clip": "a.mp4", "at": 0, "until": 2, "key": raw}]})
    assert tl.overlays[0].key == key and tl.overlays[0].box is None
    assert parse(to_dict(tl)) == tl


def test_an_inset_without_a_key_or_box_writes_neither():
    out = to_dict(parse({"segments": [{"title": "Hi"}], "overlays": [{"clip": "a.mp4", "at": 0, "until": 2}]}))
    assert out["overlays"][0] == {"clip": "a.mp4", "at": 0.0, "until": 2.0}


@pytest.mark.parametrize(("raw", "message"), [
    ("chartreuse", r'key.color must be "auto", "green", "blue" or "#rrggbb"'),
    ({"similarity": 1}, "similarity must be a number from 0 to 0.6"),
    ({"tolerance": 0.1}, "unknown key 'tolerance'"),
    (3, "key must be true"),
])
def test_a_bad_key_names_the_field(raw, message):
    with pytest.raises(ValueError, match=message):
        parse({"segments": [{"title": "Hi"}], "overlays": [{"clip": "a.mp4", "at": 0, "until": 2, "key": raw}]})


def test_a_python_key_is_checked_like_its_json():
    tl = validate(Timeline(segments=[Title("Hi")], overlays=[Inset("a.mp4", at=0, until=2, key=Key(spill=0.3))]))
    assert tl.overlays[0].key == Key(spill=0.3)
    with pytest.raises(ValueError, match="spill must be a number from 0 to 1"):
        validate(Timeline(segments=[Title("Hi")], overlays=[Inset("a.mp4", at=0, until=2, key=Key(spill=2))]))


# ---------------------------------------------------------------- render

@pytest.fixture
def project(tmp_path):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    f = d / "footage"
    f.mkdir()
    footage(f / "blue.mp4", 2, (30, 30, 220), 1000)
    c = av.open(str(f / "speaker.mp4"), "w")
    v = c.add_stream("libx264", rate=10)
    v.width, v.height, v.pix_fmt = 160, 90, "yuv444p"  # full colour, so the square's edge stays sharp
    for _ in range(20):
        for p in v.encode(av.VideoFrame.from_ndarray(screen(90, 160), format="rgb24")):
            c.mux(p)
    for p in v.encode():
        c.mux(p)
    c.close()
    return d


def test_a_keyed_speaker_stands_over_the_main_track(project):
    (project / "edits").mkdir(exist_ok=True)
    (project / "edits" / "k.json").write_text(json.dumps({
        "size": [320, 180], "fps": 10, "segments": [{"clip": "footage/blue.mp4"}],
        "overlays": [{"clip": "footage/speaker.mp4", "at": 0, "until": 2, "key": "auto", "fade": 0}]}))
    assert check_edit(project, parse(json.loads((project / "edits" / "k.json").read_text()))).ok
    r = render_edit(project, "k", sheets=False)
    with av.open(r.video) as c:
        fr = [f.to_ndarray(format="rgb24").astype(int) for f in c.decode(video=0)]
    mid, corner = fr[10][90, 160], fr[10][10, 10]
    assert mid[0] > 150 and mid[2] < 100  # the red subject, at the centre of the whole frame
    assert corner[2] > 150 and corner[1] < 90  # the blue main track, where the screen was
