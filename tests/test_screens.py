import shutil
from pathlib import Path

import av
import numpy as np
import pytest
from PIL import Image

from manimvox.kit.text import STAGE_BOTTOM, STAGE_TOP
from manimvox.scenes import (
    SceneError,
    callout,
    click,
    cursor,
    from_frames,
    from_video,
    point,
    screenshot,
    spotlight,
    still,
    window,
)

FIXTURE = Path(__file__).parent / "fixtures" / "hello"
COLOURS = {"tl": (200, 0, 0), "tr": (0, 200, 0), "bl": (0, 0, 200), "br": (200, 200, 0)}


def quadrants(w=320, h=180):
    """Four solid quadrants, so what a zoom shows can be read off one pixel."""
    a = np.zeros((h, w, 3), np.uint8)
    a[: h // 2, : w // 2], a[: h // 2, w // 2:] = COLOURS["tl"], COLOURS["tr"]
    a[h // 2:, : w // 2], a[h // 2:, w // 2:] = COLOURS["bl"], COLOURS["br"]
    return a


def centre_rgb(clip):
    h, w = clip.pixel_array.shape[:2]
    return tuple(int(v) for v in clip.pixel_array[h // 2, w // 2, :3])


def run(anim, alpha=1.0):
    anim.begin()
    anim.interpolate(alpha)
    return anim


def test_screenshot_reads_a_file_in_its_own_pixels(tmp_path):
    Image.fromarray(quadrants()).save(tmp_path / "s.png")
    c = screenshot(tmp_path / "s.png", width=8.0)
    assert c.pixels == (320, 180) and c.space == (320.0, 180.0) and c.width == pytest.approx(8.0)


def test_a_missing_screenshot_says_where_it_looked(tmp_path):
    with pytest.raises(SceneError, match="not found"):
        screenshot(tmp_path / "nope.png")


def test_framing_pads_keeps_the_clip_shape_and_stays_inside():
    c = still(quadrants())  # 320 x 180
    x, y, w, h = c.framing(10, 10, 40, 10, pad=0.0)
    assert w / h == pytest.approx(320 / 180) and w == pytest.approx(40)
    assert (x, y) == pytest.approx((10, 15 - h / 2)) or y == 0  # centred, or pushed inside at the top
    assert x >= 0 and y >= 0 and x + w <= 320 and y + h <= 180
    assert c.framing(0, 0, 400, 400) == pytest.approx((0, 0, 320, 180))  # bigger than the source: all of it
    with pytest.raises(SceneError, match="not inside"):
        c.framing(500, 10, 20, 20)


def test_zoom_shows_the_region_inside_the_clips_own_frame():
    c = still(quadrants(), width=8.0)
    size = (c.width, c.height)
    assert centre_rgb(c) in COLOURS.values()
    run(c.zoom(0, 0, 160, 90, pad=0.0))  # the top-left quadrant
    assert c.view == pytest.approx((0, 0, 160, 90))
    assert centre_rgb(c) == COLOURS["tl"] and (c.width, c.height) == pytest.approx(size)
    run(c.zoom(160, 90, 160, 90, pad=0.0))
    assert centre_rgb(c) == COLOURS["br"]
    run(c.zoom_out())
    assert c.view == c.whole


def test_zoom_moves_steadily_from_where_it_is():
    c = still(quadrants())
    z = run(c.zoom(0, 0, 80, 45, pad=0.0), 0.0)
    assert c.view == pytest.approx(c.whole)
    widths = []
    for a in (0.25, 0.5, 0.75, 1.0):
        z.interpolate_mobject(a)  # no rate function: the raw progress
        widths.append(c.view[2])
    ratios = [b / a for a, b in zip([320] + widths, widths)]
    assert ratios == pytest.approx([ratios[0]] * 4)  # geometric: the same factor every quarter


def test_at_follows_the_zoom():
    c = still(quadrants(), width=8.0)
    run(c.zoom(80, 45, 160, 90, pad=0.0))
    assert c.at(80, 45) == pytest.approx(c.get_corner(np.array([-1, 1, 0])))
    assert c.at(240, 135) == pytest.approx(c.get_corner(np.array([1, -1, 0])))


def test_a_zoomed_clip_has_a_different_cache_key():
    from manim.utils.hashing import _get_json, _Memoizer

    a, b = still(quadrants()), still(quadrants())
    run(b.zoom(0, 0, 160, 90))
    key = lambda c: _get_json(c, _Memoizer(), include_pixel_array=True)
    assert key(a) != key(b)


def test_spotlight_rings_the_region_and_dims_the_rest():
    c = still(quadrants(), width=8.0)
    s = spotlight(c, (160, 0, 160, 90))  # the top-right quadrant
    assert s.ring.get_center() == pytest.approx(c.at(240, 45))
    assert s.mask.width == pytest.approx(c.width) and s.mask.get_fill_opacity() == pytest.approx(0.72)


def test_overlays_refuse_a_region_the_zoom_has_hidden():
    c = still(quadrants())
    run(c.zoom(0, 0, 100, 56, pad=0.0))
    with pytest.raises(SceneError, match="outside what the clip shows"):
        spotlight(c, (250, 150, 20, 20))
    with pytest.raises(SceneError, match=r"\(x, y, w, h\)"):
        spotlight(c, (1, 2, 3))


@pytest.mark.parametrize("side", ["right", "left", "up", "down"])
def test_callout_sits_on_its_side_and_on_the_stage(side):
    c = still(quadrants(), width=12.0)
    g = callout(c, (140, 80, 40, 20), "this button", side=side)
    ring, label = g.ring.get_center(), g.label.get_center()
    axis = {"right": (0, 1), "left": (0, -1), "up": (1, 1), "down": (1, -1)}[side]
    assert (label[axis[0]] - ring[axis[0]]) * axis[1] > 0
    assert -6.6 - 1e-6 <= g.label.get_left()[0] and g.label.get_right()[0] <= 6.6 + 1e-6
    assert STAGE_BOTTOM - 1e-6 <= g.label.get_bottom()[1] and g.label.get_top()[1] <= STAGE_TOP + 1e-6


def test_callout_is_kept_on_the_stage_near_the_edge():
    c = still(quadrants(), width=12.0)
    g = callout(c, (300, 80, 20, 20), "a long label at the right edge", side="right")
    assert g.label.get_right()[0] <= 6.6 + 1e-6
    with pytest.raises(SceneError, match="side must be"):
        callout(c, (0, 0, 10, 10), "x", side="north")


def test_cursor_points_its_tip_and_clicks():
    c = still(quadrants(), width=8.0)
    p = cursor()
    target = c.at(100, 30)
    run(point(p, target))
    assert p.tip.get_center() == pytest.approx(target)
    assert click(p).run_time == pytest.approx(0.6)


def test_window_puts_a_bar_above_the_clip():
    c = still(quadrants(), width=8.0)
    w = window(c, url="example.com")
    assert w.bar.get_bottom()[1] < c.get_top()[1] < w.bar.get_top()[1]
    assert w.border.width == pytest.approx(c.width) and w.label.text == "example.com"
    assert window(c).label is None


STEP = 12  # grey levels between recording frames: 20 frames fit in 0..255


def _recording(path, seconds, fps, size=(64, 36)):
    """A video whose frame i is grey level STEP * i, so the frame a clip shows can be read off a pixel."""
    with av.open(str(path), "w") as box:
        s = box.add_stream("libx264", rate=fps)
        s.width, s.height, s.pix_fmt = size[0], size[1], "yuv420p"
        s.options = {"qp": "0"}
        for i in range(round(seconds * fps)):
            frame = av.VideoFrame.from_ndarray(np.full((size[1], size[0], 3), STEP * i, np.uint8), format="rgb24")
            box.mux(s.encode(frame))
        box.mux(s.encode())


def source_frame(clip, i):
    """Which recording frame clip frame `i` shows (colour conversion blurs the grey level by a few steps)."""
    return round(int(clip.show(i).pixel_array[10, 10, 0]) / STEP)


def test_from_video_samples_at_the_clip_rate(tmp_path):
    _recording(tmp_path / "r.mp4", seconds=1, fps=10)
    c = from_video(tmp_path / "r.mp4", fps=5)
    assert len(c.frames) == 5 and c.seconds == pytest.approx(1.0)
    assert [source_frame(c, i) for i in range(5)] == [0, 2, 4, 6, 8]  # every other frame


def test_from_video_holds_frames_when_the_recording_has_fewer(tmp_path):
    _recording(tmp_path / "r.mp4", seconds=1, fps=5)
    c = from_video(tmp_path / "r.mp4", fps=10)
    assert len(c.frames) == 10 and c.seconds == pytest.approx(1.0)
    assert [source_frame(c, i) for i in range(10)] == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]  # each held, not the next


def test_from_video_trims_and_keeps_positions_in_the_recordings_pixels(tmp_path):
    _recording(tmp_path / "r.mp4", seconds=2, fps=10, size=(320, 180))
    c = from_video(tmp_path / "r.mp4", fps=10, start=0.5, end=1.0, max_width=160)
    assert len(c.frames) == 5 and source_frame(c, 0) == 5
    assert c.pixels == (160, 90) and c.space == (320, 180)
    assert c.at(160, 90) == pytest.approx(c.get_center())
    with pytest.raises(SceneError, match="no frames"):
        from_video(tmp_path / "r.mp4", start=5)


EPISODE = '''from manimvox.kit import *
from manimvox.scenes import callout, click, cursor, point, screenshot, spotlight, window


class Ep01(Episode):
    def build(self):
        shot = screenshot("research/screen.png", width=9.6).move_to(STAGE_CENTER + DOWN * 0.2)
        self.say("The page.", FadeIn(Group(window(shot, url="example.com"), shot)))
        p = cursor().move_to(shot.get_center())
        self.say("Point and click.", FadeIn(p), point(p, shot.at(240, 45)))
        self.say("Click.", click(p))
        s = spotlight(shot, (160, 0, 160, 90))
        self.say("Focus.", FadeIn(s))
        self.say("Zoom.", FadeOut(s), FadeOut(p), shot.zoom(160, 90, 160, 90))
        tag = callout(shot, (200, 110, 60, 30), "here", side="up")
        self.say("Here.", FadeIn(tag))
        self.say("Back.", FadeOut(tag), shot.zoom_out())
'''


@pytest.mark.slow
def test_a_screenshot_tour_renders(tmp_path):
    from manimvox.checks.layout import check_layout, load_layout
    from manimvox.project import load_project
    from manimvox.runner import render_episode

    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    (d / "research").mkdir(exist_ok=True)
    Image.fromarray(quadrants()).save(d / "research" / "screen.png")
    (d / "episodes" / "ep01_hello.py").write_text(EPISODE, encoding="utf-8")
    pr = load_project(d)
    mp4 = render_episode(pr, pr.episode("ep01"), "draft", None)
    assert mp4.exists()
    layout = next((d / "build").rglob("layout.json"))
    assert check_layout(load_layout(layout)) == []


def test_play_runs_part_of_a_recording_at_real_speed():
    c = from_frames(lambda t: np.full((9, 16, 3), int(t * 10) * 8, np.uint8), seconds=3, fps=10)  # 30 frames
    p = c.play(start=1.0, end=2.0)
    assert p.run_time == pytest.approx(1.0)
    p.begin()
    p.interpolate(0.0)
    assert c.shown == 10
    p.interpolate(0.999)
    assert c.shown == 19
    assert c.play(run_time=4, start=1.0, end=2.0).run_time == 4
    with pytest.raises(SceneError, match="start and end"):
        c.play(start=2.0, end=1.0)
    with pytest.raises(SceneError, match="start and end"):
        c.play(end=9.0)


def test_a_zoom_to_the_edge_stays_inside_the_source_and_lands_exactly():
    c = still(quadrants())
    z = c.zoom(0, 0, 100, 56, pad=0.0)
    z.begin()
    for a in np.linspace(0, 1, 41):
        z.interpolate_mobject(a)
        x, y, w, h = c.view
        assert x >= 0 and y >= 0 and x + w <= 320 + 1e-9 and y + h <= 180 + 1e-9
    out = c.zoom_out()
    out.begin()
    out.interpolate_mobject(1.0)
    assert c.view == c.whole  # exactly: the whole picture again, not a hair-cropped copy
