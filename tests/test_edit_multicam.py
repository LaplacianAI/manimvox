"""Multi-camera sync (manimvox.edit.sync) and the multicam segment: offsets found from the sound to within 10 ms,
refused when the sound does not match, cached; parsing; the check; and a render that switches picture at each cut
while the sound stays on one camera."""
import json
import shutil

import av
import numpy as np
import pytest

from manimvox import tools
from manimvox.edit import Multicam, Timeline
from manimvox.edit import sync as sync_mod
from manimvox.edit.check import check_edit
from manimvox.edit.render import render_edit
from manimvox.edit.sync import SyncError, find_offset
from manimvox.edit.timeline import parse, to_dict, validate
from manimvox.post.audio import RATE, read_audio

from .test_edit_render import FIXTURE, peak_freq

FPS = 10


def moment(seconds=30.0, seed=3) -> np.ndarray:
    """A shared moment's sound: bursts of noise at random times and lengths, like speech, knocks and claps."""
    rng = np.random.default_rng(seed)
    x = np.zeros(round(seconds * RATE), np.float32)
    t = 0.2
    while t < seconds - 0.5:
        n = round(rng.uniform(0.05, 0.4) * RATE)
        i = round(t * RATE)
        x[i:i + n] = rng.normal(0, rng.uniform(0.05, 0.3), n)[: x.shape[0] - i]
        t += rng.uniform(0.15, 0.9)
    return x


def camera(path, sound: np.ndarray, colour, seconds: float, tone: float | None = None):
    """A solid-colour video with `sound` (mono, at RATE) under it, plus a quiet `tone` Hz if given."""
    c = av.open(str(path), "w")
    v = c.add_stream("libx264", rate=FPS)
    v.width, v.height, v.pix_fmt = 160, 90, "yuv420p"
    a = c.add_stream("aac", rate=RATE, layout="mono")
    img = np.zeros((90, 160, 3), np.uint8)
    img[:] = colour
    for _ in range(round(seconds * FPS)):
        for p in v.encode(av.VideoFrame.from_ndarray(img, format="rgb24")):
            c.mux(p)
    for p in v.encode():
        c.mux(p)
    x = sound[: round(seconds * RATE)].copy()
    if tone:
        x += 0.05 * np.sin(2 * np.pi * tone * np.arange(x.shape[0]) / RATE).astype(np.float32)
    fr = av.AudioFrame.from_ndarray(x.reshape(1, -1), format="flt", layout="mono")
    fr.sample_rate = RATE
    for p in a.encode(fr):
        c.mux(p)
    for p in a.encode():
        c.mux(p)
    c.close()
    return path


LATE = 1.37  # camera 1 started this long after camera 0


@pytest.fixture
def project(tmp_path):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    f = d / "footage"
    f.mkdir()
    m = moment()
    camera(f / "wide.mp4", m, (200, 40, 40), 20)
    camera(f / "close.mp4", m[round(LATE * RATE):], (40, 40, 200), 18, tone=3000)
    return d


def test_the_offset_is_found_from_the_sound(project):
    f = project / "footage"
    o = find_offset(project, f / "wide.mp4", f / "close.mp4")
    assert o.seconds == pytest.approx(LATE, abs=0.01) and o.confidence >= sync_mod.CONFIDENT
    back = find_offset(project, f / "close.mp4", f / "wide.mp4")
    assert back.seconds == pytest.approx(-LATE, abs=0.01)


def test_unrelated_sound_is_refused_and_a_match_is_cached(project, monkeypatch):
    f = project / "footage"
    camera(f / "other.mp4", moment(seed=99), (0, 0, 0), 18)
    with pytest.raises(SyncError, match="does not line up clearly"):
        find_offset(project, f / "wide.mp4", f / "other.mp4")
    first = find_offset(project, f / "wide.mp4", f / "close.mp4")
    monkeypatch.setattr(sync_mod, "envelope_db", lambda *a, **k: pytest.fail("measured again"))
    assert find_offset(project, f / "wide.mp4", f / "close.mp4") == first


def test_the_sync_tool_reports_each_file(project):
    r = tools.sync_media(str(project), ["footage/wide.mp4", "footage/close.mp4"])
    assert r.ok and r.offsets[0] == 0 and r.offsets[1] == pytest.approx(LATE, abs=0.01)
    with pytest.raises(tools.ToolError, match="at least two"):
        tools.sync_media(str(project), ["footage/wide.mp4"])


# ---------------------------------------------------------------- the segment

