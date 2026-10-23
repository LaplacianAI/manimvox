"""Prepare the CT heart for the episode: the walls (labels 1-10) as one volume, and the landmarks.

Download case 18 of Rodero et al. 2021 (CC BY 4.0, https://zenodo.org/records/4590294), unpack 18.vtk, then:

    python prep_ct.py path/to/18.vtk research/ct

It writes research/ct/walls.vtu and research/ct/points.json, which blocks/heart_ct.py reads.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pyvista as pv

# the dataset's element labels used here (see the Zenodo record for all 24)
LANDMARKS = {
    "lv": (1,), "rv": (2,), "la": (3,), "ra": (4,), "aorta": (5,), "pa": (6,),
    "mitral": (7,), "tricuspid": (8,), "aortic_valve": (9,), "pulmonary_valve": (10,),
    "lspv": (12,), "lipv": (13,), "ripv": (14,), "rspv": (15,), "svc": (16,), "ivc": (17,),
}


def apex(grid, ids, label, quantile):
    """The tip of a ventricle: its points lowest on the dataset's apex-to-base coordinate."""
    part = grid.extract_cells(np.where(ids == label)[0])
    z = np.asarray(part.point_data["Z.dat"])
    return np.asarray(part.points)[z <= np.quantile(z, quantile)].mean(axis=0)


def main(src: str, out: str) -> None:
    grid = pv.read(src)
    ids = np.asarray(grid.cell_data["ID"])
    for name in ("fibres", "sheets"):
        del grid.cell_data[name]
    centres = grid.cell_centers().points
    points = {name: centres[np.isin(ids, labels)].mean(axis=0).tolist() for name, labels in LANDMARKS.items()}
    points["apex"] = apex(grid, ids, 1, 0.002).tolist()
    points["rv_apex"] = apex(grid, ids, 2, 0.01).tolist()
    Path(out).mkdir(parents=True, exist_ok=True)
    grid.extract_cells(np.where(ids <= 10)[0]).save(Path(out) / "walls.vtu")
    (Path(out) / "points.json").write_text(json.dumps(points, indent=1), encoding="utf-8")
    print(f"wrote {out}/walls.vtu and {out}/points.json")


if __name__ == "__main__":
    main(*sys.argv[1:3])
