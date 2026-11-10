import io

import numpy as np
import pytest
from PIL import Image

from manimvox.scenes import Cutaway, SceneError


@pytest.fixture
def pv():
    return pytest.importorskip("pyvista")


@pytest.fixture
def block(pv):
    """A 20 cube of cells, labelled 1 for x < 10 and 2 beyond, as a volume mesh."""
    g = pv.ImageData(dimensions=(21, 21, 21)).cast_to_unstructured_grid()
    g.cell_data["part"] = np.where(g.cell_centers().points[:, 0] < 10, 1, 2)
    return g


def test_plane_forms(block):
    c = block.center
    assert np.allclose(Cutaway(block, plane="z").n, (0, 0, 1))
    assert np.allclose(Cutaway(block, plane="-x").n, (-1, 0, 0))
    assert np.allclose(Cutaway(block).n, (0, -1, 0))  # the default faces the front of a z-up model
    v = Cutaway(block, plane=(0, 0, 3))
    assert np.allclose(v.n, (0, 0, 1)) and np.allclose(v.origin, c)
    o = Cutaway(block, plane=((1, 2, 3), (0, 2, 0)))
    assert np.allclose(o.origin, (1, 2, 3)) and np.allclose(o.n, (0, 1, 0))
    assert abs(Cutaway(block, plane="z").up @ (0, 0, 1)) < 1e-9  # the picture's up is never along the normal
    with pytest.raises(SceneError, match="plane must be"):
        Cutaway(block, plane="w")


def test_the_cut_removes_the_part_in_front_of_the_plane(block):
    cut = Cutaway(block, plane="z")  # in front is +z
    assert cut.cut().bounds[5] == pytest.approx(10, abs=0.5) and cut.cut().bounds[4] == 0
    assert cut.cut(offset=5).bounds[5] == pytest.approx(15, abs=0.5)  # a positive offset cuts less away


def test_the_section_lies_on_the_plane(block):
    cut = Cutaway(block, plane="z")
    z = cut.section().points[:, 2]
    assert np.allclose(z, z[0]) and 9.9 < z[0] <= 10.5
    assert cut.section(offset=-4).points[:, 2].mean() == pytest.approx(6, abs=0.5)


def test_the_glass_is_the_part_cut_away(block):
    cut = Cutaway(block, plane="z")
    g = cut.glass()
    assert g.bounds[4] == pytest.approx(10, abs=0.5) and g.bounds[5] == 20


def test_regions_colour_by_a_scalar_and_glass_can_pick_regions(pv, block):
    cut = Cutaway(block, regions="part", colours={1: "#ff0000", 2: "#0000ff"}, plane="z", glass_regions=[2])
    assert list(cut.values) == [1, 2] and cut._hues() == ["#ff0000", "#0000ff"]
    assert cut._hues(section=True) == ["#FF5959", "#5959FF"]  # lightened, unless given
    assert Cutaway(block, regions="part", colours=["#111111", "#222222"])._hues() == ["#111111", "#222222"]
    assert len(Cutaway(block, regions="part")._hues()) == 2  # the theme's hues by default
    assert set(np.unique(cut.glass().cell_data["part"])) == {2}
    pl = pv.Plotter(off_screen=True)
    assert len(cut.add(pl)) == 3
    pl.close()
    with pytest.raises(SceneError, match="no array"):
        Cutaway(block, regions="nope")


def test_a_point_scalar_becomes_whole_cell_regions(pv):
    g = pv.ImageData(dimensions=(11, 11, 11))
    g.point_data["tissue"] = (g.points[:, 0] > 5).astype(int)
    cut = Cutaway(g, regions="tissue")
    assert list(cut.values) == [0, 1] and "tissue" in cut.mesh.cell_data


def test_region_centre_is_on_the_cut_face_inside_the_region(block):
    cut = Cutaway(block, regions="part", plane="z")
    p1, p2 = cut.region_centre(1), cut.region_centre(2)
    assert abs(p1[2] - cut.origin[2]) < 0.5 and p1[0] < 10
    assert abs(p2[2] - cut.origin[2]) < 0.5 and p2[0] > 10
    with pytest.raises(SceneError, match="not on the cut face"):
        cut.region_centre(3)
    with pytest.raises(SceneError, match="needs regions"):
        Cutaway(block).region_centre(1)


