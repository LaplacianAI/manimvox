"""The CT heart (Rodero et al. 2021, CC BY 4.0): its walls and key points, cut open along the four-chamber plane."""
import json
from pathlib import Path

import numpy as np

from manimvox.scenes import Cutaway

CT = Path(__file__).resolve().parents[1] / "research" / "ct"
MUSCLE, AORTA, PULMONARY, VALVE, SECTION = "#B8453E", "#D8655C", "#6F8FD8", "#F2D38A", "#E58C7E"
# labels 1-4 chamber walls, 5 aorta, 6 pulmonary artery, 7-10 valve planes
LABEL_COLOURS = [MUSCLE] * 4 + [AORTA, PULMONARY] + [VALVE] * 4
SECTION_COLOURS = [SECTION] * 4 + ["#F0A096", "#A9BEEB"] + [VALVE] * 4


class Heart(Cutaway):
    def __init__(self):
        import pyvista as pv

        walls = pv.read(CT / "walls.vtu")
        self.p = {k: np.array(v) for k, v in json.loads((CT / "points.json").read_text()).items()}
        p = self.p
        n = np.cross(p["mitral"] - p["apex"], p["tricuspid"] - p["apex"])
        up = (p["mitral"] + p["tricuspid"]) / 2 - p["apex"]
        if np.cross(-n, up - up.dot(n) / n.dot(n) * n).dot(p["la"] - p["ra"]) < 0:  # right atrium on the left
            n = -n
        super().__init__(walls, regions="ID", colours=LABEL_COLOURS, section_colours=SECTION_COLOURS,
                         glass_regions=[5, 6],  # the aorta and the pulmonary artery
                         plane=((p["apex"] + p["mitral"] + p["tricuspid"]) / 3, n), up=up)

    def septum(self):
        """A point in the middle of the wall between the ventricles, on the cut."""
        w = self.mesh
        phi, z, rho = (np.asarray(w.point_data[k]) for k in ("PHI.dat", "Z.dat", "RHO.dat"))
        near = np.abs((np.asarray(w.points) - self.origin) @ self.n) < 2.0
        pick = near & (np.abs(phi) < 0.15) & (z > 0.45) & (z < 0.6) & (rho > 0.3) & (rho < 0.7)
        return np.asarray(w.points)[pick].mean(axis=0)
