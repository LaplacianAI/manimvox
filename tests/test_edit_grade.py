"""Colour grading (manimvox.edit.grade): each control on known colours, .cube LUTs, the field in JSON and Python,
the check, and a graded render that leaves the letterbox in the theme's colour."""
import json
import shutil
from pathlib import Path

import av
import numpy as np
import pytest

from manimvox.edit import Clip, Grade, Timeline
from manimvox.edit.check import check_edit
from manimvox.edit.grade import apply_table, build_table, grade_colors, read_cube
from manimvox.edit.render import render_edit
from manimvox.edit.timeline import parse, to_dict, validate

from .test_edit_render import FIXTURE, footage

GREY = np.array([[0.5, 0.5, 0.5]], np.float32)
RED = np.array([[0.8, 0.2, 0.2]], np.float32)


def g(x, **kw):
    return grade_colors(x, Grade(**kw))[0]


def cube_file(path: Path, n: int, fn) -> Path:
    """A 3D .cube of size n whose output at (r, g, b) is fn(r, g, b); red changes fastest, as the format says."""
    rows = []
    for b in range(n):
        for gg in range(n):
            for r in range(n):
                rows.append(" ".join(f"{v:.6f}" for v in fn(r / (n - 1), gg / (n - 1), b / (n - 1))))
    path.write_text(f"TITLE \"test\"\n# a comment\nLUT_3D_SIZE {n}\n" + "\n".join(rows) + "\n")
    return path


# ---------------------------------------------------------------- the controls

def test_the_default_grade_changes_nothing():
    rgb = np.random.default_rng(1).integers(0, 256, (40, 60, 3), dtype=np.uint8)
    assert np.array_equal(apply_table(build_table(Grade()), rgb), rgb)


def test_each_control_moves_colour_the_way_it_says():
    assert g(GREY, exposure=1)[0] > 0.6 and g(GREY, exposure=-1)[0] < 0.4
    warm, cool = g(GREY, temperature=0.6), g(GREY, temperature=-0.6)
    assert warm[0] > warm[2] and cool[2] > cool[0]
    assert g(GREY, tint=0.6)[1] < g(GREY, tint=0.6)[0]  # magenta: less green
    assert g(GREY, tint=-0.6)[1] > g(GREY, tint=-0.6)[0]
    assert np.ptp(g(RED, saturation=0)) < 1e-6  # no colour left
    assert np.ptp(g(RED, saturation=1.5)) > np.ptp(RED[0])
    dark = np.array([[0.2, 0.2, 0.2]], np.float32)
    assert g(dark, contrast=1.5)[0] < 0.2 and g(np.array([[0.8] * 3], np.float32), contrast=1.5)[0] > 0.8
    black = np.zeros((1, 3), np.float32)
    assert g(black, lift=0.1)[0] == pytest.approx(0.1, abs=1e-6)
    assert g(np.ones((1, 3), np.float32), gain=0.8)[0] == pytest.approx(0.8, abs=1e-6)
    assert g(GREY, gamma=2)[0] > 0.5
    per = g(GREY, gain=(1.2, 1.0, 0.8))
    assert per[0] > per[1] > per[2]


def test_white_balance_keeps_the_brightness():
    luma = np.array([0.2126, 0.7152, 0.0722])
    assert abs(float(luma @ g(GREY, temperature=0.8)) - 0.5) < 0.04


def test_everything_stays_in_range_and_alpha_is_kept():
    x = np.random.default_rng(2).random((500, 3), np.float32)
    y = grade_colors(x, Grade(exposure=3, contrast=3, saturation=3, gain=4))
    assert y.min() >= 0 and y.max() <= 1
    rgba = np.full((4, 4, 4), 200, np.uint8)
    rgba[..., 3] = 77
    out = apply_table(build_table(Grade(exposure=-1)), rgba)
    assert out.shape == (4, 4, 4) and np.all(out[..., 3] == 77) and out[0, 0, 0] < 200


# ---------------------------------------------------------------- .cube LUTs

def test_a_cube_lut_is_read_in_its_order_and_applied_last(tmp_path):
    ident = read_cube(cube_file(tmp_path / "id.cube", 5, lambda r, gg, b: (r, gg, b)))
    x = np.random.default_rng(3).random((200, 3), np.float32)
    assert np.allclose(ident(x), x, atol=1e-5)
    swap = read_cube(cube_file(tmp_path / "swap.cube", 9, lambda r, gg, b: (b, gg, r)))
    assert np.allclose(swap(np.array([[0.9, 0.5, 0.1]], np.float32)), [[0.1, 0.5, 0.9]], atol=1e-5)
    # applied after the other controls: saturation 0 makes grey, which the swap leaves grey
    out = grade_colors(RED, Grade(saturation=0), swap)[0]
    assert np.ptp(out) < 1e-5


