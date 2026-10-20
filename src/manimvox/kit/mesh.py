"""3D models as triangles: a glTF, GLB, OBJ, STL or PLY file, or arrays, read into a Mesh the episode can draw."""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..voice.base import install_hint

MAX_FACES = 5000  # Cairo draws and depth-sorts every face on every frame
UP = {  # the file's up axis onto Manim's z, keeping the model right-handed
    "y": np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float),  # glTF, OBJ, and Blender's glTF export
    "z": np.eye(3),  # STL and many CAD tools
}


@dataclass(frozen=True)
class Mesh:
    """Triangles with Manim's z up: `vertices` (n, 3), `faces` (m, 3) indices into them, and per face its
    `colors` as #RRGGBB (None when the source has none) and the name of the `parts` it came from."""

    vertices: np.ndarray
    faces: np.ndarray
    colors: tuple[str, ...] | None
    parts: tuple[str, ...]


def _need(module: str):
    try:
        return importlib.import_module(module)
    except ImportError as e:
        raise ImportError(f"{module} is not installed; add the trimesh extra: {install_hint('trimesh')}") from e


def _hex(rgb) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(int(c) for c in rgb[:3]))


def _from_file(path: Path):
    """Each geometry of the file with its node's transform applied: (vertices, faces, colours or None, part)."""
    trimesh = _need("trimesh")
    try:
        scene = trimesh.load(str(path), force="scene")
    except Exception as e:  # trimesh raises many types for a file it cannot parse
        raise ValueError(f"cannot read {path} as a 3D model: {e}") from e
    pieces = []
    for node in scene.graph.nodes_geometry:
        transform, name = scene.graph[node]
        geom = scene.geometry[name]
        if not hasattr(geom, "faces") or not len(geom.faces):
            continue  # points and lines have no faces to draw
        geom = geom.copy()
        geom.apply_transform(transform)
        visual = geom.visual
        if visual.kind == "texture":
            visual = visual.to_color()  # samples the texture at each vertex
        colors = None if visual.kind is None else np.asarray(visual.face_colors)[:, :3]
        pieces.append((np.asarray(geom.vertices, float), np.asarray(geom.faces), colors, str(node)))
    if not pieces:
        raise ValueError(f"{path} holds no triangles")
    return pieces


def _from_arrays(source):
    if not isinstance(source, (tuple, list)) or len(source) not in (2, 3):
        raise ValueError("a mesh is a file path, or (vertices, faces) or (vertices, faces, colors) arrays")
    v = np.asarray(source[0], float)
    f = np.asarray(source[1])
    if v.ndim != 2 or v.shape[1] != 3 or f.ndim != 2 or f.shape[1] != 3 or not len(f):
        raise ValueError(f"vertices must be (n, 3) and faces (m, 3) with m > 0, got {v.shape} and {f.shape}")
    if not np.issubdtype(f.dtype, np.integer) or f.min() < 0 or f.max() >= len(v):
        raise ValueError("faces must be integer indices into the vertices")
    if not np.isfinite(v).all():
        raise ValueError("vertices must be finite")
    colors = None
    if len(source) == 3:
        from manim import ManimColor

        colors = list(source[2]) if not isinstance(source[2], str) else [source[2]] * len(f)
        if len(colors) != len(f):
            raise ValueError(f"colors must give one colour per face: {len(colors)} for {len(f)} faces")
        colors = np.array([(-1, -1, -1) if c is None else ManimColor(c).to_int_rgb() for c in colors])
    return [(v, f, colors, "mesh")]


def _nearest(points: np.ndarray, to: np.ndarray) -> np.ndarray:
    """For each of `points`, the index of the nearest of `to` (brute force, a few rows at a time)."""
    out = np.empty(len(points), int)
    for i in range(0, len(points), 32):
        d = ((points[i:i + 32, None, :] - to[None, :, :]) ** 2).sum(axis=2)
        out[i:i + 32] = d.argmin(axis=1)
    return out


def _decimate(v, f, max_faces):
    """At most `max_faces` triangles of the same shape (quadric decimation)."""
    fs = _need("fast_simplification")
    v2, f2 = fs.simplify(v.astype(np.float32), f.astype(np.int32), target_count=max_faces)
    if len(f2) > max_faces:  # the simplifier stops near the target, sometimes just above it
        v2, f2 = fs.simplify(v2, f2, target_count=int(max_faces * 0.9))
    return np.asarray(v2, float), np.asarray(f2)


def load_mesh(source, max_faces: int = 1500, up: str = "y") -> Mesh:
    """Read a 3D model: a .glb, .gltf, .obj, .stl or .ply file (export Blender scenes as glTF), or
    (vertices, faces) arrays with optional per-face colours. `up` names the source's up axis, "y" (glTF,
    OBJ) or "z" (STL, CAD); it becomes Manim's z, which points up once the camera tilts.
    A model with more than `max_faces` triangles (at most 5000) is simplified to that many.
    Files and simplifying need the trimesh extra. Raises ValueError for input it cannot draw."""
    if up not in UP:
        raise ValueError(f"up must be 'y' or 'z', got {up!r}")
    if not 4 <= max_faces <= MAX_FACES:
        raise ValueError(f"max_faces must be from 4 to {MAX_FACES}, got {max_faces}")
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.is_file():
            raise ValueError(f"no model file at {path}")
        pieces = _from_file(path)
    else:
        pieces = _from_arrays(source)
    v = np.concatenate([p[0] for p in pieces])
    offsets = np.cumsum([0] + [len(p[0]) for p in pieces[:-1]])
    f = np.concatenate([p[1] + o for p, o in zip(pieces, offsets)])
    coloured = any(p[2] is not None for p in pieces)
    rgb = np.concatenate([p[2] if p[2] is not None else np.full((len(p[1]), 3), -1) for p in pieces])
    part = np.concatenate([np.full(len(p[1]), i) for i, p in enumerate(pieces)])
    if len(f) > max_faces:
        centres = v[f].mean(axis=1)
        v, f = _decimate(v, f, max_faces)
        # decimation drops colours and parts: each new face takes them from the nearest old face
        sample = np.random.default_rng(0).permutation(len(centres))[:50_000]
        near = sample[_nearest(v[f].mean(axis=1), centres[sample])]
        rgb, part = rgb[near], part[near]
    names = [p[3] for p in pieces]
    colors = tuple(_hex(c) if c[0] >= 0 else None for c in rgb) if coloured else None
    return Mesh(v @ UP[up].T, np.asarray(f, int), colors, tuple(names[i] for i in part))
