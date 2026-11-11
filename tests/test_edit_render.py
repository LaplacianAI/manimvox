"""Rendering an edit (manimvox.edit.render): exact lengths, sound in step at every seam, transitions, layers,
ducking, speed with the pitch kept, windows that match the full render, and refusals. Footage is made here:
a solid colour and a pure tone per clip, so pictures and sound can be told apart by measurement."""
import json
import shutil
from pathlib import Path

import av
import numpy as np
import pytest
from PIL import Image as PILImage

from manimvox import tools
from manimvox.edit.render import EditError, render_edit
from manimvox.edit.sound import envelope, samples, stretch
from manimvox.post.audio import RATE, read_audio

FIXTURE = Path(__file__).parent / "fixtures" / "hello"
SIZE = [320, 180]


def footage(path: Path, seconds: float, colour, freq: float, fps: int = 10, size=(160, 90)) -> Path:
    """A solid `colour` picture with a `freq` Hz tone, as H.264/AAC."""
    c = av.open(str(path), "w")
    v = c.add_stream("libx264", rate=fps)
    v.width, v.height, v.pix_fmt = size[0], size[1], "yuv420p"
    a = c.add_stream("aac", rate=RATE, layout="mono")
    img = np.zeros((size[1], size[0], 3), np.uint8)
    img[:] = colour
    for _ in range(round(seconds * fps)):
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


@pytest.fixture
def project(tmp_path):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    f = d / "footage"
    f.mkdir()
    footage(f / "red.mp4", 3, (220, 30, 30), 1000)
    footage(f / "blue.mp4", 3, (30, 30, 220), 3000)
    return d


def edit(project, data, name="cut") -> str:
    p = project / "edits" / f"{name}.json"
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps({"size": SIZE, "fps": 10, **data}))
    return name


def frames_of(path) -> list[np.ndarray]:
    with av.open(str(path)) as c:
        return [f.to_ndarray(format="rgb24") for f in c.decode(c.streams.video[0])]


