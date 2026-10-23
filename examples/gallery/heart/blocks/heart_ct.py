"""The CT heart (Rodero et al. 2021, CC BY 4.0): its walls, key points and four-chamber cut, rendered with PyVista."""
import json
from pathlib import Path

import numpy as np

CT = Path(__file__).resolve().parents[1] / "research" / "ct"
MUSCLE, AORTA, PULMONARY, VALVE, SECTION = "#B8453E", "#D8655C", "#6F8FD8", "#F2D38A", "#E58C7E"
# labels 1-4 chamber walls, 5 aorta, 6 pulmonary artery, 7-10 valve planes
LABEL_COLOURS = [MUSCLE] * 4 + [AORTA, PULMONARY] + [VALVE] * 4
SECTION_COLOURS = [SECTION] * 4 + ["#F0A096", "#A9BEEB"] + [VALVE] * 4


def unit(v):
    return v / np.linalg.norm(v)


class Heart:
    def __init__(self):
        import pyvista as pv

        self.walls = pv.read(CT / "walls.vtu")
        self.p = {k: np.array(v) for k, v in json.loads((CT / "points.json").read_text()).items()}
        p = self.p
        n = unit(np.cross(p["mitral"] - p["apex"], p["tricuspid"] - p["apex"]))
        up = (p["mitral"] + p["tricuspid"]) / 2 - p["apex"]
        up = unit(up - up.dot(n) * n)
        if np.cross(-n, up).dot(p["la"] - p["ra"]) < 0:  # face it from the front: the right atrium on the left
            n = -n
        self.n, self.up = n, up  # n points from the cut plane to the camera
        self.origin = (p["apex"] + p["mitral"] + p["tricuspid"]) / 3
        self.centre = np.asarray(self.walls.center)
        self.outside = self.walls.extract_surface(algorithm="dataset_surface")
        self.radius = self.walls.length / 2

    def add(self, pl, mesh, colours=LABEL_COLOURS, **kw):
        return pl.add_mesh(mesh, scalars="ID", cmap=colours, clim=[0.5, 10.5], n_colors=10,
                           show_scalar_bar=False, smooth_shading=True, specular=0.25, **kw)

    def cut(self, offset=0.0):
        """The walls with the front removed down to `offset` (scene mm) in front of the four-chamber plane."""
        return self.walls.clip(normal=self.n, origin=self.origin + self.n * offset)

    def septum(self):
        """A point in the middle of the wall between the ventricles, on the cut."""
        w = self.walls
        phi, z, rho = (np.asarray(w.point_data[k]) for k in ("PHI.dat", "Z.dat", "RHO.dat"))
        near = np.abs((np.asarray(w.points) - self.origin) @ self.n) < 2.0
        pick = near & (np.abs(phi) < 0.15) & (z > 0.45) & (z < 0.6) & (rho > 0.3) & (rho < 0.7)
        return np.asarray(w.points)[pick].mean(axis=0)

    def section(self, offset=0.0):
        """The cut face itself: the slice through the walls at `offset`, a hair in front so it shows."""
        return self.walls.slice(normal=self.n, origin=self.origin + self.n * (offset + 0.05))

    def front(self, offset=0.0):
        """The outside of the part cut away, to show as glass."""
        vessels = self.outside.threshold([4.5, 6.5], scalars="ID")  # the aorta and the pulmonary artery
        return vessels.clip(normal=-self.n, origin=self.origin + self.n * offset)

    def add_cut(self, pl, offset=0.0, glass=0.3):
        """The heart cut open at `offset`: the back half, its cut face, and the great arteries in front as glass."""
        actors = [self.add(pl, self.cut(offset))]
        sec = self.section(offset)
        if sec.n_points:
            actors.append(self.add(pl, sec, colours=SECTION_COLOURS, ambient=0.35, diffuse=0.7))
        if glass:
            front = self.front(offset)
            if front.n_points:
                actors.append(self.add(pl, front, opacity=glass))
        return actors

    def camera(self, pl, turn=0.0, zoom=1.0, lift=0.0):
        """Look at the four-chamber plane from the front, turned `turn` degrees about the long axis."""
        a = np.radians(turn)
        side = np.cross(self.up, self.n)
        view = np.cos(a) * self.n + np.sin(a) * side
        view = unit(view + self.up * lift)
        dist = self.radius / np.sin(np.radians(pl.camera.view_angle) / 2) / zoom
        pl.camera.focal_point = self.centre
        pl.camera.position = self.centre + view * dist
        pl.camera.up = self.up