@pytest.mark.parametrize(("text", "message"), [
    ("LUT_1D_SIZE 4\n0 0 0\n", "1D LUT"),
    ("LUT_3D_SIZE 2\n0 0 0\n1 1 1\n", "should have 8 rows"),
    ("0 0 0\n", "no LUT_3D_SIZE"),
    ("LUT_3D_SIZE 2\nDOMAIN_MIN 1 1 1\nDOMAIN_MAX 0 0 0\n" + "0 0 0\n" * 8, "DOMAIN_MAX must be above"),
    ("LUT_3D_SIZE 2\n0 zero 0\n", "line 2"),
])
def test_a_bad_cube_says_what_is_wrong(tmp_path, text, message):
    p = tmp_path / "bad.cube"
    p.write_text(text)
    with pytest.raises(ValueError, match=message):
        read_cube(p)


# ---------------------------------------------------------------- the field

def test_grade_parses_round_trips_and_leaves_out_defaults():
    raw = {"segments": [{"clip": "a.mp4", "grade": {"exposure": 0.3, "gain": [1.1, 1, 0.9], "lut": "looks/a.cube"}},
                        {"image": "b.png", "grade": {"saturation": 0}}]}
    tl = parse(raw)
    assert tl.segments[0].grade == Grade(exposure=0.3, gain=(1.1, 1.0, 0.9), lut="looks/a.cube")
    assert tl.segments[1].grade == Grade(saturation=0.0)
    out = to_dict(tl)
    assert out["segments"][0]["grade"] == {"exposure": 0.3, "gain": [1.1, 1.0, 0.9], "lut": "looks/a.cube"}
    assert parse(out) == tl
    assert "grade" not in to_dict(parse({"segments": [{"clip": "a.mp4"}]}))["segments"][0]


def test_a_python_grade_is_checked_like_its_json():
    tl = validate(Timeline(segments=[Clip("a.mp4", grade=Grade(temperature=0.2))]))
    assert tl.segments[0].grade == Grade(temperature=0.2)
    with pytest.raises(ValueError, match=r"segments\[0\].grade.exposure must be a number from -4 to 4"):
        validate(Timeline(segments=[Clip("a.mp4", grade=Grade(exposure=9))]))


@pytest.mark.parametrize(("grade", "message"), [
    ({"bright": 1}, "unknown key 'bright'"),
    ({"contrast": -1}, "contrast must be a number from 0 to 3"),
    ({"lift": [0, 0]}, r"lift must be a number or \[r, g, b\]"),
    ("warm", "must be an object"),
])
def test_a_bad_grade_names_the_field(grade, message):
    with pytest.raises(ValueError, match=message):
        parse({"segments": [{"clip": "a.mp4", "grade": grade}]})


def test_a_title_card_has_no_grade():
    with pytest.raises(ValueError, match="unknown key 'grade'"):
        parse({"segments": [{"title": "Hi", "grade": {"exposure": 1}}]})


# ---------------------------------------------------------------- check and render

@pytest.fixture
def project(tmp_path):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    (d / "footage").mkdir()
    footage(d / "footage" / "square.mp4", 1, (200, 120, 60), 1000, size=(90, 90))
    return d


def edit(project, grade) -> str:
    (project / "edits").mkdir(exist_ok=True)
    (project / "edits" / "g.json").write_text(json.dumps(
        {"size": [320, 180], "fps": 10, "segments": [{"clip": "footage/square.mp4", "grade": grade}]}))
    return "g"


def test_check_finds_a_missing_or_broken_lut(project):
    (project / "bad.cube").write_text("LUT_3D_SIZE 2\n")
    for lut, message in [("none.cube", "no file none.cube"), ("bad.cube", "bad.cube should have 8 rows")]:
        rep = check_edit(project, parse({"segments": [{"clip": "footage/square.mp4", "grade": {"lut": lut}}]}))
        assert any(f"grade.lut: {message}" in f for f in rep.findings), rep.findings


def test_a_graded_render_grades_the_picture_and_not_the_letterbox(project):
    def frame(path):
        with av.open(path) as c:
            return next(c.decode(video=0)).to_ndarray(format="rgb24").astype(int)

    plain = frame(render_edit(project, edit(project, None), sheets=False).video)
    cube_file(project / "swap.cube", 9, lambda r, gg, b: (b, gg, r))
    graded = frame(render_edit(project, edit(project, {"saturation": 1.3, "lut": "swap.cube"}), sheets=False).video)
    mid = graded[90, 160]
    assert mid[2] > mid[0] + 60  # orange footage, red and blue swapped by the LUT
    assert np.abs(graded[90, 10] - plain[90, 10]).max() <= 2  # the bars keep the theme's background