def centre(frame) -> np.ndarray:
    h, w = frame.shape[:2]
    return frame[h // 2, w // 2].astype(int)


def level_at(x: np.ndarray, freq: float, a: float, b: float) -> float:
    """The amplitude of `freq` in seconds a..b of a mono signal."""
    seg = x[samples(a):samples(b)] * np.hanning(samples(b) - samples(a))
    spec = np.abs(np.fft.rfft(seg)) / (len(seg) / 4)
    k = round(freq * len(seg) / RATE)
    return float(spec[max(0, k - 2):k + 3].max())


def peak_freq(x: np.ndarray, a: float, b: float) -> float:
    seg = x[samples(a):samples(b)] * np.hanning(samples(b) - samples(a))
    spec = np.abs(np.fft.rfft(seg))
    return float(np.argmax(spec[1:]) + 1) * RATE / len(seg)


def render(project, name, **kw):
    return render_edit(project, name, voice="fake:tone", sheets=False, **kw)


# ---------------------------------------------------------------- length and step

def test_two_cuts_give_exactly_their_frames_and_sound_in_step(project):
    edit(project, {"segments": [{"clip": "footage/red.mp4", "end": 2}, {"clip": "footage/blue.mp4", "start": 1,
                                                                        "end": 2.5}]})
    r = render(project, "cut")
    assert r.video.endswith("out/cut.mp4") and r.size == (320, 180)
    fr = frames_of(r.video)
    assert len(fr) == 35
    assert centre(fr[19])[0] > 150 and centre(fr[20])[2] > 150  # the cut is on frame 20, at 2.0 s
    x = read_audio(Path(r.video)).mean(axis=0)
    assert abs(x.shape[0] / RATE - 3.5) < 0.03
    assert abs(peak_freq(x, 1.4, 1.9) - 1000) < 30 and abs(peak_freq(x, 2.1, 2.6) - 3000) < 30


def test_a_crossfade_mixes_picture_and_sound_over_its_overlap(project):
    edit(project, {"segments": [{"clip": "footage/red.mp4", "end": 2},
                                {"clip": "footage/blue.mp4", "end": 2, "transition": {"kind": "fade", "seconds": 1}}]})
    r = render(project, "cut")
    fr = frames_of(r.video)
    assert len(fr) == 30  # 2 + 2 - 1
    mid = centre(fr[15])  # halfway through the fade, which runs 1.0..2.0 s
    assert 80 < mid[0] < 170 and 80 < mid[2] < 170
    x = read_audio(Path(r.video)).mean(axis=0)
    assert level_at(x, 1000, 1.35, 1.65) > 0.03 and level_at(x, 3000, 1.35, 1.65) > 0.03


def test_a_dip_passes_through_the_background(project):
    from manimvox.kit.theme import Theme

    edit(project, {"segments": [{"clip": "footage/red.mp4", "end": 2},
                                {"clip": "footage/blue.mp4", "end": 2, "transition": {"kind": "dip", "seconds": 1}}]})
    fr = frames_of(render(project, "cut").video)
    bg = np.array([int(Theme.from_dict({})["bg"][i:i + 2], 16) for i in (1, 3, 5)])
    assert np.abs(centre(fr[15]) - bg).max() < 20


# ---------------------------------------------------------------- layers

def test_a_picture_sits_in_its_box_and_text_and_drawing_appear(project):
    PILImage.new("RGBA", (40, 20), (0, 255, 0, 255)).save(project / "footage" / "logo.png")
    (project / "fx.py").write_text("import numpy as np\n"
                                   "def white(t):\n    a = np.zeros((10, 10, 4), np.uint8); a[:] = 255; return a\n")
    edit(project, {"segments": [{"clip": "footage/red.mp4", "end": 2}],
                   "overlays": [{"image": "footage/logo.png", "at": 0.5, "until": 2, "box": [200, 20, 80], "fade": 0},
                                {"draw": "fx.py:white", "at": 1, "until": 2, "box": [10, 140, 20]}]})
    fr = frames_of(render(project, "cut").video)
    assert centre(fr[2])[0] > 150  # 0.2 s: no logo yet, red everywhere
    assert fr[2][40, 240][1] < 100
    g = fr[8][40, 240].astype(int)  # 0.8 s: the logo's middle (box 200..280 x 20..60)
    assert g[1] > 180 and g[0] < 80
    assert fr[15][150, 20].min() > 200  # 1.5 s: the drawn white square at 10..30 x 140..160


def test_an_effect_changes_every_frame_and_must_keep_its_size(project):
    (project / "fx.py").write_text("def invert(rgb, t):\n    return 255 - rgb\ndef half(rgb, t):\n    return rgb[::2]\n")
    edit(project, {"segments": [{"clip": "footage/red.mp4", "end": 1, "effects": ["fx.py:invert"]}]})
    c = centre(frames_of(render(project, "cut").video)[5])
    assert c[0] < 80 and c[1] > 180  # red (220, 30, 30) inverted
    edit(project, {"segments": [{"clip": "footage/red.mp4", "end": 1, "effects": ["fx.py:half"]}]})
    with pytest.raises(EditError, match="an effect returned a 320x90 frame for a 320x180 one"):
        render(project, "cut")


def test_frames_made_by_code_play_with_their_sound(project):
    (project / "parts.py").write_text(
        "import numpy as np\nfrom manimvox.edit import frames\n"
        "def make():\n"
        "    t = np.arange(48000) / 48000\n"
        "    snd = np.stack([0.3 * np.sin(2 * np.pi * 2000 * t)] * 2).astype(np.float32)\n"
        "    return frames(lambda u: np.full((90, 160, 3), (0, 200, 0), np.uint8), 1, sound=snd)\n")
    edit(project, {"segments": [{"frames": "parts.py:make"}]})
    r = render(project, "cut")
    assert centre(frames_of(r.video)[4])[1] > 150
    assert abs(peak_freq(read_audio(Path(r.video)).mean(axis=0), 0.2, 0.8) - 2000) < 30


# ---------------------------------------------------------------- sound

def test_footage_dips_under_narration(project):
    edit(project, {"duck_db": -12, "segments": [{"clip": "footage/red.mp4"}], "audio": [{"say": "one two", "at": 1}]})
    r = render(project, "cut")
    x = read_audio(Path(r.video)).mean(axis=0)
    before, during = level_at(x, 1000, 0.2, 0.7), level_at(x, 1000, 1.6, 2.2)  # the fake line runs 1.0..2.4 s
    assert 9 < 20 * np.log10(before / during) < 15
    assert level_at(x, 220, 1.6, 2.2) > 0.05  # the narration's own tone
    srt = Path(r.srt).read_text()
    assert "00:00:01,000 --> 00:00:02,400" in srt and "one two" in srt


def test_speed_halves_the_time_and_keeps_the_pitch(project):
    edit(project, {"segments": [{"clip": "footage/red.mp4", "speed": 2}]})
    r = render(project, "cut")
    assert len(frames_of(r.video)) == 15
    x = read_audio(Path(r.video)).mean(axis=0)
    assert abs(peak_freq(x, 0.3, 1.2) - 1000) < 30


def test_stretch_and_envelope_units():
    t = np.arange(RATE) / RATE
    x = np.stack([np.sin(2 * np.pi * 500 * t)] * 2).astype(np.float32)
    for speed in (0.25, 0.5, 1.5, 4):
        y = stretch(x, speed)
        assert y.shape == (2, round(RATE / speed))
    env = envelope(samples(1), ("cut", 0), ("cut", 0))  # a cut fades over 30 ms at each end
    assert env[0] == 0 and env[samples(0.5)] == 1 and env[-1] < 0.001 and env[samples(0.015)] < 0.6
    fade = envelope(samples(2), ("fade", 1.0), ("cut", 0))
    assert abs(fade[samples(0.5)] - 0.5) < 0.01
    dip = envelope(samples(2), ("dip", 1.0), ("cut", 0))
    assert dip[samples(0.25)] == 0 and abs(dip[samples(0.75)] - 0.5) < 0.01
    part = envelope(samples(2), ("fade", 1.0), ("cut", 0), samples(0.5), samples(0.6))
    assert abs(part[0] - 0.5) < 0.01 and part.shape == (samples(0.1),)


# ---------------------------------------------------------------- drafts and windows

def test_a_window_matches_the_full_render(project):
    edit(project, {"segments": [{"clip": "footage/red.mp4", "end": 2},
                                {"clip": "footage/blue.mp4", "end": 2, "transition": {"kind": "fade", "seconds": 1}}]})
    full = frames_of(render(project, "cut").video)
    r = render(project, "cut", start=1.2, end=2.4)
    assert "build/edit/cut/final_" in r.video and r.seconds == 1.2
    part = frames_of(r.video)
    assert len(part) == 12
    for i, f in enumerate(part):
        assert np.abs(f.astype(int) - full[12 + i].astype(int)).mean() < 4


def test_a_draft_is_480p_in_build(project):
    edit(project, {"size": [1280, 720], "segments": [{"clip": "footage/red.mp4", "end": 1}]})
    r = render_edit(project, "cut", draft=True, sheets=False)
    assert r.size == (854, 480) and r.video.endswith("build/edit/cut/draft.mp4")


# ---------------------------------------------------------------- refusals

def test_a_render_refuses_an_edit_with_findings(project):
    edit(project, {"segments": [{"clip": "footage/red.mp4", "end": 9}]})
    with pytest.raises(EditError, match=r"(?s)1 problem\(s\).*end 9 s is past the file's end"):
        render(project, "cut")


def test_narration_lines_must_not_overlap_or_run_past_the_end(project):
    edit(project, {"segments": [{"clip": "footage/red.mp4"}],
                   "audio": [{"say": "first line", "at": 0}, {"say": "second", "at": 0.5}]})
    with pytest.raises(EditError, match="starts before 'first line' ends at 1.40 s; move it to 1.7 s or later"):
        render(project, "cut")
    edit(project, {"segments": [{"clip": "footage/red.mp4"}], "audio": [{"say": "late", "at": 2.5}]})
    with pytest.raises(EditError, match="past the film's end"):
        render(project, "cut")


def test_the_tool_renders_and_writes_contact_sheets(project):
    edit(project, {"segments": [{"clip": "footage/red.mp4", "end": 1}]})
    r = tools.render_edit(str(project), "cut", allow_download=False)
    assert r.ok and Path(r.video).is_file() and r.sheets and r.srt is None


@pytest.mark.slow
def test_a_manim_scene_lies_over_the_footage_with_its_transparency(project):
    (project / "scenes.py").write_text(
        "from manim import *\n"
        "class Box(Scene):\n"
        "    def construct(self):\n"
        "        self.add(Square(side_length=2, color=GREEN, fill_opacity=1))\n"
        "        self.wait(1)\n")
    edit(project, {"segments": [{"clip": "footage/red.mp4", "end": 2}], "overlays": [{"scene": "scenes.py:Box", "at": 0.5}]})
    fr = frames_of(render(project, "cut").video)
    assert centre(fr[2])[0] > 150  # before the scene
    c = centre(fr[10])  # Manim's GREEN, (131, 193, 103), in the middle
    assert np.abs(c - [131, 193, 103]).max() < 12
    assert fr[10][10, 10][0] > 150  # the corner stays red: the scene's background is transparent
    assert centre(fr[17])[0] > 150  # after its 1 s
