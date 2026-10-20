import base64
import io
import json
import math
import sys

import numpy as np
import pytest
from PIL import Image

from manimvox.scenes import SceneError, from_model


def turning_cube(path, seconds=2.0):
    """A glTF cube with one animation, 'turn': a quarter turn about y over `seconds`."""
    v = np.array([[x, y, z] for x in (-.5, .5) for y in (-.5, .5) for z in (-.5, .5)], np.float32)
    f = np.array([0, 1, 3, 0, 3, 2, 4, 6, 7, 4, 7, 5, 0, 4, 5, 0, 5, 1,
                  2, 3, 7, 2, 7, 6, 0, 2, 6, 0, 6, 4, 1, 5, 7, 1, 7, 3], np.uint16)
    t = np.array([0, seconds], np.float32)
    q = np.array([[0, 0, 0, 1], [0, math.sin(math.pi / 4), 0, math.cos(math.pi / 4)]], np.float32)
    parts = [v, f, t, q]
    blob = b"".join(p.tobytes() for p in parts)
    offsets = np.cumsum([0] + [p.nbytes for p in parts[:-1]])
    gltf = {
        "asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "material": 0}]}],
        "materials": [{"pbrMetallicRoughness": {"baseColorFactor": [0.9, 0.4, 0.2, 1]}}],
        "buffers": [{"byteLength": len(blob),
                     "uri": "data:application/octet-stream;base64," + base64.b64encode(blob).decode()}],
        "bufferViews": [{"buffer": 0, "byteOffset": int(o), "byteLength": p.nbytes} for o, p in zip(offsets, parts)],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 8, "type": "VEC3", "min": [-.5] * 3, "max": [.5] * 3},
            {"bufferView": 1, "componentType": 5123, "count": 36, "type": "SCALAR"},
            {"bufferView": 2, "componentType": 5126, "count": 2, "type": "SCALAR", "min": [0], "max": [seconds]},
            {"bufferView": 3, "componentType": 5126, "count": 2, "type": "VEC4"}],
        "animations": [{"name": "turn", "channels": [{"sampler": 0, "target": {"node": 0, "path": "rotation"}}],
                        "samplers": [{"input": 2, "output": 3, "interpolation": "LINEAR"}]}],
    }
    path.write_text(json.dumps(gltf), encoding="utf-8")
    return path


@pytest.fixture
def pv():
    return pytest.importorskip("pyvista")


def frame(clip, i):
    return np.asarray(Image.open(io.BytesIO(clip.frames[i])))


def test_a_model_renders_on_a_transparent_background(pv, tmp_path):
    clip = from_model(turning_cube(tmp_path / "cube.gltf"), seconds=1, fps=4, size=(96, 54), orbit=0)
    assert len(clip.frames) == 4 and clip.fps == 4
    a = frame(clip, 0)
    assert a.shape == (54, 96, 4)
    assert a[0, 0, 3] == 0 and a[27, 48, 3] == 255  # corner clear, middle covered by the cube


def test_the_camera_orbits(pv, tmp_path):
    path = turning_cube(tmp_path / "cube.gltf")
    still = from_model(path, seconds=1, fps=4, size=(96, 54), orbit=0, animation=None)
    turning = from_model(path, seconds=1, fps=4, size=(96, 54), orbit=40, animation=None)
    assert len(set(still.frames)) == 1
    assert len(set(turning.frames)) == 4


def test_the_animation_plays_by_time_and_holds_its_last_pose(pv, tmp_path):
    path = turning_cube(tmp_path / "cube.gltf", seconds=1.0)
    clip = from_model(path, seconds=2, fps=4, size=(96, 54), orbit=0, animation="turn")
    assert clip.frames[0] != clip.frames[1]  # turning
    assert clip.frames[4] == clip.frames[5] == clip.frames[7]  # done after 1 s: it holds
    again = from_model(path, seconds=2, fps=4, size=(96, 54), orbit=0, animation=0)
    assert again.frames == clip.frames  # the same input gives the same frames


