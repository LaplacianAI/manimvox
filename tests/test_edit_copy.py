"""The picture copied, not re-encoded (manimvox.edit.copy): an untouched clip's frames come out identical to the
file's, with the sound mixed as usual; every other edit is encoded, and the notes say why."""
import json
import shutil

import av
import numpy as np
import pytest

from manimvox.edit import copy as copy_mod
from manimvox.edit.render import render_edit
from manimvox.post.audio import RATE, read_audio

from .test_edit_render import FIXTURE, level_at

W, H, FPS = 320, 180, 10


def camera(path, seconds=4.0, size=(W, H), freq=1000.0):
    """Made as a camera makes it: High profile, a keyframe each second, B-frames. Frame i is grey level 5i."""
    c = av.open(str(path), "w")
    v = c.add_stream("libx264", rate=FPS)
    v.width, v.height, v.pix_fmt = size[0], size[1], "yuv420p"
    v.options = {"profile": "high", "g": str(FPS), "keyint_min": str(FPS), "bf": "2", "sc_threshold": "0"}
    a = c.add_stream("aac", rate=RATE, layout="mono")
    for i in range(round(seconds * FPS)):
        img = np.full((size[1], size[0], 3), 5 * i, np.uint8)
        img[:20, :20] = (255, 0, 0)
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
    return path


def decoded(path) -> list[np.ndarray]:
    with av.open(str(path)) as c:
        return [f.to_ndarray(format="rgb24") for f in c.decode(video=0)]


@pytest.fixture
def project(tmp_path):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    (d / "footage").mkdir()
    camera(d / "footage" / "take.mp4")
    return d


def render(project, seg, copy=True, **kw):
    (project / "edits").mkdir(exist_ok=True)
    data = {"size": [W, H], "fps": FPS, "segments": [seg]} | kw.pop("extra", {})
    (project / "edits" / "c.json").write_text(json.dumps(data))
    return render_edit(project, "c", voice="fake:tone", sheets=False, copy=copy, **kw)


def test_an_untouched_clip_is_copied_frame_for_frame(project):
    r = render(project, {"clip": "footage/take.mp4", "start": 1, "end": 3},
               extra={"audio": [{"say": "Look here.", "at": 0.5}]})
    assert any("not re-encoded" in n for n in r.notes), r.notes
    src, out = decoded(project / "footage" / "take.mp4"), decoded(r.video)
    assert len(out) == 20
    assert all(np.array_equal(a, b) for a, b in zip(out, src[10:30], strict=True))  # the camera's own pixels
    with av.open(r.video) as c:  # in step with the sound: a B-frame's decode delay must not push the picture on
        assert next(c.decode(video=0)).time == 0
    x = read_audio(r.video).mean(axis=0)
    assert abs(x.shape[0] / RATE - 2.0) < 0.05
    # mixed as usual: the clip's own 1 kHz under the narration (the test voice speaks at 220 Hz)
    assert level_at(x, 1000, 0.6, 1.9) > 0.01 and level_at(x, 220, 0.6, 1.2) > 0.01


def test_a_clip_to_the_end_of_its_file_is_copied(project):
    r = render(project, {"clip": "footage/take.mp4", "start": 2})
    assert any("not re-encoded" in n for n in r.notes), r.notes
    assert len(decoded(r.video)) == 20


def test_without_copy_the_film_is_encoded_as_before(project):
    r = render(project, {"clip": "footage/take.mp4", "start": 1, "end": 3}, copy=False)
    assert not any(n.startswith("copy:") for n in r.notes)
    assert len(decoded(r.video)) == 20


@pytest.mark.parametrize(("seg", "extra", "why"), [
    ({"clip": "footage/take.mp4", "start": 1.3, "end": 3}, {}, "not on a keyframe (the nearest is 1.000 s)"),
    ({"clip": "footage/take.mp4", "start": 1, "end": 2.5}, {}, "neither on a keyframe nor at the file's end"),
    ({"clip": "footage/take.mp4", "end": 2, "grade": {"exposure": 0.2}}, {}, "the picture is changed (a grade)"),
    ({"clip": "footage/take.mp4", "end": 2, "speed": 2}, {}, "a speed change"),
    ({"clip": "footage/take.mp4", "end": 2}, {"overlays": [{"text": "Hi", "at": 0, "until": 1}]}, "overlays"),
    ({"clip": "footage/take.mp4", "end": 2}, {"captions": "burn"}, "burned-in captions"),
    ({"clip": "footage/take.mp4", "end": 2}, {"size": [640, 360]}, "is 320x180, the film 640x360"),
    ({"clip": "footage/take.mp4", "end": 2}, {"fps": 25}, "is 10 fps, the film 25"),
])
def test_anything_that_changes_the_picture_is_encoded_and_says_why(project, seg, extra, why):
    r = render(project, seg, extra=extra)
    note = next(n for n in r.notes if n.startswith("copy:"))
    assert why in note and note.endswith("encoded instead"), note
    assert decoded(r.video)


def test_two_clips_are_encoded(project):
    (project / "edits").mkdir(exist_ok=True)
    (project / "edits" / "c.json").write_text(json.dumps({"size": [W, H], "fps": FPS, "segments": [
        {"clip": "footage/take.mp4", "end": 1}, {"clip": "footage/take.mp4", "start": 2, "end": 3}]}))
    r = render_edit(project, "c", sheets=False, copy=True)
    assert any("the film is more than one clip" in n for n in r.notes)


def test_a_draft_or_window_is_never_copied(project):
    r = render(project, {"clip": "footage/take.mp4", "start": 1, "end": 3}, draft=True)
    assert any("only the final render of the whole film is copied" in n for n in r.notes)


def test_a_copy_that_fails_its_check_is_encoded_instead(project, monkeypatch):
    monkeypatch.setattr(copy_mod, "write_copied", lambda *a, **k: False)
    r = render(project, {"clip": "footage/take.mp4", "start": 1, "end": 3})
    assert any("did not decode to the film's frames; encoded instead" in n for n in r.notes)
    assert len(decoded(r.video)) == 20
