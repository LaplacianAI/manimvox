"""A cut-away view of any 3D mesh: a volume (a CT scan, a simulation) or a closed surface (a CAD part) opened along a
plane, its regions coloured, the cut face shown, the removed part as glass, and the points to label.

`Cutaway` holds the geometry; its clip makers (`turning`, `sweep`, `opened`) return clips through `from_pyvista`,
and `at` maps a 3D point to a scene point on the opened clip for `leaders`. Needs the pyvista extra."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from .charts import SERIES_ROLES, _need, _theme
from .clip import DEFAULT_WIDTH, Clip, SceneError
from .model import from_pyvista

AXES = {"x": (1.0, 0.0, 0.0), "y": (0.0, 1.0, 0.0), "z": (0.0, 0.0, 1.0)}
VIEW_ANGLE = 30.0  # VTK's default vertical angle; the camera keeps it, so a point can be projected without a plotter
SIZE = (1280, 720)
FACE = 0.35  # how far towards white the cut face is drawn, unless `section_colours` says otherwise
REGION = "_cutaway_region"
QUARTER = 90.0  # the wedge a quarter cut removes, in degrees


def _unit(v) -> np.ndarray:
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    if not n > 0:
        raise SceneError("cutaway: a direction cannot be the zero vector")
    return v / n


def _lighten(colour: str, k: float = FACE) -> str:
    c = colour.lstrip("#")
    rgb = [int(c[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(v + (255 - v) * k):02X}" for v in rgb)


class Cutaway:
    """`source` (a PyVista dataset, or a file PyVista reads: .vtk, .vtu, .stl, .obj, .ply, ...) cut along a plane.

    `regions` names a cell or point array that labels the parts (a material id, a tissue label); None draws one
    colour. `colours` is a dict {region value: colour} or a list in the order of the sorted region values,
    default the theme's hues. `section_colours` does the same for the cut face, default the colours lightened.
    `glass_regions` lists the region values drawn as glass once cut away (default all of them: a heavy interior
    would hide the cut, so list only the outer parts).

    `field` instead names a continuous point or cell array of a volume (stress, temperature), drawn as a colour
    ramp, `cmap` a list of colours low to high (default theme blue to orange) and `clim` its (low, high) range
    (default the array's); the cut face shows the field inside. `extreme` finds where it peaks on a cut.

    `plane` is where to cut, and the front is the side the camera looks from:
    "x", "y" or "z" (the plane through the centre, facing along that axis; "-y" faces the other way),
    a normal vector (through the centre), or (origin, normal). Default "-y": the front of a z-up model.
    `up` is the picture's up (default z, or y for a plane facing along z). `cut(offset)` and friends take
    `offset` in the mesh's units, in front of the plane: 0 is the plane, a positive offset cuts less away.

    `axis` instead makes a quarter cut, the engineering-drawing way to show a round part: a 90 degree wedge is
    removed between two perpendicular planes through the part's axis, so the outside and the inside show
    together, and both cut faces are capped and coloured by region. `axis` is "x", "y" or "z" (through the
    centre), a direction, or (origin, direction); `towards` is the direction, across the axis, the wedge
    opens to (default up, z). The camera looks from there: `turn` swings it toward the axis so the end of the
    part shows, `lift` raises it along `up` (default the direction across both). In a quarter cut `offset` is
    in degrees: how much of the 90 is not yet cut away, so `sweep` opens the wedge from 90 to 0.

    `ghost` is {region value: opacity}: those regions of the body are drawn see-through (the cut face stays solid),
    so what hides behind an outer shell, such as the rollers inside a bearing's outer ring, shows."""

    def __init__(self, source, regions: str | None = None, colours=None, plane=None, up=None,
                 section_colours=None, glass_regions=None, field=None, cmap=None, clim=None, axis=None, towards=None,
                 ghost=None):
        pv = _need("pyvista", "pyvista")
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.is_file():
                raise SceneError(f"cutaway: no mesh file at {path}")
            try:
                source = pv.read(str(path))
            except Exception as e:  # VTK's readers raise several types
                raise SceneError(f"cutaway: cannot read {path} as a mesh: {e}") from e
        if not isinstance(source, pv.DataSet):
            source = pv.wrap(source)
        if not source.n_points:
            raise SceneError("cutaway: the mesh holds no geometry")
        self.mesh = source.copy()
        self.regions = regions
        self.values = None
        if regions is not None:
            if regions not in self.mesh.cell_data:
                if regions not in self.mesh.point_data:
                    have = sorted(set(self.mesh.cell_data) | set(self.mesh.point_data))
                    raise SceneError(f"cutaway: the mesh has no array {regions!r}; it has {', '.join(have) or 'none'}")
                # a cell takes the label of the point nearest its middle: labels are never blended
                near = cKDTree(self.mesh.points).query(self.mesh.cell_centers().points)[1]
                self.mesh.cell_data[regions] = np.asarray(self.mesh.point_data[regions])[near]
            labels = np.asarray(self.mesh.cell_data[regions])
            self.values = np.unique(labels)
            self.mesh.cell_data[REGION] = np.searchsorted(self.values, labels).astype(np.int32)
        self.field, self._cmap, self._clim = field, cmap, clim
        if field is not None:
            if regions is not None:
                raise SceneError("cutaway: colour by regions or by field, not both")
            if self.mesh.GetClassName() == "vtkPolyData":
                raise SceneError("cutaway: field colours a volume's cut face; a surface has no inside to show it")
            if field not in self.mesh.point_data and field not in self.mesh.cell_data:
                have = sorted(set(self.mesh.cell_data) | set(self.mesh.point_data))
                raise SceneError(f"cutaway: the mesh has no array {field!r}; it has {', '.join(have) or 'none'}")
            if self._clim is None:
                data = self.mesh.point_data if field in self.mesh.point_data else self.mesh.cell_data
                self._clim = (float(np.min(data[field])), float(np.max(data[field])))
        self.centre = np.asarray(self.mesh.center, float)
        self.radius = self.mesh.length / 2
        self.quarter = axis is not None
        self.axis = self.e = None
        if self.quarter:
            if plane is not None:
                raise SceneError("cutaway: cut along a plane or a quarter about an axis, not both")
            self.origin, self.axis = self._axis(axis)
            self.n = self._towards(towards)  # the way the wedge opens, and the way the camera looks from
            self.e = np.cross(self.axis, self.n)
            if up is None:
                up = self.e
        else:
            if towards is not None:
                raise SceneError("cutaway: towards needs an axis (a quarter cut)")
            self.origin, self.n = self._plane(plane)
        z = np.array(AXES["y"] if abs(self.n[2]) > 0.99 else AXES["z"]) if up is None else np.asarray(up, float)
        self.up = _unit(z - z.dot(self.n) * self.n)  # the picture's up, across the normal
        self._colours, self._section_colours, self._glass = colours, section_colours, glass_regions
        self._ghost = dict(ghost) if ghost else {}
        self.outside = self.mesh.extract_surface(algorithm="dataset_surface") if not isinstance(
            self.mesh, pv.PolyData) else self.mesh
        self._capped: dict[float, tuple] = {}

    # the plane and what it cuts

    def _plane(self, plane):
        if plane is None:
            plane = "-y"
        if isinstance(plane, str):
            axis = plane.lstrip("-")
            if axis not in AXES:
                raise SceneError(f"cutaway: plane must be 'x', 'y', 'z' (or with a '-'), a normal, or (origin, normal); "
                                 f"got {plane!r}")
            return self.centre, _unit(AXES[axis]) * (-1 if plane.startswith("-") else 1)
        if len(plane) == 2 and np.ndim(plane[0]) == 1:
            return np.asarray(plane[0], float), _unit(plane[1])
        if np.shape(plane) == (3,):
            return self.centre, _unit(plane)
        raise SceneError(f"cutaway: plane must be 'x', 'y', 'z', a normal, or (origin, normal); got {plane!r}")

    def _axis(self, axis):
        if isinstance(axis, str):
            if axis.lstrip("-") not in AXES:
                raise SceneError(f"cutaway: axis must be 'x', 'y', 'z', a direction, or (origin, direction); got {axis!r}")
            return self.centre, _unit(AXES[axis.lstrip("-")]) * (-1 if axis.startswith("-") else 1)
        if len(axis) == 2 and np.ndim(axis[0]) == 1:
            return np.asarray(axis[0], float), _unit(axis[1])
        if np.shape(axis) == (3,):
            return self.centre, _unit(axis)
        raise SceneError(f"cutaway: axis must be 'x', 'y', 'z', a direction, or (origin, direction); got {axis!r}")

    def _towards(self, towards) -> np.ndarray:
        if towards is None:
            towards = AXES["y"] if abs(self.axis[2]) > 0.99 else AXES["z"]
        elif isinstance(towards, str):
            if towards.lstrip("-") not in AXES:
                raise SceneError(f"cutaway: towards must be 'x', 'y', 'z' (or with a '-') or a direction; got {towards!r}")
            towards = np.asarray(AXES[towards.lstrip("-")]) * (-1 if towards.startswith("-") else 1)
        t = np.asarray(towards, float)
        t = t - t.dot(self.axis) * self.axis
        if np.linalg.norm(t) < 1e-9:
            raise SceneError("cutaway: towards cannot run along the axis")
        return _unit(t)

    def _normals(self, offset: float):
        """The two plane normals of the wedge left to remove at `offset` (the removed part is in front of both),
        or None when none is left. Face 0 lies on the +e side of the opening, face 1 on the -e side."""
        w = min(180.0, QUARTER - offset)
        if w < 1e-3:
            return None
        h = math.radians(w / 2)
        return math.sin(h) * self.n - math.cos(h) * self.e, math.sin(h) * self.n + math.cos(h) * self.e

    def _at(self, offset: float) -> np.ndarray:
        return self.origin + self.n * offset

    def _is_surface(self) -> bool:
        return self.mesh.GetClassName() == "vtkPolyData"

    def _split(self, offset: float):
        """A closed surface cut and capped: (the rest, the cap), or None when the surface cannot be capped."""
        if not self._is_surface():
            return None
        key = round(float(offset), 9)
        if key not in self._capped:
            try:
                self._capped[key] = self._cap_wedge(offset) if self.quarter else self._cap(self._at(offset))
            except Exception:  # noqa: BLE001 - VTK raises several types; an open surface has no inside to cap
                self._capped[key] = None
        return self._capped[key]

    def _cap(self, origin):
        """(the rest, the cap) of the closed surface cut at `origin`. VTK's cap drops the cell arrays, so with
        regions each region is cut and capped on its own and keeps its label."""
        pv = _need("pyvista", "pyvista")
        tol = 1e-6 * max(1.0, self.radius)
        if self.values is None:
            wholes = [(self.mesh, None)]
        else:
            ids = np.asarray(self.mesh.cell_data[REGION])
            wholes = [(self.mesh.extract_cells(np.where(ids == k)[0]).extract_surface(algorithm="dataset_surface"), k)
                      for k in range(len(self.values))]
        rest, caps = [], []
        for part, k in wholes:
            capped = part.clip_closed_surface(normal=-self.n, origin=origin)
            if not capped.n_cells:
                continue
            if k is not None:
                capped.cell_data[REGION] = np.full(capped.n_cells, k, np.int32)
                capped.cell_data[self.regions] = np.full(capped.n_cells, self.values[k])
            on = np.abs((capped.cell_centers().points - origin) @ self.n) < tol
            if (~on).any():
                rest.append(capped.extract_cells(~on).extract_surface(algorithm="dataset_surface"))
            if on.any():
                caps.append(capped.extract_cells(on).extract_surface(algorithm="dataset_surface"))
        if not caps:
            return None

        def join(parts):
            return parts[0] if len(parts) == 1 else parts[0].merge(parts[1:]).extract_surface(algorithm="dataset_surface")

        return join(rest) if rest else pv.PolyData(), join(caps)

    def _cap_wedge(self, offset: float):
        """(the rest, both cut faces joined, [face 0, face 1]) of a closed surface with the quarter wedge removed.
        The rest is the part behind the first plane, and what is behind the second of the part in front of the first;
        each cap is kept only where it bounds the wedge, so no face is drawn inside the solid."""
        pv = _need("pyvista", "pyvista")
        normals = self._normals(offset)
        if normals is None:
            return self.mesh.extract_surface(algorithm="dataset_surface") if not self._is_surface() else self.mesh, \
                pv.PolyData(), [pv.PolyData(), pv.PolyData()]
        n1, n2 = normals
        o = self.origin
        tol = 1e-6 * max(1.0, self.radius)
        if self.values is None:
            wholes = [(self.mesh, None)]
        else:
            ids = np.asarray(self.mesh.cell_data[REGION])
            wholes = [(self.mesh.extract_cells(np.where(ids == k)[0]).extract_surface(algorithm="dataset_surface"), k)
                      for k in range(len(self.values))]

        def label(piece, k):
            if k is not None and piece.n_cells:
                piece.cell_data[REGION] = np.full(piece.n_cells, k, np.int32)
                piece.cell_data[self.regions] = np.full(piece.n_cells, self.values[k])
            return piece

        def on(piece, n):
            return np.abs((piece.cell_centers().points - o) @ n) < tol

        def sub(piece, mask):
            return piece.extract_cells(mask).extract_surface(algorithm="dataset_surface") if mask.any() else None

        rest, face0, face1 = [], [], []
        for part, k in wholes:
            behind2 = part.clip_closed_surface(normal=-n2, origin=o)  # all of it behind the second plane
            if behind2.n_cells:
                on2 = on(behind2, n2)
                rest.append((sub(behind2, ~on2), k))
                cap = sub(behind2, on2)  # kept where it is in front of the first plane: the second cut face
                if cap is not None:
                    cap = cap.clip(normal=-n1, origin=o)
                    if cap.n_cells:
                        face1.append(label(cap, k))
            front2 = part.clip_closed_surface(normal=n2, origin=o)
            if not front2.n_cells:
                continue
            rest_of = front2.clip_closed_surface(normal=-n1, origin=o)  # in front of the second, behind the first
            if not rest_of.n_cells:
                continue
            on1, on2 = on(rest_of, n1), on(rest_of, n2)
            rest.append((sub(rest_of, ~(on1 | on2)), k))
            cap = sub(rest_of, on1 & ~on2)  # the first cut face; the face on the second plane is inside the solid
            if cap is not None:
                face0.append(label(cap, k))
        rest = [label(r, k) for r, k in rest if r is not None]
        if not (face0 or face1):
            return None

        def join(parts):
            parts = [p for p in parts if p is not None and p.n_cells]
            if not parts:
                return pv.PolyData()
            return parts[0] if len(parts) == 1 else parts[0].merge(parts[1:]).extract_surface(algorithm="dataset_surface")

        faces = [join(face0), join(face1)]
        return join(rest), join([f for f in faces if f.n_cells]), faces

    def _cut_open(self, offset: float):
        """The mesh (a volume, or a surface that cannot be capped) with the quarter wedge removed."""
        normals = self._normals(offset)
        if normals is None:
            return self.mesh
        n1, n2 = normals
        o = self.origin
        parts = [self.mesh.clip(normal=n1, origin=o), self.mesh.clip(normal=-n1, origin=o).clip(normal=n2, origin=o)]
        parts = [p for p in parts if p.n_points]
        if not parts:
            return self.mesh.clip(normal=n1, origin=o)
        return parts[0] if len(parts) == 1 else parts[0].merge(parts[1:])

    def _faces_open(self, offset: float):
        """The two cut faces of a volume as slices, a hair in front so they show."""
        normals = self._normals(offset)
        if normals is None:
            return None
        n1, n2 = normals
        o, hair = self.origin, 5e-4 * self.radius * 2
        f0 = self.mesh.slice(normal=n1, origin=o + n1 * hair).clip(normal=-n2, origin=o)  # on plane 1, in front of 2
        f1 = self.mesh.slice(normal=n2, origin=o + n2 * hair).clip(normal=-n1, origin=o)
        return f0, f1

    def cut(self, offset: float = 0.0):
        """The mesh with everything in front of the plane at `offset` removed (a quarter cut: the wedge, `offset`
        degrees short of 90)."""
        split = self._split(offset)
        if split:
            return split[0]
        if self.quarter:
            return self._cut_open(offset)
        return self.mesh.clip(normal=self.n, origin=self._at(offset))

    def section(self, offset: float = 0.0, face: int | None = None):
        """The cut face itself: the slice through the mesh (for a closed surface, its cap), a hair in front so it shows.
        A quarter cut has two faces: `face` 0 or 1 picks one (0 on the +e side of the opening, 1 on the other), None
        joins them."""
        if face not in (None, 0, 1):
            raise SceneError("cutaway: face is 0, 1 or None")
        if face is not None and not self.quarter:
            raise SceneError("cutaway: face needs a quarter cut (axis=)")
        split = self._split(offset)
        if split:
            return split[2][face] if face is not None else split[1]
        if self.quarter:
            both = self._faces_open(offset)
            if both is None:
                return _need("pyvista", "pyvista").PolyData()
            if face is not None:
                return both[face]
            parts = [f for f in both if f.n_points]
            return parts[0].merge(parts[1:]) if len(parts) > 1 else parts[0] if parts else both[0]
        return self.mesh.slice(normal=self.n, origin=self._at(offset + 5e-4 * self.radius * 2))

    def glass(self, offset: float = 0.0):
        """The part cut away, outside only (the surface in front of the plane, or inside the wedge), to draw translucent."""
        out = self.outside
        if self._glass is not None and self.regions is not None:
            keep = np.isin(np.asarray(out.cell_data[self.regions]), np.atleast_1d(self._glass))
            out = out.extract_cells(keep)
        if self.quarter:
            normals = self._normals(offset)
            if normals is None or not out.n_points:
                return _need("pyvista", "pyvista").PolyData()
            n1, n2 = normals
            return out.clip(normal=-n1, origin=self.origin).clip(normal=-n2, origin=self.origin)
        return out.clip(normal=-self.n, origin=self._at(offset)) if out.n_points else out

    # drawing

    def _resolve(self, given, fallback: list[str]) -> list[str]:
        """One colour per region (one in all for no regions) from a dict, a list or a string, else `fallback`."""
        if self.values is None:
            return [given if isinstance(given, str) else fallback[0]]
        out = []
        for i, v in enumerate(self.values):
            if isinstance(given, dict):
                c = given.get(v.item())
            else:
                c = given[i] if given is not None and not isinstance(given, str) and i < len(given) else None
            out.append(c or fallback[i])
        return out

    def _hues(self, section: bool = False) -> list[str]:
        """The colour of each region in order (the one colour of a mesh with no regions), for the body or the face."""
        th = _theme(None)
        n = 1 if self.values is None else len(self.values)
        theme = [th[SERIES_ROLES[i % len(SERIES_ROLES)]] for i in range(n)]
        body = self._resolve(self._colours, theme)
        if not section:
            return body
        return self._resolve(self._section_colours, [_lighten(c) for c in body])

    def _show(self, pl, mesh, section=False, **kw):
        if self.field is not None:
            th = _theme(None)
            return pl.add_mesh(mesh, scalars=self.field, cmap=self._cmap or [th["blue"], th["orange"]],
                               clim=list(self._clim), show_scalar_bar=False, smooth_shading=True, specular=0.25, **kw)
        hues = self._hues(section)
        if self.values is None:
            return pl.add_mesh(mesh, color=hues[0], smooth_shading=True, specular=0.25, **kw)
        return pl.add_mesh(mesh, scalars=REGION, cmap=hues, clim=[-0.5, len(hues) - 0.5], n_colors=len(hues),
                           show_scalar_bar=False, smooth_shading=True, specular=0.25, **kw)

    def _body(self, pl, body) -> list:
        """The cut body, its `ghost` regions drawn see-through."""
        if not self._ghost or self.regions is None:
            return [self._show(pl, body)]
        labels = np.asarray(body.cell_data[REGION])
        ids = {int(np.searchsorted(self.values, v)): o for v, o in self._ghost.items() if v in self.values}
        solid = ~np.isin(labels, list(ids))
        actors = [self._show(pl, body.extract_cells(np.where(solid)[0]))] if solid.any() else []
        for k, opacity in ids.items():
            if (labels == k).any():
                actors.append(self._show(pl, body.extract_cells(np.where(labels == k)[0]), opacity=opacity))
        return actors

    def add(self, pl, offset: float = 0.0, glass: float = 0.3, mesh=None):
        """Put the cut mesh, its cut face and the glass (opacity `glass`, 0 for none) in the plotter `pl`.
        Returns the actors, to remove before drawing another cut. `mesh` draws that mesh in the regions'
        colours instead (for the whole object, pass `cut.outside`)."""
        if mesh is not None:
            return [self._show(pl, mesh)]
        actors = []
        body = self.cut(offset)
        if body.n_points:
            actors.extend(self._body(pl, body))
        face = self.section(offset)
        if face.n_points and face.n_cells:
            actors.append(self._show(pl, face, section=True, ambient=0.35, diffuse=0.7))
        if glass:
            front = self.glass(offset)
            if front.n_points:
                actors.append(self._show(pl, front, opacity=glass))
        return actors

    # the camera

    def view(self, turn: float = 0.0, zoom: float = 1.0, lift: float = 0.0, aim=None) -> tuple[np.ndarray, np.ndarray]:
        """The camera's (position, focal point): in front of the cut face, turned `turn` degrees about the up
        axis and raised by `lift` (about 0.3 tilts it a little from above). `aim` is the 3D point to look at
        (default the middle of the object): with `zoom` it closes in on one place."""
        a = math.radians(turn)
        side = np.cross(self.up, self.n)
        view = _unit(math.cos(a) * self.n + math.sin(a) * side + self.up * lift)
        dist = self.radius / math.sin(math.radians(VIEW_ANGLE) / 2) / zoom
        focus = self.centre if aim is None else np.asarray(aim, float)
        return focus + view * dist, focus

    def camera(self, pl, turn: float = 0.0, zoom: float = 1.0, lift: float = 0.0, aim=None) -> None:
        """Look at the cut face from the front (the side the cut removed), turned `turn` degrees about the up
        axis, `zoom` above 1 closer, `lift` raising the camera, `aim` the point looked at."""
        pos, focus = self.view(turn, zoom, lift, aim)
        pl.camera.view_angle = VIEW_ANGLE
        pl.camera.focal_point = focus
        pl.camera.position = pos
        pl.camera.up = self.up

    # clips

    def _spun(self, pl, degrees: float, turn: float, zoom: float, lift: float, aim=None) -> None:
        """The camera of `camera`, carried `degrees` about the part's axis: the part turns while the view stays."""
        pos, focus = self.view(turn, zoom, lift, aim)
        k, a, o = self.axis, math.radians(degrees), self.origin

        def rot(v):
            return v * math.cos(a) + np.cross(k, v) * math.sin(a) + k * (k @ v) * (1 - math.cos(a))

        pl.camera.view_angle = VIEW_ANGLE
        pl.camera.focal_point = o + rot(focus - o)
        pl.camera.position = o + rot(pos - o)
        pl.camera.up = rot(self.up)

    def _remember(self, clip: Clip, turn: float, zoom: float, lift: float, size, aim=None) -> Clip:
        clip.cutaway_view = {"turn": turn, "zoom": zoom, "lift": lift, "size": tuple(size), "aim": aim}
        return clip

    def turning(self, seconds: float = 9, turns: float = 1, zoom: float = 1.0, lift: float = 0.0, fps: float = 15,
                size: tuple[int, int] = SIZE, width: float = DEFAULT_WIDTH, turn: float = 0.0, aim=None) -> Clip:
        """The whole object, uncut, turning `turns` times (1 loops without a repeated frame). A plane cut turns the
        camera about the up axis, starting at `turn` degrees. A quarter cut turns the part about its own axis while
        the camera stays at the `turn`, `zoom` and `lift` you also give `sweep` and `opened`, so the view never changes."""
        if self.quarter:
            clip = from_pyvista(lambda pl, t: self._spun(pl, 360 * turns * t / seconds, turn, zoom, lift, aim),
                                seconds, fps, size, width, setup=lambda pl: self.add(pl, mesh=self.outside))
            return self._remember(clip, turn, zoom, lift, size, aim)
        return from_pyvista(lambda pl, t: self.camera(pl, turn=turn + 360 * turns * t / seconds, zoom=zoom, lift=lift, aim=aim),
                            seconds, fps, size, width, setup=lambda pl: self.add(pl, mesh=self.outside))

    def sweep(self, seconds: float = 2.4, zoom: float = 1.0, lift: float = 0.0, glass: float = 0.0, hold: float = 0.2,
              fps: float = 15, size: tuple[int, int] = SIZE, width: float = DEFAULT_WIDTH, turn: float = 0.0,
              aim=None) -> Clip:
        """The cut sweeping from in front of the object to the plane, easing in, then holding `hold` seconds. A quarter
        cut opens the wedge from nothing to 90 degrees instead. The camera stays where `turn`, `zoom` and `lift` put it."""
        from manim.utils.rate_functions import smooth

        shown: list = []
        span = max(seconds - hold, 1e-6)
        start = QUARTER if self.quarter else self.radius

        def draw(pl, t):
            for a in shown:
                pl.remove_actor(a)
            shown.clear()
            shown.extend(self.add(pl, offset=start * (1 - smooth(min(1.0, t / span))), glass=glass))
            self.camera(pl, turn=turn, zoom=zoom, lift=lift, aim=aim)

        return self._remember(from_pyvista(draw, seconds, fps, size, width), turn, zoom, lift, size, aim)

    def opened(self, glass: float = 0.3, offset: float = 0.0, turn: float = 0.0, zoom: float = 1.0, lift: float = 0.0,
               fps: float = 15, size: tuple[int, int] = SIZE, width: float = DEFAULT_WIDTH, aim=None) -> Clip:
        """A still of the object opened at `offset`, to label with `at`. Remembers its camera for `at`."""
        clip = from_pyvista(lambda pl, t: self.camera(pl, turn=turn, zoom=zoom, lift=lift, aim=aim), 1 / fps, fps, size,
                            width, setup=lambda pl: self.add(pl, offset=offset, glass=glass))
        return self._remember(clip, turn, zoom, lift, size, aim)

    def move(self, seconds: float, start: dict, end: dict, glass: float = 0.3, offset: float = 0.0, fps: float = 15,
             size: tuple[int, int] = SIZE, width: float = DEFAULT_WIDTH) -> Clip:
        """The opened object while the camera glides from `start` to `end` (each a dict of `turn`, `zoom`, `lift`,
        `aim`; a missing key is the default), easing in and out: a push in on one part, or a swing round. The clip
        remembers `end`, so `at` and `labelled` work on it once it has played."""
        from manim.utils.rate_functions import smooth

        a = {"turn": 0.0, "zoom": 1.0, "lift": 0.0, "aim": self.centre, **start}
        b = {"turn": 0.0, "zoom": 1.0, "lift": 0.0, "aim": self.centre, **end}
        a["aim"], b["aim"] = np.asarray(a["aim"], float), np.asarray(b["aim"], float)

        def draw(pl, t):
            k = smooth(min(1.0, t / max(seconds - 1 / fps, 1e-6)))
            self.camera(pl, turn=a["turn"] + (b["turn"] - a["turn"]) * k,
                        zoom=math.exp(math.log(a["zoom"]) + (math.log(b["zoom"]) - math.log(a["zoom"])) * k),
                        lift=a["lift"] + (b["lift"] - a["lift"]) * k, aim=a["aim"] + (b["aim"] - a["aim"]) * k)

        clip = from_pyvista(draw, seconds, fps, size, width, setup=lambda pl: self.add(pl, offset=offset, glass=glass))
        return self._remember(clip, b["turn"], b["zoom"], b["lift"], size, b["aim"])

    def colour(self, colours=None, section_colours=None, ghost=None) -> Cutaway:
        """Change the regions' colours for the clips made after this (clips are drawn when made): one colour for the
        part the narration is on, greys for the rest. Pass None to leave one as it was; `ghost` is {} for none.
        Returns self."""
        if colours is not None:
            self._colours = colours
        if section_colours is not None:
            self._section_colours = section_colours
        if ghost is not None:
            self._ghost = dict(ghost)
        return self

    # points to label

    def screen(self, point, turn: float = 0.0, zoom: float = 1.0, lift: float = 0.0,
               size: tuple[int, int] = SIZE, aim=None) -> tuple[float, float]:
        """Where the 3D `point` shows in a frame made with this camera, in pixels from the top left: the
        position `screen_xy` gives inside `draw`, worked out without a plotter."""
        pos, focus = self.view(turn, zoom, lift, aim)
        f = _unit(focus - pos)
        r = _unit(np.cross(f, self.up))
        u = np.cross(r, f)
        d = np.asarray(point, float) - pos
        depth = d @ f
        if not depth > 0:
            raise SceneError("cutaway: the point is behind the camera")
        half = depth * math.tan(math.radians(VIEW_ANGLE) / 2)
        w, h = size
        return (1 + (d @ r) / (half * w / h)) / 2 * w, (1 - (d @ u) / half) / 2 * h

    def at(self, clip: Clip, point) -> np.ndarray:
        """The scene point over the 3D `point` on a clip from `opened`, to pass to `leaders` or `stream`."""
        view = getattr(clip, "cutaway_view", None)
        if view is None:
            raise SceneError("cutaway: at() needs a clip made by opened()")
        return clip.at(*self.screen(point, **view))

    def labelled(self, clip: Clip, names: dict) -> list[tuple[np.ndarray, str]]:
        """`leaders` targets for {name: 3D point}: `leaders(cut.labelled(clip, {"Core": p, ...}), side="right")`."""
        return [(self.at(clip, p), name) for name, p in names.items()]

    def region_centre(self, value, offset: float = 0.0, face: int | None = None) -> np.ndarray:
        """A point of region `value` on the cut face at `offset`, nearest the middle of its largest piece there.
        A quarter cut has two faces: `face` 0 or 1 looks on that one only."""
        if self.regions is None:
            raise SceneError("cutaway: region_centre needs regions (the name of a labelling array)")
        which, face = face, self.section(offset, face=face)
        if not (face.n_points and face.n_cells):
            raise SceneError(f"cutaway: the cut at offset {offset:g} has no face" + (f" {which}" if which is not None else ""))
        mask = np.asarray(face.cell_data[self.regions]) == value
        if not mask.any():
            raise SceneError(f"cutaway: region {value!r} is not on the cut face; the face has "
                             f"{', '.join(str(v) for v in np.unique(face.cell_data[self.regions]))}")
        piece = face.extract_cells(np.where(mask)[0]).extract_surface(algorithm="dataset_surface")
        if piece.n_cells > 1:  # a region cut in two pieces (a ring) has its middle between them: take the biggest piece
            pieces = piece.connectivity("all")
            ids = np.asarray(pieces.cell_data["RegionId"])
            area = np.bincount(ids, weights=np.asarray(pieces.compute_cell_sizes(length=False, volume=False)
                                                       .cell_data["Area"]))
            piece = pieces.extract_cells(np.where(ids == np.argmax(area))[0]).extract_surface(algorithm="dataset_surface")
        sized = piece.compute_cell_sizes(length=False, volume=False)
        centres = piece.cell_centers().points
        area = np.asarray(sized.cell_data["Area"])
        mean = (centres * area[:, None]).sum(axis=0) / max(area.sum(), 1e-12)
        return centres[np.argmin(np.linalg.norm(centres - mean, axis=1))]

    def extreme(self, offset: float = 0.0, highest: bool = True) -> np.ndarray:
        """The point on the cut face at `offset` where the `field` is highest (or lowest), to label with `at`."""
        if self.field is None:
            raise SceneError("cutaway: extreme needs a field (the name of a continuous array)")
        face = self.section(offset)
        if not (face.n_points and face.n_cells):
            raise SceneError(f"cutaway: the cut at offset {offset:g} has no face")
        if self.field in face.point_data:
            values, points = np.asarray(face.point_data[self.field]), face.points
        else:
            values, points = np.asarray(face.cell_data[self.field]), face.cell_centers().points
        return points[np.argmax(values) if highest else np.argmin(values)]