def test_a_looping_animation_starts_again(pv, tmp_path):
    path = turning_cube(tmp_path / "cube.gltf", seconds=1.0)
    clip = from_model(path, seconds=2, fps=4, size=(96, 54), orbit=0, loop=True)
    assert clip.frames[1] == clip.frames[5]  # 0.25 s and 1.25 s


def test_an_unknown_animation_is_named(pv, tmp_path):
    path = turning_cube(tmp_path / "cube.gltf")
    with pytest.raises(SceneError, match="has no animation 'walk'; it has turn"):
        from_model(path, seconds=1, fps=2, size=(32, 18), animation="walk")
    with pytest.raises(SceneError, match="animation must be 0 to 0"):
        from_model(path, seconds=1, fps=2, size=(32, 18), animation=3)


def test_a_mesh_file_takes_the_colour_given(pv, tmp_path):
    trimesh = pytest.importorskip("trimesh")
    path = tmp_path / "box.stl"
    trimesh.creation.box((1, 1, 1)).export(path)
    clip = from_model(path, seconds=0.5, fps=2, size=(96, 54), orbit=0, elevation=0, up="z", color="#00ff00")
    r, g, b, a = frame(clip, 0)[27, 48]
    assert a == 255 and g > r and g > b


@pytest.mark.parametrize("name, kwargs, match", [
    ("nope.glb", {}, "no model file"),
    ("model.fbx", {}, "not a model format"),
    ("cube.gltf", {"up": "x"}, "up must"),
    ("cube.gltf", {"zoom": 0}, "zoom must"),
])
def test_bad_input_is_refused(tmp_path, name, kwargs, match):
    turning_cube(tmp_path / "cube.gltf")
    (tmp_path / "model.fbx").write_bytes(b"")
    with pytest.raises(SceneError, match=match):
        from_model(tmp_path / name, seconds=1, fps=2, **kwargs)


def test_missing_pyvista_names_the_extra(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "pyvista", None)
    with pytest.raises(SceneError, match=r"manimvox\[kokoro,pyvista\]"):
        from_model(turning_cube(tmp_path / "cube.gltf"), seconds=1, fps=2)


def test_a_full_orbit_loops_without_repeating_a_frame(pv, tmp_path):
    path = turning_cube(tmp_path / "cube.gltf")
    clip = from_model(path, seconds=1, fps=5, size=(96, 54), orbit=360, azimuth=10, animation=None)  # 72° steps
    after = from_model(path, seconds=0.2, fps=5, size=(96, 54), orbit=0, azimuth=370, animation=None)
    assert len(set(clip.frames)) == 5 and after.frames[0] == clip.frames[0]  # the frame after the last is the first


def test_from_pyvista_draws_each_frame_from_its_time(pv):
    from manimvox.scenes import from_pyvista

    seen = []

    def setup(pl):
        pl.add_mesh(pv.Sphere(radius=0.5), color="#ffffff")

    def draw(pl, t):
        seen.append(t)
        pl.camera.position = (0, 0, 3 + t * 4)  # moving away: the sphere shrinks
        pl.camera.focal_point, pl.camera.up = (0, 0, 0), (0, 1, 0)

    clip = from_pyvista(draw, seconds=1, fps=2, size=(64, 36), setup=setup)
    assert seen == [0.0, 0.5] and len(clip.frames) == 2
    covered = [int((frame(clip, i)[..., 3] > 0).sum()) for i in range(2)]
    assert covered[0] > covered[1] > 0


def test_screen_xy_finds_a_point_in_the_frame(pv):
    from manimvox.scenes import from_pyvista, screen_xy

    where = {}

    def draw(pl, t):
        pl.camera.position, pl.camera.focal_point, pl.camera.up = (0, 0, 5), (0, 0, 0), (0, 1, 0)
        where["centre"], where["up"] = screen_xy(pl, (0, 0, 0)), screen_xy(pl, (0, 1, 0))

    from_pyvista(draw, seconds=0.5, fps=2, size=(64, 36), setup=lambda pl: pl.add_mesh(pv.Sphere()))
    assert where["centre"] == pytest.approx((32, 18), abs=0.6)
    assert where["up"][1] < where["centre"][1]  # up in the world is up the picture: a smaller y
