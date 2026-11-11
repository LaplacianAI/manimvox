"""The edit timeline (manimvox.edit): its shape, JSON and Python front ends, function hooks, probing files, and
checking an edit against its files."""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image as PILImage

from manimvox import tools
from manimvox.edit import Clip, Image, Picture, Timeline, frames, from_moviepy
from manimvox.edit.check import check_edit
from manimvox.edit.load import edit_path, frame_source, load, new_edit, resolve_ref
from manimvox.edit.probe import MediaError, probe
from manimvox.edit.timeline import parse, place, to_dict, validate

from .media import make_mp4

FIXTURE = Path(__file__).parent / "fixtures" / "hello"


@pytest.fixture
def project(tmp_path):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    (d / "footage").mkdir()
    make_mp4(d / "footage" / "take.mp4", seconds=4, fps=10)
    PILImage.new("RGBA", (200, 100), (255, 0, 0, 128)).save(d / "footage" / "logo.png")
    return d


def write(project, name, data) -> Path:
    p = project / "edits" / f"{name}.json"
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(data))
    return p


# ---------------------------------------------------------------- shape

def test_a_minimal_edit_gets_the_defaults():
    tl = parse({"segments": [{"clip": "a.mp4"}]})
    assert tl.size == (1920, 1080) and tl.fps == 30 and tl.captions == "srt" and tl.duck_db == -12
    assert tl.segments == (Clip("a.mp4"),)


def test_every_kind_of_item_parses():
    tl = parse({
        "size": [1280, 720], "fps": 25, "captions": "burn",
        "segments": [
            {"title": "Hi", "lines": ["one"]},
            {"clip": "a.mp4", "start": 1, "end": 3, "speed": 2, "volume": -6, "fit": "crop", "crop": [0, 0, 10, 10],
             "transition": {"kind": "fade", "seconds": 0.4}, "effects": ["fx.py:warm"]},
            {"episode": "ep01", "transition": "dip"},
            {"image": "p.png", "seconds": 2, "move": "push"},
            {"frames": "parts.py:intro", "seconds": 3},
        ],
        "overlays": [
            {"image": "logo.png", "at": 0, "until": 2, "box": [10, 10, 100]},
            {"text": "Ada", "sub": "Engineer", "at": 1, "until": 3},
            {"text": "here", "kind": "label", "pos": [5, 5], "at": 0, "until": 1},
            {"clip": "cam.mp4", "at": 0, "until": 1, "box": [0, 0, 50], "volume": -3},
            {"draw": "g.py:arrow", "at": 0, "until": 1},
            {"scene": "s.py:Arrow", "at": 1, "box": [0, 0, 640]},
        ],
        "audio": [{"say": "Hello.", "at": 0.5}, {"music": "m.mp3", "volume": -18}, {"sound": "c.wav", "at": 2}],
    })
    assert [type(s).__name__ for s in tl.segments] == ["Title", "Clip", "Clip", "Image", "Frames"]
    assert tl.segments[2].episode == "ep01" and tl.segments[2].transition.kind == "dip"
    assert [type(o).__name__ for o in tl.overlays] == ["Picture", "Text", "Text", "Inset", "Draw", "Scene"]
    assert tl.overlays[5].until is None and tl.segments[1].effects == ("fx.py:warm",)


@pytest.mark.parametrize(("raw", "message"), [
    ({}, "segments must be a list"),
    ({"segments": []}, "segments must be a list"),
    ({"segments": [{"clip": "a.mp4"}], "colour": 1}, "unknown key 'colour'"),
    ({"segments": [{"clip": "a.mp4", "image": "b.png"}]}, "exactly one of"),
    ({"segments": [{"clip": "a.mp4", "start": 5, "end": 2}]}, "segments[0].end must be a number above 5"),
    ({"segments": [{"clip": "a.mp4", "speed": 10}]}, "segments[0].speed must be a number from 0.25 to 4"),
    ({"segments": [{"clip": "a.mp4", "fit": "crop"}]}, 'needs "crop"'),
    ({"segments": [{"clip": "a.mp4", "transition": "fade"}]}, "nothing before it to fade from"),
    ({"segments": [{"clip": "a.mp4"}, {"clip": "b.mp4", "transition": "wipe"}]}, "segments[1].transition.kind"),
    ({"segments": [{"clip": "a.mp4", "effects": ["warm"]}]}, '"path.py:name"'),
    ({"segments": [{"clip": "a.mp4"}], "size": [1921, 1080]}, "even whole numbers"),
    ({"segments": [{"clip": "a.mp4"}], "overlays": [{"text": "x", "at": 3, "until": 1}]}, "until must be a number above 3"),
    ({"segments": [{"clip": "a.mp4"}], "overlays": [{"text": "x", "kind": "label", "at": 0, "until": 1}]}, 'needs "pos"'),
    ({"segments": [{"clip": "a.mp4"}], "overlays": [{"image": "l.png", "at": 0, "until": 1, "box": [0, 0, 0]}]},
     "width must be above 0"),
    ({"segments": [{"clip": "a.mp4"}], "audio": [{"music": "a.mp3"}, {"music": "b.mp3"}]}, "more than one music"),
    ({"segments": [{"clip": "a.mp4", "mute": "yes"}]}, "mute must be true or false"),
    ({"segments": [{"clip": "a.mp4"}], "version": 2}, "version must be 1"),
])
def test_a_bad_edit_names_the_field(raw, message):
    with pytest.raises(ValueError, match=None) as e:
        parse(raw)
    assert message in str(e.value)