def test_the_camera_looks_at_the_cut_face_from_the_removed_side(pv, block):
    cut = Cutaway(block, plane="z")
    pl = pv.Plotter(off_screen=True, window_size=[64, 36])
    cut.camera(pl, zoom=1.0)
    assert np.allclose(pl.camera.focal_point, cut.centre)
    to_camera = np.asarray(pl.camera.position) - cut.centre
    assert to_camera @ cut.n > 0 and np.allclose(np.cross(to_camera, cut.n), 0, atol=1e-6)  # in front, on the normal
    cut.camera(pl, turn=90)
    to_camera = np.asarray(pl.camera.position) - cut.centre
    assert abs(to_camera @ cut.n) < 1e-6  # a quarter turn is side on
    pl.close()


def test_screen_maps_a_point_to_the_frame(block):
    cut = Cutaway(block, plane="z")
    assert cut.screen(cut.centre) == pytest.approx((640, 360))  # the focus is the middle of the frame
    right = np.cross(cut.up, cut.n)
    x, y = cut.screen(cut.centre + right * 3)
    assert y == pytest.approx(360) and x != pytest.approx(640)
    assert cut.screen(cut.centre + cut.up * 3)[1] < 360  # up in the scene is up in the frame (smaller y)
    assert cut.screen(cut.centre, size=(100, 50)) == pytest.approx((50, 25))
    with pytest.raises(SceneError, match="behind"):
        cut.screen(cut.centre + cut.n * 1000)


def test_a_closed_surface_is_capped(pv):
    cut = Cutaway(pv.Sphere(radius=5), plane="z")
    face = cut.section()
    assert face.n_cells and np.allclose(face.points[:, 2], 0, atol=1e-5)
    assert cut.cut().bounds[5] <= 1e-5


def test_a_file_loads_and_a_bad_one_says_so(pv, tmp_path):
    path = tmp_path / "ball.stl"
    pv.Sphere().save(str(path))
    assert Cutaway(path).mesh.n_points
    with pytest.raises(SceneError, match="no mesh file"):
        Cutaway(tmp_path / "missing.stl")


@pytest.mark.slow
def test_a_tiny_render_through_from_pyvista(pv, block):
    cut = Cutaway(block, regions="part", plane="z")
    size = (96, 54)
    still = cut.opened(glass=0.3, size=size, fps=2)
    assert len(still.frames) >= 1
    a = np.asarray(Image.open(io.BytesIO(still.frames[0])))
    assert a.shape == (54, 96, 4) and a[27, 48, 3] == 255 and a[0, 0, 3] == 0
    # the plotter-free projection agrees with VTK's own
    from manimvox.scenes import screen_xy

    pl = pv.Plotter(off_screen=True, window_size=list(size))
    cut.camera(pl, zoom=1.3)
    p = cut.centre + np.cross(cut.up, cut.n) * 4 + cut.up * 2
    assert cut.screen(p, zoom=1.3, size=size) == pytest.approx(screen_xy(pl, p), abs=0.5)
    pl.close()
    assert len(cut.turning(seconds=1, fps=2, size=size).frames) == 2
    assert len(cut.sweep(seconds=1, fps=2, size=size).frames) == 2
    assert np.allclose(cut.at(still, cut.centre), still.at(48, 27))


def _two_bodies(pv):
    """Two small balls (region 1, one either side) and a big one between them (region 2), closed, labelled by 'part'."""
    side = pv.Sphere(radius=1.5, center=(-6, 0, 0)).merge(pv.Sphere(radius=1.5, center=(6, 0, 0)))
    mid = pv.Sphere(radius=2.5)
    both = side.extract_surface().merge(mid).extract_surface().triangulate()
    both.cell_data["part"] = np.r_[np.full(side.n_cells, 1), np.full(mid.n_cells, 2)].astype(np.int32)
    return both


