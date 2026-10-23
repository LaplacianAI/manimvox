import sys

import numpy as np
import pytest

from manimvox.kit import load_mesh

TRI = (np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]]), np.array([[0, 1, 2]]))


def box_file(tmp_path, name="part.glb"):
    trimesh = pytest.importorskip("trimesh")
    a = trimesh.creation.box((1, 1, 1))
    a.visual.face_colors = [255, 0, 0, 255]
    b = trimesh.creation.box((1, 1, 1))
    b.apply_translation((3, 0, 0))
    b.visual.face_colors = [0, 0, 255, 255]
    path = tmp_path / name
    trimesh.Scene({"red": a, "blue": b}).export(path)
    return path


def test_arrays_load_with_z_up_unchanged():
    m = load_mesh(TRI, up="z")
    assert m.vertices.tolist() == [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
    assert m.faces.tolist() == [[0, 1, 2]] and m.colors is None and m.parts == ("mesh",)


def test_y_up_becomes_manims_z_and_stays_right_handed():
    m = load_mesh(TRI, up="y")
    assert m.vertices[2].tolist() == [0, 0, 1]  # the source's up is z now
    a, b, c = m.vertices
    assert np.cross(b - a, c - a).tolist() == [0, -1, 0]  # the face still faces the source's front, +z in glTF


def test_array_colours_one_per_face_or_one_for_all():
    assert load_mesh((*TRI, ["#ff8800"])).colors == ("#ff8800",)
    assert load_mesh((*TRI, "#00ff00")).colors == ("#00ff00",)
    with pytest.raises(ValueError, match="one colour per face"):
        load_mesh((*TRI, ["#ff8800", "#000000"]))


@pytest.mark.parametrize("source, match", [
    ((np.zeros((3, 2)), [[0, 1, 2]]), "vertices must be"),
    ((np.zeros((3, 3)), [[0, 1, 3]]), "indices"),
    ((np.zeros((3, 3)), np.zeros((0, 3), int)), "m > 0"),
    ((np.full((3, 3), np.nan), [[0, 1, 2]]), "finite"),
    (42, "file path"),
])
def test_arrays_it_cannot_draw_are_refused(source, match):
    with pytest.raises(ValueError, match=match):
        load_mesh(source)


@pytest.mark.parametrize("kwargs, match", [({"up": "x"}, "up must"), ({"max_faces": 3}, "max_faces"),
                                           ({"max_faces": 6000}, "max_faces")])
def test_bad_options_are_refused(kwargs, match):
    with pytest.raises(ValueError, match=match):
        load_mesh(TRI, **kwargs)


def test_a_missing_file_is_named(tmp_path):
    with pytest.raises(ValueError, match="no model file"):
        load_mesh(tmp_path / "nope.glb")


def test_a_gltf_file_keeps_its_parts_and_colours(tmp_path):
    m = load_mesh(box_file(tmp_path))
    assert len(m.faces) == 24 and set(m.parts) == {"red", "blue"}
    by_part = {p: {c for c, q in zip(m.colors, m.parts) if q == p} for p in m.parts}
    assert by_part == {"red": {"#ff0000"}, "blue": {"#0000ff"}}
    blue = m.vertices[m.faces[[p == "blue" for p in m.parts]].ravel()]
    assert blue[:, 0].min() == pytest.approx(2.5)  # each node's transform is applied


def test_a_file_that_is_not_a_model_is_refused(tmp_path):
    pytest.importorskip("trimesh")
    bad = tmp_path / "bad.glb"
    bad.write_bytes(b"not a model")
    with pytest.raises(ValueError, match="cannot read"):
        load_mesh(bad)


def test_a_big_model_is_simplified_and_keeps_its_colours(tmp_path):
    trimesh = pytest.importorskip("trimesh")
    pytest.importorskip("fast_simplification")
    s = trimesh.creation.icosphere(subdivisions=4)  # 5120 faces
    s.visual.face_colors = [0, 200, 0, 255]
    path = tmp_path / "ball.glb"
    s.export(path)
    m = load_mesh(path, max_faces=500)
    assert 0 < len(m.faces) <= 500
    assert set(m.colors) == {"#00c800"}
    assert np.abs(m.vertices).max() == pytest.approx(1.0, abs=0.05)  # same shape, fewer faces


def test_missing_trimesh_names_the_extra(tmp_path, monkeypatch):
    path = tmp_path / "x.glb"
    path.write_bytes(b"")
    monkeypatch.setitem(sys.modules, "trimesh", None)
    with pytest.raises(ImportError, match=r"manimvox\[kokoro,trimesh\]"):
        load_mesh(path)