# ---------------------------------------------------------------- JSON and Python agree

def test_json_round_trips_and_leaves_out_defaults():
    raw = {"version": 1, "segments": [{"clip": "a.mp4", "end": 3}, {"image": "p.png", "transition": "fade"}],
           "audio": [{"say": "Hi.", "at": 1}]}
    tl = parse(raw)
    assert to_dict(tl) == raw
    assert parse(to_dict(tl)) == tl


def test_a_python_edit_is_checked_like_its_json():
    tl = validate(Timeline(segments=[Clip("a.mp4", end=3), Image("p.png", transition="fade")],
                           overlays=[Picture("l.png", at=0, until=1, box=[0, 0, 10])]))
    assert tl.segments[1].transition.kind == "fade" and tl.overlays[0].box == (0, 0, 10)
    with pytest.raises(ValueError, match=r"segments\[0\]\.speed"):
        validate(Timeline(segments=[Clip("a.mp4", speed=0)]))


def test_a_python_edit_saves_its_hooks_as_names(project, monkeypatch):
    for mod in [m for m in sys.modules if m == "blocks" or m.startswith("blocks.")]:  # another project's blocks
        monkeypatch.delitem(sys.modules, mod)
    (project / "blocks").mkdir()
    (project / "blocks" / "grade.py").write_text("def warm(rgb, t):\n    return rgb\n")
    (project / "edits").mkdir()
    (project / "edits" / "cut.py").write_text(
        "from blocks.grade import warm\n"
        "from manimvox.edit import Clip, Timeline\n"
        "timeline = Timeline(segments=[Clip('footage/take.mp4', effects=[warm])])\n")
    tl = load(project, "cut")
    fn = tl.segments[0].effects[0]
    assert callable(fn) and fn.__name__ == "warm"
    out = tl.save(project / "edits" / "saved.json")
    assert json.loads(out.read_text())["segments"][0]["effects"] == ["blocks/grade.py:warm"]
    assert load(project, "saved").segments[0].effects == ("blocks/grade.py:warm",)


def test_a_lambda_works_in_python_but_cannot_be_saved(project):
    tl = validate(Timeline(segments=[Clip("footage/take.mp4", effects=[lambda rgb, t: rgb])]))
    assert callable(tl.segments[0].effects[0])
    with pytest.raises(ValueError, match="cannot be written to JSON"):
        tl.save(project / "edits" / "x.json")


def test_loading_reports_the_file(project):
    write(project, "bad", {"segments": [{"clip": "a.mp4", "speed": 9}]})
    with pytest.raises(ValueError, match=r"edits/bad.json: segments\[0\]\.speed"):
        load(project, "bad")
    with pytest.raises(ValueError, match="no edit 'nope'.*available: bad.*manimvox edit new nope"):
        edit_path(project, "nope")
    (project / "edits" / "py.py").write_text("x = 1\n")
    with pytest.raises(ValueError, match="must set `timeline"):
        load(project, "py")


# ---------------------------------------------------------------- placing in time

def test_a_fade_overlaps_its_neighbours_and_shortens_the_film():
    tl = parse({"segments": [{"clip": "a.mp4", "end": 4}, {"clip": "b.mp4", "start": 1, "end": 3, "speed": 2,
                                                          "transition": {"kind": "fade", "seconds": 0.5}},
                             {"title": "End", "seconds": 2}]})
    placed = place(tl, [None, None, None])
    assert [(p.at, p.seconds, p.overlap) for p in placed] == [(0, 4, 0), (3.5, 1, 0.5), (4.5, 2, 0)]


