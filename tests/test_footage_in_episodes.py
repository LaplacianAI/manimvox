"""Footage inside explainers: from_video reads a recording of any length from the file as it plays, and
`sound=True` makes the recording heard in the episode when the clip plays, at its playing speed."""
import copy
import shutil
import tracemalloc
from pathlib import Path

import numpy as np
import pytest

from manimvox.post.audio import RATE, read_audio
from manimvox.scenes import from_video
from manimvox.scenes.clip import MAX_FRAMES, SceneError, clip_sound

from .test_edit_render import footage, level_at, peak_freq

FIXTURE = Path(__file__).parent / "fixtures" / "hello"


def test_a_recording_longer_than_the_old_limit_plays_without_holding_its_frames(tmp_path):
    src = footage(tmp_path / "long.mp4", 300, (40, 120, 200), 440, fps=5, size=(64, 36))  # 5 minutes
    tracemalloc.start()
    c = from_video(src, fps=15)
    c.show(len(c.frames) // 2)
    c.show(-1)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert len(c.frames) == 4500 > MAX_FRAMES and c.seconds == pytest.approx(300)
    assert peak < 20e6  # the frames stay in the file
    assert c.pixel_array.shape == (36, 64, 4)  # RGBA, as Manim draws it
    assert abs(int(c.pixel_array[18, 32, 2]) - 200) < 12  # the last frame, decoded on demand
    twin = copy.deepcopy(c)  # Manim copies mobjects when an animation starts; the open file is not copied
    assert twin.frames.path == c.frames.path and twin.frames_digest == c.frames_digest


def test_sound_is_refused_for_a_recording_without_any(tmp_path):
    import av

    silent = tmp_path / "silent.mp4"
    with av.open(str(silent), "w") as box:
        s = box.add_stream("libx264", rate=5)
        s.width, s.height, s.pix_fmt = 32, 18, "yuv420p"
        for _ in range(5):
            box.mux(s.encode(av.VideoFrame.from_ndarray(np.zeros((18, 32, 3), np.uint8), format="rgb24")))
        box.mux(s.encode())
    assert from_video(silent).sound is None
    with pytest.raises(SceneError, match="has no sound; leave out sound=True"):
        from_video(silent, sound=True)


def test_the_played_stretch_of_sound_is_cut_levelled_and_kept_at_pitch(tmp_path, monkeypatch):
    monkeypatch.setenv("MANIMVOX_PROJECT", str(tmp_path))
    src = footage(tmp_path / "talk.mp4", 4, (0, 0, 0), 1000)
    c = from_video(src, start=1.0, sound=True)
    assert c.sound == (str(src.resolve()), 1.0, 0.0)
    wav = clip_sound(c.sound, 0.5, 2.5, run_time=1.0)  # two seconds of the clip, played twice as fast
    import soundfile as sf

    x, rate = sf.read(str(wav), dtype="float32")
    assert rate == RATE and abs(len(x) / rate - 1.0) < 0.02
    assert abs(peak_freq(x.mean(axis=1), 0.2, 0.8) - 1000) < 30  # the pitch kept
    assert clip_sound(c.sound, 0.5, 2.5, run_time=1.0) == wav  # cached


EPISODE = '''from manimvox.kit import *
from manimvox.scenes import from_video


class Ep01(Episode):
    def build(self):
        self.wait(1)
        clip = from_video("footage/talk.mp4", fps=10, end=2, width=6, sound=True)
        self.add(clip)
        self.play(clip.play())
        self.wait(1)
'''


@pytest.mark.slow
def test_a_clip_that_speaks_is_heard_in_the_episode_while_it_plays(tmp_path):
    from manimvox.project import load_project
    from manimvox.runner import render_episode

    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    (d / "footage").mkdir()
    footage(d / "footage" / "talk.mp4", 3, (200, 60, 60), 1000)
    (d / "episodes" / "ep01_hello.py").write_text(EPISODE, encoding="utf-8")
    pr = load_project(d)
    mp4 = render_episode(pr, pr.episode("ep01"), "draft", None)
    x = read_audio(mp4).mean(axis=0)
    assert x.shape[0] / RATE == pytest.approx(3.0, abs=0.1)  # Manim's sound ends at its last sound: the clip's
    assert level_at(x, 1000, 0.2, 0.8) < 0.003  # silent before the clip plays
    assert level_at(x, 1000, 1.3, 2.7) > 0.05  # heard while it plays, from 1 s for its 2 s


@pytest.mark.slow
def test_the_clip_is_heard_at_its_place_when_manim_serves_the_play_from_its_cache(tmp_path):
    from manimvox.project import load_project
    from manimvox.runner import render_episode
    from manimvox.voice import parse_voice

    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    (d / "footage").mkdir()
    footage(d / "footage" / "talk.mp4", 3, (200, 60, 60), 1000)
    (d / "episodes" / "ep01_hello.py").write_text(EPISODE, encoding="utf-8")
    pr = load_project(d)
    for _ in range(2):  # final renders cache each play; the second is served from the cache
        x = read_audio(render_episode(pr, pr.episode("ep01"), "final", parse_voice("fake:tone"))).mean(axis=0)
        assert level_at(x, 1000, 0.2, 0.8) < 0.003 and level_at(x, 1000, 1.3, 2.7) > 0.05