def test_multicam_parses_and_round_trips():
    raw = {"segments": [{"multicam": ["a.mp4", "b.mp4"], "start": 2, "end": 12, "cuts": [[5, 1], [8, 0]],
                         "offsets": [0, 1.37], "sound": 0}]}
    tl = parse(raw)
    m = tl.segments[0]
    assert isinstance(m, Multicam) and m.cuts == ((5.0, 1), (8.0, 0)) and m.offsets == (0.0, 1.37)
    assert [m.camera_at(t) for t in (2, 4.99, 5, 7, 8, 11)] == [0, 0, 1, 1, 0, 0]
    assert m.spans(12) == [(2.0, 5.0, 0), (5.0, 8.0, 1), (8.0, 12, 0)]
    assert parse(json.loads(json.dumps(to_dict(tl)))) == tl
    py = validate(Timeline(segments=[Multicam(("a.mp4", "b.mp4"), cuts=((3, 1),))]))
    assert py.segments[0].cuts == ((3.0, 1),)


@pytest.mark.parametrize(("seg", "message"), [
    ({"multicam": ["a.mp4"]}, "a list of 2 to 9 video files"),
    ({"multicam": ["a.mp4", "b.mp4"], "cuts": [[3, 2]]}, r"cuts\[0\]\[1\] must be a camera's number, 0 to 1"),
    ({"multicam": ["a.mp4", "b.mp4"], "cuts": [[3, 1], [2, 0]]}, r"cuts\[1\]\[0\] must be a number above 3"),
    ({"multicam": ["a.mp4", "b.mp4"], "end": 5, "cuts": [[6, 1]]}, "at or past the end"),
    ({"multicam": ["a.mp4", "b.mp4"], "offsets": [1, 2]}, r"offsets\[0\] must be 0"),
    ({"multicam": ["a.mp4", "b.mp4"], "offsets": [0]}, "one number per camera"),
    ({"multicam": ["a.mp4", "b.mp4"], "speed": 2}, "unknown key 'speed'"),
])
def test_a_bad_multicam_names_the_field(seg, message):
    with pytest.raises(ValueError, match=message):
        parse({"segments": [seg]})


def edit(project, seg) -> str:
    (project / "edits").mkdir(exist_ok=True)
    (project / "edits" / "m.json").write_text(json.dumps({"size": [320, 180], "fps": FPS, "segments": [seg]}))
    return "m"


def test_check_finds_the_offsets_and_cameras_shown_past_their_files(project):
    seg = {"multicam": ["footage/wide.mp4", "footage/close.mp4"], "start": 2, "end": 12, "cuts": [[5, 1]]}
    rep = check_edit(project, parse({"segments": [seg]}))
    assert rep.ok, rep.findings
    assert rep.timeline.segments[0].offsets[1] == pytest.approx(LATE, abs=0.01)
    assert any("camera 1 (footage/close.mp4) starts at +1.37" in c for c in rep.cuts)
    assert rep.seconds == pytest.approx(10)
    early = {**seg, "start": 0.5, "camera": 1, "cuts": []}  # camera 1 only starts at 1.37 s
    rep = check_edit(project, parse({"segments": [early]}))
    assert any("camera 1 is shown from 0.5 s" in f for f in rep.findings), rep.findings


def test_a_multicam_switches_picture_and_keeps_one_sound(project):
    seg = {"multicam": ["footage/wide.mp4", "footage/close.mp4"], "start": 2, "end": 10, "cuts": [[5, 1], [8, 0]]}
    r = render_edit(project, edit(project, seg), sheets=False)
    with av.open(r.video) as c:
        fr = [f.to_ndarray(format="rgb24")[90, 160].astype(int) for f in c.decode(video=0)]
    assert len(fr) == 80
    assert fr[25][0] > 150 and fr[35][2] > 150 and fr[65][0] > 150  # wide, close at 5 s (frame 30), wide at 8 s
    x = read_audio(r.video).mean(axis=0)
    assert abs(x.shape[0] / RATE - 8.0) < 0.05
    # the close camera's sound carries a 3 kHz tone; the film's sound is the wide camera's throughout
    spec = np.abs(np.fft.rfft(x[int(3.5 * RATE):int(5.5 * RATE)]))
    freqs = np.fft.rfftfreq(int(2 * RATE), 1 / RATE)
    band = (freqs > 2950) & (freqs < 3050)
    assert spec[band].max() < 5 * np.median(spec[(freqs > 2000) & (freqs < 4000)])
    assert peak_freq(x, 3.5, 5.5) != pytest.approx(3000, abs=30)