# ---------------------------------------------------------------- hooks

def test_a_hook_resolves_from_the_project_and_reports_what_is_missing(project):
    (project / "fx.py").write_text("def warm(rgb, t):\n    return rgb\nclass Holder:\n    def go(self): pass\n")
    assert resolve_ref(project, "fx.py:warm").__name__ == "warm"
    assert resolve_ref(project, "fx.py:Holder.go").__name__ == "go"
    with pytest.raises(ValueError, match="has no cool"):
        resolve_ref(project, "fx.py:cool")
    with pytest.raises(ValueError, match="no file"):
        resolve_ref(project, "nope.py:warm")
    (project / "broken.py").write_text("raise RuntimeError('boom')\n")
    with pytest.raises(ValueError, match="importing broken.py failed: RuntimeError: boom"):
        resolve_ref(project, "broken.py:x")


def test_a_frame_source_can_be_a_function_that_builds_one(project):
    (project / "parts.py").write_text(
        "import numpy as np\nfrom manimvox.edit import frames\n"
        "def intro():\n    return frames(lambda t: np.zeros((4, 4, 3), np.uint8), 2)\n")
    src = frame_source(project, "parts.py:intro")
    assert src.duration == 2 and src.get_frame(0.5).shape == (4, 4, 3)
    (project / "parts2.py").write_text("def nothing():\n    return 3\n")
    with pytest.raises(ValueError, match="must be \\(or return\\) a frame source"):
        frame_source(project, "parts2.py:nothing")


class FakeMask:
    def get_frame(self, t):
        return np.full((2, 3), 0.5)