def test_a_closed_surface_with_regions_keeps_its_labels_on_the_cut_face(pv):
    cut = Cutaway(_two_bodies(pv), regions="part", plane="y")
    face = cut.section()
    assert set(np.unique(face.cell_data["part"])) == {1, 2}
    assert set(np.unique(cut.cut().cell_data["part"])) <= {1, 2}
    assert np.allclose(face.points[:, 1], 0, atol=1e-5)


def test_region_centre_of_a_split_region_lies_in_one_of_its_pieces(pv):
    p = Cutaway(_two_bodies(pv), regions="part", plane="y").region_centre(1)
    # region 1 is cut in two pieces; the middle between them lies in region 2, so the point must sit in one piece
    assert abs(p[1]) < 1e-5 and abs(abs(p[0]) - 6) < 0.6 and abs(p[2]) < 0.6


def _ramp(pv):
    grid = pv.ImageData(dimensions=(9, 7, 5), spacing=(1, 1, 1))
    grid.point_data["stress"] = np.asarray(grid.points)[:, 0] * 2 + np.asarray(grid.points)[:, 2]
    return grid


def test_a_field_colours_a_volume_by_a_ramp_and_finds_its_peak_on_the_cut(pv):
    cut = Cutaway(_ramp(pv), field="stress", plane=((4, 3, 2), (0, 0, 1)))
    assert cut._clim == (0.0, 20.0)
    hi, lo = cut.extreme(), cut.extreme(highest=False)
    assert hi[0] == 8 and lo[0] == 0 and abs(hi[2] - 2) < 0.01  # on the cut face, at its two ends
    still = cut.opened(size=(96, 54), fps=2)
    a = np.asarray(Image.open(io.BytesIO(still.frames[0])))
    assert a[27, 48, 3] == 255
    left, right = a[27, 30, :3].astype(int), a[27, 66, :3].astype(int)
    assert np.abs(left - right).sum() > 40  # the two ends of the cut face are not one colour


def test_a_field_is_checked(pv):
    with pytest.raises(SceneError, match="no array 'heat'"):
        Cutaway(_ramp(pv), field="heat")
    with pytest.raises(SceneError, match="not both"):
        Cutaway(_ramp(pv), field="stress", regions="stress")
    with pytest.raises(SceneError, match="surface"):
        Cutaway(pv.Sphere(), field="x")
    with pytest.raises(SceneError, match="needs a field"):
        Cutaway(_ramp(pv)).extreme()


# the quarter cut: a 90 degree wedge removed between two planes through an axis

def _balls(pv):
    """A big ball at the origin (region 2) and two small ones (region 1) sitting on the two planes of a quarter cut
    about z that opens towards +x (the planes are x = y and x = -y), closed and labelled by 'part'."""
    small = pv.Sphere(radius=1.0, center=(3, 3, 0)).merge(pv.Sphere(radius=1.0, center=(3, -3, 0)))
    mid = pv.Sphere(radius=2.5)
    both = small.extract_surface().merge(mid).extract_surface().triangulate()
    both.cell_data["part"] = np.r_[np.full(small.n_cells, 1), np.full(mid.n_cells, 2)].astype(np.int32)
    return both


def _inside_wedge(cut, mesh, tol=1e-6):
    n1, n2 = cut._normals(0.0)
    c = np.asarray(mesh.cell_centers().points) - cut.origin
    return (c @ n1 > tol) & (c @ n2 > tol)


def test_the_quarter_cut_is_set_by_an_axis_and_the_way_it_opens(block):
    cut = Cutaway(block, axis="z", towards="x")
    assert cut.quarter and np.allclose(cut.axis, (0, 0, 1)) and np.allclose(cut.n, (1, 0, 0))
    n1, n2 = cut._normals(0.0)
    assert abs(n1 @ n2) < 1e-9 and np.allclose(n1 + n2, np.sqrt(2) * cut.n)  # perpendicular planes, split by the opening
    assert Cutaway(block, axis="z").n @ (0, 0, 1) == pytest.approx(0)  # default opening is up, across the axis
    assert np.allclose(Cutaway(block, axis="z", towards=(1, 0, 5)).n, (1, 0, 0))  # only what is across the axis counts
    assert not Cutaway(block, plane="z").quarter
    assert cut._normals(90.0) is None  # nothing left to cut
    with pytest.raises(SceneError, match="not both"):
        Cutaway(block, axis="z", plane="x")
    with pytest.raises(SceneError, match="towards needs an axis"):
        Cutaway(block, towards="x")
    with pytest.raises(SceneError, match="along the axis"):
        Cutaway(block, axis="z", towards="z")
    with pytest.raises(SceneError, match="axis must be"):
        Cutaway(block, axis="w")



