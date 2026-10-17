import io
import shutil
from pathlib import Path

import av
import numpy as np
import pytest
from manim import tempconfig
from PIL import Image

from manimvox.scenes import SceneError, from_cairo, from_frames, png, still

FIXTURE = Path(__file__).parent / "fixtures" / "hello"


def solid(v, size=(16, 9)):
    return np.full((size[1], size[0], 3), v, np.uint8)


def test_clip_width_is_in_scene_units_at_any_resolution():
    sizes = []
    for h, w in ((480, 854), (1080, 1920)):
        with tempconfig({"pixel_height": h, "pixel_width": w}):
            c = still(solid(10, (160, 90)), width=6.0)
            sizes.append((round(c.width, 3), round(c.height, 3)))
    assert sizes[0] == sizes[1] == (6.0, 3.375)


def test_play_steps_through_every_frame():
    c = from_frames(lambda t: solid(int(t * 100)), seconds=3, fps=1)  # frames of 0, 100, 200
    anim = c.play()
    assert anim.run_time == pytest.approx(3.0)
    seen = []
    for alpha in (0.0, 0.34, 0.67, 1.0):
        anim.interpolate_mobject(alpha)
        seen.append(int(c.pixel_array[0, 0, 0]))
    assert seen == [0, 100, 200, 200]


def test_play_stretches_to_the_run_time_given():
    c = from_frames(lambda t: solid(0), seconds=1, fps=10)
    assert c.play(run_time=4).run_time == 4


def test_from_frames_accepts_pil_images_and_arrays():
    c = from_frames(lambda t: Image.new("RGB", (16, 9), (255, 0, 0)) if t < 0.5 else solid(7), seconds=1, fps=2)
    assert len(c.frames) == 2 and c.seconds == 1.0


@pytest.mark.parametrize("bad", [np.zeros((9, 16), np.uint8), np.zeros((9, 16, 3), np.float32), "nope"])
def test_from_frames_rejects_what_is_not_a_frame(bad):
    with pytest.raises(SceneError, match="a frame must be"):
        from_frames(lambda t: bad, seconds=1, fps=1)


def test_frames_must_share_one_size():
    with pytest.raises(SceneError, match="same size"):
        from_frames(lambda t: solid(0, (16, 9) if t < 1 else (32, 18)), seconds=2, fps=1)


@pytest.mark.parametrize("seconds,fps", [(0, 10), (1, 0), (-1, 10), (200, 30)])
def test_frame_count_limits(seconds, fps):
    with pytest.raises(SceneError):
        from_frames(lambda t: solid(0), seconds=seconds, fps=fps)


def test_from_cairo_returns_straight_rgba():
    def draw(ctx, t, w, h):
        ctx.set_source_rgba(1, 0, 0, 0.5)
        ctx.rectangle(0, 0, w, h)
        ctx.fill()

    c = from_cairo(draw, seconds=1, fps=1, size=(8, 4))
    px = c.pixel_array[0, 0]
    assert abs(int(px[0]) - 255) <= 1 and px[1] == 0 and abs(int(px[3]) - 128) <= 1


def test_png_roundtrip_keeps_pixels():
    a = np.random.default_rng(0).integers(0, 256, (9, 16, 4), dtype=np.uint8)
    assert np.array_equal(np.asarray(Image.open(io.BytesIO(png(a)))), a)


EPISODE = '''from manimvox.kit import *
from manimvox.scenes import from_frames


class Ep01(Episode):
    def build(self):
        clip = from_frames(lambda t: np.full((90, 160, 3), int(t * 120), np.uint8), seconds=3, fps=1, width=14.3)
        self.add(clip)
        self.play(clip.play(), run_time=3)
'''


@pytest.mark.slow
def test_a_clip_plays_in_a_rendered_episode(tmp_path):
    from manimvox.project import load_project
    from manimvox.runner import render_episode

    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    (d / "episodes" / "ep01_hello.py").write_text(EPISODE, encoding="utf-8")
    pr = load_project(d)
    mp4 = render_episode(pr, pr.episode("ep01"), "draft", None)
    with av.open(str(mp4)) as c:
        grey = [int(f.to_ndarray(format="gray")[200, 300]) for f in c.decode(video=0)]
    assert grey[0] < 40 and max(grey) > 200 and len({g // 40 for g in grey}) >= 3


def _play_key(clip):
    """The text Manim hashes for a clip in a play call (include_pixel_array, as for animations)."""
    from manim.utils.hashing import _get_json, _Memoizer

    return _get_json(clip, _Memoizer(), include_pixel_array=True)


def test_cache_key_changes_when_a_later_frame_changes():
    a = from_frames(lambda t: solid(0 if t < 1 else 50), seconds=3, fps=1)
    b = from_frames(lambda t: solid(0 if t < 1 else 200), seconds=3, fps=1)  # same first frame
    same = from_frames(lambda t: solid(0 if t < 1 else 50), seconds=3, fps=1)
    assert _play_key(a) != _play_key(b)
    assert _play_key(a) == _play_key(same)


def test_cache_key_changes_with_fps():
    a = from_frames(lambda t: solid(5), seconds=2, fps=1)
    b = from_frames(lambda t: solid(5), seconds=1, fps=2)
    assert _play_key(a) != _play_key(b)
