"""The OpenTimelineIO export (manimvox.edit.otio), read back with opentimelineio itself: tracks as long as the film,
pieces of footage as clips of their own files, dissolves, speed, pieces only manimvox can draw made into files,
overlays drawn with their transparency, and the sound tracks."""
import json
import shutil
from pathlib import Path

import av
import numpy as np
import pytest

from manimvox import tools
from manimvox.edit.check import check_edit
from manimvox.edit.load import load
from manimvox.edit.otio import export_edit

from .test_edit_render import FIXTURE, footage

otio = pytest.importorskip("opentimelineio")
FPS = 10


@pytest.fixture
def project(tmp_path):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    f = d / "footage"
    f.mkdir()
    footage(f / "red.mp4", 3, (220, 30, 30), 1000)
    footage(f / "blue.mp4", 3, (30, 30, 220), 3000)
    footage(f / "knock.mp4", 1, (0, 0, 0), 500)
    return d


EDIT = {
    "size": [320, 180], "fps": FPS,
    "segments": [
        {"clip": "footage/red.mp4", "end": 2},
        {"clip": "footage/blue.mp4", "start": 1, "end": 2.5, "transition": {"kind": "fade", "seconds": 0.6}, "grade": {"exposure": 0.5}},
        {"title": "The end", "seconds": 1.5},
        {"clip": "footage/red.mp4", "start": 0, "end": 2, "speed": 2},
    ],
    "overlays": [{"text": "Ada Lovelace", "at": 0.5, "until": 1.5, "sub": "Engineer"}],
    "audio": [{"say": "Hello there.", "at": 0.2}, {"sound": "footage/knock.mp4", "at": 3, "end": 0.5}],
}


def export(project, data=EDIT, name="cut"):
    (project / "edits").mkdir(exist_ok=True)
    (project / "edits" / f"{name}.json").write_text(json.dumps(data))
    r = export_edit(project, name, voice="fake:tone")
    return r, otio.adapters.read_from_file(r.path)


def frames(item) -> int:
    return round(item.duration().value)


def test_the_timeline_is_as_long_as_the_film_on_every_track(project):
    r, tl = export(project)
    film = round(check_edit(project, load(project, "cut")).seconds * FPS)
    names = [t.name for t in tl.tracks]
    assert names[0] == "Main" and "Overlays 1" in names and "Footage sound" in names and "Narration" in names
    assert "Sounds 1" in names
    for track in tl.tracks:
        assert round(track.duration().value) == film, track.name
    assert any("levels and ducking are not in the timeline" in n for n in r.notes)


def test_footage_is_named_and_changed_pieces_are_drawn(project):
    r, tl = export(project)
    main = tl.tracks[0]
    clips = [c for c in main if isinstance(c, otio.schema.Clip)]
    assert [Path(c.media_reference.target_url).name for c in clips] == ["red.mp4", "seg01.mp4", "seg02.mp4",
                                                                        "red.mp4"]
    assert clips[0].source_range.start_time.value == 0
    fades = [c for c in main if isinstance(c, otio.schema.Transition)]
    assert len(fades) == 1 and fades[0].transition_type == otio.schema.TransitionTypes.SMPTE_Dissolve
    # the dissolve is centred on the 0.6 s overlap: the red piece is cut at 1.7 s, the blue one starts 0.3 s in
    assert frames(clips[0]) == 17 and fades[0].in_offset.value == 3 and fades[0].out_offset.value == 3
    assert clips[1].source_range.start_time.value == pytest.approx(3)
    assert {Path(p).name for p in r.rendered} >= {"seg01.mp4", "seg02.mp4", "layer00.mov"}
    for p in r.rendered:
        assert Path(p).is_file()
    sped = clips[3]
    assert [e.time_scalar for e in sped.effects] == [2.0]
    assert frames(sped) == 10  # two seconds of the file at double speed


def test_overlays_keep_their_transparency(project):
    _r, tl = export(project)
    layer = next(c for c in tl.tracks[1] if isinstance(c, otio.schema.Clip))
    assert layer.range_in_parent().start_time.value == pytest.approx(0.5 * FPS)
    with av.open(Path(layer.media_reference.target_url.replace("file://", ""))) as c:
        s = c.streams.video[0]
        assert s.codec_context.name == "prores" and "a" in s.codec_context.pix_fmt  # ProRes 4444 with alpha
        fr = [f.to_ndarray(format="rgba") for f in c.decode(s)]
    assert len(fr) == 10 and fr[0][..., 3].max() == 0  # it fades in from nothing at 0.5 s
    mid = fr[5]
    assert mid[2, 2, 3] == 0 and mid[..., 3].max() == 255  # clear round the lower third, solid in it


def test_sound_goes_on_its_own_tracks(project):
    _r, tl = export(project)
    by = {t.name: t for t in tl.tracks}
    said = next(c for c in by["Narration"] if isinstance(c, otio.schema.Clip))
    assert said.range_in_parent().start_time.value == pytest.approx(0.2 * FPS)
    assert Path(said.media_reference.target_url.replace("file://", "")).is_file()
    knock = next(c for c in by["Sounds 1"] if isinstance(c, otio.schema.Clip))
    assert knock.range_in_parent().start_time.value == 30 and frames(knock) == 5
    foot = [c for c in by["Footage sound"] if isinstance(c, otio.schema.Clip)]
    assert Path(foot[0].media_reference.target_url).name == "red.mp4"
    assert not any(Path(c.media_reference.target_url).name == "seg02.mp4" for c in foot)  # a title is silent


def test_a_multicam_becomes_a_clip_per_shot(project):
    data = {"size": [320, 180], "fps": FPS, "segments": [
        {"multicam": ["footage/red.mp4", "footage/blue.mp4"], "offsets": [0, 0.5], "start": 0.5, "end": 2.5,
         "cuts": [[1.5, 1]]}]}
    _r, tl = export(project, data, "multi")
    shots = [c for c in tl.tracks[0] if isinstance(c, otio.schema.Clip)]
    assert [Path(c.media_reference.target_url).name for c in shots] == ["red.mp4", "blue.mp4"]
    assert shots[1].source_range.start_time.value == pytest.approx((1.5 - 0.5) * FPS)  # camera 1's own clock
    sound = [c for c in tl.tracks[-1] if isinstance(c, otio.schema.Clip)]
    assert [Path(c.media_reference.target_url).name for c in sound] == ["red.mp4"] and frames(sound[0]) == 20


def test_the_tool_exports_and_refuses_an_edit_with_findings(project):
    (project / "edits").mkdir(exist_ok=True)
    (project / "edits" / "cut.json").write_text(json.dumps(EDIT))
    r = tools.export_edit(str(project), "cut", voice="fake:tone")
    assert r.ok and r.path.endswith("out/cut.otio")
    (project / "edits" / "bad.json").write_text(json.dumps({"segments": [{"clip": "footage/none.mp4"}]}))
    with pytest.raises(tools.ToolError, match="fix them first"):
        tools.export_edit(str(project), "bad")


def test_the_file_is_plain_json_any_reader_can_open(project):
    r, _tl = export(project)
    data = json.loads(Path(r.path).read_text())
    assert data["OTIO_SCHEMA"] == "Timeline.1" and data["metadata"]["manimvox"]["fps"] == FPS
    assert np.isfinite([c["source_range"]["duration"]["value"] for t in data["tracks"]["children"]
                        for c in t["children"] if "source_range" in c]).all()