def test_the_wedge_is_removed_from_a_volume_and_a_surface(pv, block):
    vol = Cutaway(block, axis="z", towards="x")
    kept = vol.cut()
    assert kept.n_cells and not _inside_wedge(vol, kept).any()
    assert kept.n_cells < block.n_cells and kept.n_cells > block.n_cells * 0.6  # a quarter gone, not more
    surf = Cutaway(_balls(pv), regions="part", axis="z", towards="x")
    rest = surf.cut()
    assert rest.n_cells and not _inside_wedge(surf, rest).any()
    assert surf.cut(offset=90).n_cells == surf.mesh.n_cells  # offset is the degrees not yet cut: all 90, nothing removed
    assert surf.section(offset=90).n_points == 0


def test_both_cut_faces_lie_on_their_planes_and_carry_the_regions(pv):
    cut = Cutaway(_balls(pv), regions="part", axis="z", towards="x")
    n1, n2 = cut._normals(0.0)
    f0, f1 = cut.section(face=0), cut.section(face=1)
    assert f0.n_cells and f1.n_cells
    assert np.allclose((f0.points - cut.origin) @ n1, 0, atol=1e-5) and np.allclose((f1.points - cut.origin) @ n2, 0, atol=1e-5)
    assert ((f0.points - cut.origin) @ n2 > -1e-5).all() and ((f1.points - cut.origin) @ n1 > -1e-5).all()  # bound the wedge only
    assert set(np.unique(f0.cell_data["part"])) == {1, 2} and set(np.unique(f1.cell_data["part"])) == {1, 2}
    both = cut.section()
    assert both.n_cells == f0.n_cells + f1.n_cells
    assert set(np.unique(cut.cut().cell_data["part"])) == {1, 2}  # the body keeps its labels too
    for face, n in ((0, n1), (1, n2)):
        p = cut.region_centre(1, face=face)
        assert abs((p - cut.origin) @ n) < 1e-5
    with pytest.raises(SceneError, match="face is"):
        cut.section(face=2)
    with pytest.raises(SceneError, match="needs a quarter cut"):
        Cutaway(_balls(pv), plane="z").section(face=0)


def test_a_volume_quarter_has_two_faces_too(block):
    cut = Cutaway(block, axis="z", towards="x")
    n1, n2 = cut._normals(0.0)
    f0, f1 = cut.section(face=0), cut.section(face=1)
    assert f0.n_cells and f1.n_cells
    assert abs(((f0.points - cut.origin) @ n1).mean()) < 0.5 and abs(((f1.points - cut.origin) @ n2).mean()) < 0.5


def test_the_glass_of_a_quarter_is_only_the_wedge(pv):
    cut = Cutaway(_balls(pv), regions="part", axis="z", towards="x")
    g = cut.glass()
    assert g.n_cells and _inside_wedge(cut, g, tol=-1e-6).all()


def test_the_three_quarter_camera_looks_into_the_wedge(pv):
    cut = Cutaway(_balls(pv), axis="z", towards="x")
    n1, n2 = cut._normals(0.0)
    pos, focus = cut.view(turn=30, lift=0.3)
    to_camera = pos - focus
    assert to_camera @ n1 > 0 and to_camera @ n2 > 0  # in front of both cut faces: it sees both
    assert to_camera @ cut.axis != 0  # and off to the side, so the end of the part shows
    pos0, _ = cut.view()
    assert np.allclose(np.cross(pos0 - focus, cut.n), 0, atol=1e-9)  # no turn: straight down the opening
    assert np.allclose(cut.view(aim=(1, 2, 3))[1], (1, 2, 3))  # aim moves what it looks at