class FakeAudio:
    def to_soundarray(self, fps):
        return np.full((fps // 10, 1), 0.25)


class FakeMoviePyClip:
    """What from_moviepy reads of a MoviePy clip: get_frame, duration, mask and audio."""
    duration = 1.5
    mask = FakeMask()
    audio = FakeAudio()

    def get_frame(self, t):
        return np.full((2, 3, 3), 200.0)


def test_from_moviepy_keeps_the_mask_as_transparency_and_the_sound():
    src = from_moviepy(FakeMoviePyClip())
    f = src.get_frame(0.2)
    assert f.dtype == np.uint8 and f.shape == (2, 3, 4) and f[0, 0, 3] == 127 and f[0, 0, 0] == 200
    snd = src.audio(1000)
    assert snd.shape == (2, 100) and np.allclose(snd, 0.25)
    with pytest.raises(ValueError, match="needs a MoviePy clip"):
        from_moviepy(object())


def test_frames_resamples_its_sound():
    src = frames(lambda t: None, 1, sound=np.ones((2, 100), np.float32), rate=100)
    assert src.audio(200).shape == (2, 200) and src.audio(100).shape == (2, 100)


# ---------------------------------------------------------------- probing

def test_probe_reads_videos_and_images(project):
    v = probe(project / "footage" / "take.mp4")
    assert v.kind == "video" and abs(v.seconds - 4) < 0.15 and (v.width, v.height) == (320, 180)
    assert v.fps == 10 and v.audio and v.channels == 1 and "no sound" not in v.describe()
    i = probe(project / "footage" / "logo.png")
    assert i.kind == "image" and i.seconds is None and i.alpha and (i.width, i.height) == (200, 100)
    with pytest.raises(MediaError, match="not found"):
        probe(project / "nope.mp4")
    (project / "junk.mp4").write_bytes(b"not a video")
    with pytest.raises(MediaError, match="cannot read junk.mp4"):
        probe(project / "junk.mp4")


def test_probe_media_writes_contact_sheets(project):
    r = tools.probe_media(str(project), "footage/take.mp4")
    assert r.kind == "video" and r.sheets and all(Path(s).is_file() for s in r.sheets)
    assert Path(r.sheets[0]).parent == project / "sheets" / "probe" / "take"
    assert not tools.probe_media(str(project), "footage/logo.png").sheets


# ---------------------------------------------------------------- checking against the files

def test_a_good_edit_checks_ok_and_shows_where_each_piece_lands(project):
    write(project, "good", {"segments": [{"title": "Hi", "seconds": 2},
                                         {"clip": "footage/take.mp4", "start": 1, "transition": "fade"}],
                            "overlays": [{"image": "footage/logo.png", "at": 0, "until": 3, "box": [10, 10, 200]}],
                            "audio": [{"say": "Hello.", "at": 1}, {"sound": "footage/take.mp4", "at": 2}]})
    r = tools.check(str(project), "edit", "good")
    assert r.ok, r.findings
    assert r.summary == "edit check: ok (4.5 s)"
    assert r.notes == ["0:00.00-0:02.00  title 'Hi'", "0:01.50-0:04.50  clip footage/take.mp4  (fade 0.5 s)"]


def test_check_finds_what_the_files_cannot_give(project):
    tl = parse({
        "size": [640, 360],
        "segments": [{"clip": "footage/take.mp4", "start": 1, "end": 9},
                     {"clip": "footage/take.mp4", "crop": [0, 0, 400, 100], "fit": "crop"},
                     {"clip": "footage/missing.mp4"},
                     {"image": "footage/take.mp4"},
                     {"episode": "ep01"},
                     {"clip": "footage/take.mp4", "end": 1, "transition": {"kind": "fade", "seconds": 2}}],
        "overlays": [{"image": "footage/logo.png", "at": 0, "until": 99, "box": [600, 0, 100]},
                     {"draw": "nope.py:fn", "at": 0, "until": 1},
                     {"clip": "footage/take.mp4", "start": 3, "at": 0, "until": 2, "box": [0, 0, 100]}],
        "audio": [{"sound": "footage/logo.png", "at": 0}, {"say": "late", "at": 500}],
    })
    found = "\n".join(check_edit(project, tl).findings)
    for message in [
        "segments[0] (clip footage/take.mp4): end 9 s is past the file's end",
        "segments[1] (clip footage/take.mp4): crop [0.0, 0.0, 400.0, 100.0] reaches outside the 320x180 picture",
        "segments[2] (clip footage/missing.mp4): ", "not found",
        "segments[3] (image footage/take.mp4): take.mp4 is video, not an image",
        "segments[4] (episode ep01): out/ep01_hello.mp4 is not rendered yet: manimvox render ep01_hello",
        "segments[5] (clip footage/take.mp4): its fade of 2 s is longer than it or the segment before it",
        "overlays[0] (image footage/logo.png): until 99 s is past the film's end",
        "overlays[0] (image footage/logo.png): box [600.0, 0.0, 100.0] (100x50) reaches outside the 640x360 frame",
        "overlays[1] (draw): nope.py:fn: no file",
        "overlays[2] (clip footage/take.mp4): showing 2 s from 3 s runs past the file's end",
        "audio[0] (sound footage/logo.png): logo.png is image, not sound",
        "audio[1] (say 'late'): at 500 s is at or past the film's end",
    ]:
        assert message in found, message


def test_a_scene_hook_must_be_a_class(project):
    (project / "s.py").write_text("def notaclass():\n    pass\nclass Arrow:\n    pass\n")
    base = {"segments": [{"clip": "footage/take.mp4"}]}
    ok = check_edit(project, parse({**base, "overlays": [{"scene": "s.py:Arrow", "at": 0}]}))
    assert ok.ok, ok.findings
    bad = check_edit(project, parse({**base, "overlays": [{"scene": "s.py:notaclass", "at": 0}]}))
    assert "must name a Manim scene class" in bad.findings[0]


def test_a_shape_error_is_a_finding_and_a_missing_edit_is_an_error(project):
    write(project, "bad", {"segments": [{"clip": "a.mp4", "speed": 9}]})
    r = tools.check(str(project), "edit", "bad")
    assert not r.ok and "speed" in r.findings[0]
    with pytest.raises(tools.ToolError, match="no edit 'gone'"):
        tools.check(str(project), "edit", "gone")


def test_new_edit_starts_from_the_files(project):
    r = tools.new_edit(str(project), "first", ["footage/take.mp4", "footage/logo.png"])
    data = json.loads(Path(r.path).read_text())
    assert data == {"version": 1, "segments": [{"clip": "footage/take.mp4"}, {"image": "footage/logo.png"}]}
    with pytest.raises(tools.ToolError, match="already exists"):
        tools.new_edit(str(project), "first", ["footage/take.mp4"])
    with pytest.raises(ValueError, match="give videos"):
        new_edit(project, "other", ["notes.txt"], base=project)

