"""Stabilisation (manimvox.edit.stabilize): the shake measured against known jitter and turns, the cache, a pan kept
while the jitter is taken out, the zoom, the field in JSON and Python, and a steadier render."""
import itertools
import json
import math
import shutil

import av
import numpy as np
import pytest
from PIL import Image as PILImage
from PIL import ImageFilter

from manimvox.edit import Clip, Stabilize, Timeline
from manimvox.edit import stabilize as stab
from manimvox.edit.render import render_edit
from manimvox.edit.timeline import parse, to_dict, validate

from .test_edit_render import FIXTURE

W, H, FPS = 480, 270, 10


def texture(seed=0, size=(720, 480)) -> PILImage.Image:
    rng = np.random.default_rng(seed)
    noise = (rng.random((size[1] // 6, size[0] // 6)) * 255).astype(np.uint8)
    return PILImage.fromarray(noise).resize(size, PILImage.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(1.5))


def shaky(path, offsets, turns=None):
    """A W x H window over a texture, moved by `offsets` (px) and turned by `turns` (degrees) frame by frame."""
    tex = texture().convert("RGB")
    c = av.open(str(path), "w")
    v = c.add_stream("libx264", rate=FPS)
    v.width, v.height, v.pix_fmt = W, H, "yuv444p"
    v.options = {"crf": "0"}
    cx, cy = tex.width // 2, tex.height // 2
    for k, (ox, oy) in enumerate(offsets):
        img = tex
        if turns is not None and turns[k]:
            img = tex.rotate(turns[k], resample=PILImage.Resampling.BICUBIC, center=(cx + ox, cy + oy))
        box = (cx - W // 2 + ox, cy - H // 2 + oy, cx + W // 2 + ox, cy + H // 2 + oy)
        frame = np.asarray(img.crop(box))
        for p in v.encode(av.VideoFrame.from_ndarray(frame, format="rgb24")):
            c.mux(p)
    for p in v.encode():
        c.mux(p)
    c.close()
    return path


@pytest.fixture
def project(tmp_path):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    (d / "footage").mkdir()
    return d


def jitter(n, seed=1, amp=6):
    rng = np.random.default_rng(seed)
    return [(int(x), int(y)) for x, y in rng.integers(-amp, amp + 1, (n, 2))]


def test_the_shake_is_measured_to_within_a_pixel(project):
    offs = jitter(30)
    path = shaky(project / "footage" / "shake.mp4", offs)
    cam = stab.measure(project, path, 0, 3)
    assert len(cam.times) == 30 and cam.aspect == pytest.approx(H / W)
    # the window moved right by ox, so the picture moved left: the measured path is -(ox - ox0)
    want_x = -(np.array([o[0] for o in offs]) - offs[0][0])
    want_y = -(np.array([o[1] for o in offs]) - offs[0][1])
    assert np.max(np.abs(cam.x * W - want_x)) < 1.0
    assert np.max(np.abs(cam.y * W - want_y)) < 1.0
    assert np.max(np.abs(cam.a)) < 0.003


def test_a_turn_is_measured(project):
    turns = [0, 0, 1.0, 1.0, -0.5, 0, 0, 0, 0, 0]
    path = shaky(project / "footage" / "turn.mp4", [(0, 0)] * 10, turns)
    cam = stab.measure(project, path, 0, 1)
    # PIL turns counter-clockwise for a positive angle; the path counts clockwise on screen as positive
    assert np.allclose(cam.a, [-math.radians(t) for t in turns], atol=math.radians(0.15))


def test_the_measurement_is_cached(project, monkeypatch):
    path = shaky(project / "footage" / "shake.mp4", jitter(10))
    first = stab.measure(project, path, 0, 1)
    monkeypatch.setattr(stab.av, "open", lambda *a, **k: pytest.fail("measured again"))
    again = stab.measure(project, path, 0, 1)
    assert np.allclose(first.x, again.x, atol=1e-6) and np.allclose(first.a, again.a, atol=1e-6)  # stored to 7 places
    assert list((project / "build" / "edit" / "stab").glob("*.json"))


def test_a_pan_is_kept_and_the_jitter_taken_out():
    t = np.arange(0, 10, 1 / 30)
    rng = np.random.default_rng(4)
    shake = rng.normal(0, 0.004, t.shape)
    cam = stab.CameraPath(t, 0.02 * t + shake, np.zeros_like(t), np.zeros_like(t), 9 / 16)
    st = stab.Steady(cam, Stabilize(smooth=1.0))
    inner = slice(30, -30)  # away from the held ends
    assert np.corrcoef(st.cx[inner], -shake[inner])[0, 1] > 0.9
    assert abs(float(np.mean(st.cx[inner]))) < 0.002  # the pan itself is not corrected
    assert 1.0 < st.zoom < 1.1 and st.zoom == pytest.approx(st.wanted)
    fixed = stab.Steady(cam, Stabilize(zoom=1.2))
    assert fixed.zoom == 1.2


def test_a_shake_too_big_to_hide_is_capped():
    t = np.arange(0, 3, 1 / 30)
    cam = stab.CameraPath(t, np.where(np.arange(len(t)) % 2, 0.3, -0.3), np.zeros_like(t), np.zeros_like(t), 0.5625)
    st = stab.Steady(cam, Stabilize())
    assert st.zoom == stab.MAX_ZOOM and st.wanted > stab.MAX_ZOOM


# ---------------------------------------------------------------- the field

@pytest.mark.parametrize(("raw", "want"), [
    (True, Stabilize()),
    ({"smooth": 2}, Stabilize(smooth=2.0)),
    ({"zoom": 1.1}, Stabilize(zoom=1.1)),
])
def test_stabilize_parses_and_round_trips(raw, want):
    tl = parse({"segments": [{"clip": "a.mp4", "stabilize": raw}]})
    assert tl.segments[0].stabilize == want
    assert parse(json.loads(json.dumps(to_dict(tl)))) == tl
    assert validate(Timeline(segments=[Clip("a.mp4", stabilize=want)])).segments[0].stabilize == want


@pytest.mark.parametrize(("raw", "message"), [
    ({"smooth": 0}, "smooth must be a number from 0.1 to 10"),
    ({"zoom": 2}, "zoom must be a number from 1 to 1.5"),
    ({"strength": 1}, "unknown key 'strength'"),
    ("yes", "stabilize must be true"),
])
def test_a_bad_stabilize_names_the_field(raw, message):
    with pytest.raises(ValueError, match=message):
        parse({"segments": [{"clip": "a.mp4", "stabilize": raw}]})


# ---------------------------------------------------------------- render

def test_a_stabilised_render_is_steadier(project):
    shaky(project / "footage" / "shake.mp4", jitter(30, amp=8))

    def render(stabilize):
        (project / "edits").mkdir(exist_ok=True)
        seg = {"clip": "footage/shake.mp4"} | ({"stabilize": stabilize} if stabilize else {})
        (project / "edits" / "s.json").write_text(json.dumps({"size": [W, H], "fps": FPS, "segments": [seg]}))
        r = render_edit(project, "s", sheets=False)
        with av.open(r.video) as c:
            fr = [f.to_ndarray(format="rgb24").astype(float)[60:-60, 100:-100] for f in c.decode(video=0)]
        return r, float(np.mean([np.abs(a - b).mean() for a, b in itertools.pairwise(fr)]))

    _, shaking = render(None)
    r, steady = render({"smooth": 3})
    assert steady < 0.5 * shaking
    assert any("stabilised" in n and "zoomed" in n for n in r.notes)