def test_the_part_turns_about_its_axis_while_the_camera_stays(pv):
    cut = Cutaway(_balls(pv), axis="z", towards="x")
    pl = pv.Plotter(off_screen=True, window_size=[64, 36])
    cut.camera(pl, turn=30, zoom=1.5, lift=0.3)
    start = np.asarray(pl.camera.position).copy()
    cut._spun(pl, 0, 30, 1.5, 0.3)
    assert np.allclose(pl.camera.position, start)
    cut._spun(pl, 360, 30, 1.5, 0.3)
    assert np.allclose(pl.camera.position, start)  # a full turn is the opened view's own camera
    cut._spun(pl, 90, 30, 1.5, 0.3)
    p = np.asarray(pl.camera.position) - cut.origin
    assert not np.allclose(pl.camera.position, start)
    assert p @ cut.axis == pytest.approx((start - cut.origin) @ cut.axis)  # round the axis, never along it
    assert np.linalg.norm(p - (p @ cut.axis) * cut.axis) == pytest.approx(
        np.linalg.norm((start - cut.origin) - ((start - cut.origin) @ cut.axis) * cut.axis))
    pl.close()


def test_single_plane_cut_is_untouched_by_the_quarter_options(block):
    cut = Cutaway(block, plane="z")
    assert not cut.quarter and cut.axis is None
    assert cut.view(turn=20, lift=0.1)[1].tolist() == list(cut.centre)
    assert cut.cut().bounds[5] == pytest.approx(10, abs=0.5)


@pytest.mark.slow
def test_one_camera_serves_turning_sweep_and_opened_and_labels_map(pv):
    cut = Cutaway(_balls(pv), regions="part", axis="z", towards="x")
    cam = {"turn": 30, "zoom": 1.4, "lift": 0.3}
    size = (96, 54)
    spin = cut.turning(seconds=1, fps=2, size=size, **cam)
    sweep = cut.sweep(seconds=1, fps=2, size=size, **cam)
    still = cut.opened(size=size, fps=2, **cam)
    assert spin.cutaway_view == sweep.cutaway_view == still.cutaway_view
    assert len(spin.frames) == 2 and len(sweep.frames) == 2
    for face in (0, 1):
        p = cut.region_centre(1, face=face)
        x, y = cut.screen(p, size=size, **cam)
        assert 0 <= x <= 96 and 0 <= y <= 54  # on screen in the opened view
        assert np.allclose(cut.at(still, p), still.at(x, y))
    marks = cut.labelled(still, {"a": cut.region_centre(1, face=0), "b": cut.region_centre(2, face=1)})
    assert [name for _, name in marks] == ["a", "b"]
    moved = cut.move(1, {"zoom": 1.0}, {**cam, "aim": cut.region_centre(1, face=0)}, size=size, fps=2)
    assert moved.cutaway_view["zoom"] == 1.4 and len(moved.frames) == 2
    assert np.asarray(Image.open(io.BytesIO(still.frames[0])))[:, :, 3].any()  # something was drawn


def test_a_part_mounted_axle_across_and_up_up_keeps_the_weight_pointing_down_the_picture(pv):
    """A wheel's bearing: axle along x, picture up along z. The axle then runs across the frame, down is down."""
    cut = Cutaway(_balls(pv), axis="x", towards=(0, -1, 0), up=(0, 0, 1))
    c = cut.centre
    for cam in ({}, {"turn": 30, "lift": 0.6}):
        x0, y0 = cut.screen(c, **cam)
        xa, ya = cut.screen(c + cut.axis * 4, **cam)
        xd, yd = cut.screen(c - np.array([0, 0, 1.0]) * 4, **cam)
        assert xa > x0 + 1 and abs(ya - y0) < abs(xa - x0) * 0.8  # the axle runs mostly across the frame
        assert yd > y0 + 1 and abs(xd - x0) < abs(yd - y0)  # down in the world is down in the picture
    n1, n2 = cut._normals(0.0)
    to_camera = cut.view(turn=30, lift=0.6)[0] - c
    assert to_camera @ n1 > 0 and to_camera @ n2 > 0  # and from there it still looks into the opened wedge
