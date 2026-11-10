"""manimvox's own lighting for mesh-model faces: the maths, the lit camera, and one tiny render."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from manim import DEGREES

from manimvox.blocks import add_block
from manimvox.kit import Lighting, LitCamera
from manimvox.kit.shading import shade_colors, shade_factors

REG = Path(__file__).resolve().parents[1] / "blocks"
FRONT = np.eye(3)  # a camera looking straight down z: view space is scene space


def rot(phi, theta):
    cam = LitCamera()
    cam.set_phi(phi)
    cam.set_theta(theta)
    cam.reset_rotation_matrix()  # the scene does this before each frame
    return cam.get_rotation_matrix()


def test_a_face_never_exceeds_its_base_colour_times_the_cap():
    rng = np.random.default_rng(1)
    n = rng.normal(size=(500, 3))
    base = rng.random((500, 3))
    for cap in (1.0, 0.8):
        out = shade_colors(base, n, rot(1.0, -2.0), Lighting(cap=cap, ambient=0.9, rim=1.0))
        assert (out <= base * cap + 1e-12).all() and (out >= 0).all()


def test_hue_is_kept_nothing_washes_to_white():
    base = np.array([[0.8, 0.2, 0.1]] * 3)
    out = shade_colors(base, np.array([[0, 0, 1.0], [1.0, 0, 0], [0, -1.0, 0]]), FRONT, Lighting())
    assert np.allclose(out / out[:, :1], base / base[:, :1])  # same ratios, only scaled down


def test_faces_towards_the_light_are_brighter_than_faces_away():
    lighting = Lighting(light=(-1, 1, 1))
    towards = np.array([[-1, 1, 1.0]])
    away = np.array([[1, -1, 0.1]])
    k_to = shade_factors(towards, FRONT, lighting)[0]
    k_away = shade_factors(away, FRONT, lighting)[0]
    assert k_to == pytest.approx(1.0) and k_away < k_to
    assert k_away >= lighting.ambient  # ambient is the floor


def test_faces_are_two_sided():
    n = np.array([[0.3, 0.2, 1.0]])
    assert shade_factors(n, FRONT, Lighting()) == pytest.approx(shade_factors(-n, FRONT, Lighting()))


def test_shading_follows_the_camera_and_is_deterministic():
    n = np.array([[1.0, 0.2, 0.3], [0.0, 1.0, 0.5], [0.3, -0.4, 0.8]])
    lighting = Lighting()
    a = shade_factors(n, rot(60 * DEGREES, -50 * DEGREES), lighting)
    b = shade_factors(n, rot(60 * DEGREES, 40 * DEGREES), lighting)
    assert not np.allclose(a, b)
    assert np.array_equal(a, shade_factors(n, rot(60 * DEGREES, -50 * DEGREES), lighting))


def _block(tmp_path, monkeypatch):
    import importlib

    add_block(tmp_path, "mesh-model", root=REG)
    monkeypatch.syspath_prepend(str(tmp_path))
    for mod in [m for m in sys.modules if m == "blocks" or m.startswith("blocks.")]:
        monkeypatch.delitem(sys.modules, mod)
    return importlib.import_module("blocks.mesh_model")


TETRA = (np.array([[0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2]], float),
         np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]]))


def test_lit_is_the_default_and_manim_keeps_the_old_faces(tmp_path, monkeypatch):
    mm = _block(tmp_path, monkeypatch)
    lit = mm.mesh_model(TETRA, up="z")
    assert all(f.lighting == Lighting() and f.shade_in_3d for f in lit)  # shade_in_3d still makes the camera sort
    old = mm.mesh_model(TETRA, up="z", shading="manim")
    assert all(not hasattr(f, "lighting") and f.shade_in_3d for f in old)
    custom = mm.mesh_model(TETRA, up="z", light=(1, 0, 1), ambient=0.3)
    assert custom[0].lighting.light == (1.0, 0.0, 1.0) and custom[0].lighting.ambient == 0.3


@pytest.mark.parametrize("kwargs, match", [({"shading": "phong"}, "shading must"), ({"ambient": 2}, "ambient"),
                                           ({"light": (0, 0, 0)}, "light must")])
def test_bad_lighting_options_are_refused(tmp_path, monkeypatch, kwargs, match):
    mm = _block(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match=match):
        mm.mesh_model(TETRA, up="z", **kwargs)


def test_the_lit_camera_sorts_by_depth_and_leaves_other_mobjects_alone(tmp_path, monkeypatch):
    from manim import Dot

    mm = _block(tmp_path, monkeypatch)
    model = mm.mesh_model(TETRA, up="z")
    cam = LitCamera()
    cam.set_phi(70 * DEGREES)
    cam.set_theta(-30 * DEGREES)
    cam.reset_rotation_matrix()
    pin = Dot()
    shown = cam.get_mobjects_to_display([pin, *model.submobjects])
    assert shown[-1] is pin  # non-3D mobjects draw last, as in Manim
    depth = [(np.dot(f.points[0:9:4].mean(axis=0), cam.get_rotation_matrix().T))[2] for f in shown[:-1]]
    assert depth == sorted(depth)


@pytest.mark.slow
def test_a_lit_model_renders_and_keeps_its_colour(tmp_path):
    from manimvox.project import load_project
    from manimvox.runner import render_episode
    from manimvox.scaffold import new_project

    root = new_project(tmp_path / "p", series="Lit", voice="fake:tone")
    add_block(root, "mesh-model", root=REG)
    (root / "episodes" / "ep01_demo.py").write_text('''
import numpy as np
from manimvox.kit import *
from blocks.mesh_model import mesh_model

class Demo(Episode3D):
    def build(self):
        v = np.array([[0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2]], float)
        f = np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]])
        self.set_camera_orientation(phi=60 * DEGREES, theta=-50 * DEGREES)
        self.add(mesh_model((v, f, "#cc2222"), size=3, up="z"))
        self.begin_ambient_camera_rotation(rate=0.5)
        self.wait(1)
''', encoding="utf-8")
    conf = json.loads((root / "series.json").read_text(encoding="utf-8"))
    conf["episodes"] = [{"n": 1, "stem": "ep01_demo", "cls": "Demo", "title": "lit"}]
    (root / "series.json").write_text(json.dumps(conf), encoding="utf-8")
    pr = load_project(root)
    mp4 = render_episode(pr, pr.episode("ep01_demo"), "draft", None)
    import av

    with av.open(str(mp4)) as c:
        frame = next(c.decode(video=0)).to_ndarray(format="rgb24").astype(int)
    red = frame[(frame[:, :, 0] > 80) & (frame[:, :, 0] > 2 * frame[:, :, 1])]
    assert len(red) > 500  # the model is drawn
    assert (red[:, 0] <= 0xCC + 6).all()  # never brighter than its own colour
