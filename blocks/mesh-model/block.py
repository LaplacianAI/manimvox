"""A 3D model from a glTF, OBJ or STL file (or arrays) as shaded faces the 3D camera can orbit. For an Episode3D."""
import numpy as np

from manimvox.kit import *


def mesh_model(source, size=4.0, color=ACCENT, max_faces=1500, up="y", wire=False):
    """The model in `source` (a .glb, .gltf, .obj, .stl or .ply file, or (vertices, faces) arrays) as one
    flat-shaded triangle per face, centred on the origin and scaled so its largest side is `size` scene
    units. Faces take the model's own colours; faces without one, and models without any, are `color`.
    `up` is the source's up axis: "y" for glTF and OBJ (Blender's glTF export), "z" for STL and CAD.
    Models over `max_faces` triangles (at most 5000) are simplified first: each face costs render time.
    `wire` draws every face's edges in the background colour, for a low-poly look.
    Draw it in an Episode3D: the camera sorts the faces by depth as it moves. Reveal it with FadeIn (Create
    draws every edge, slowly). Returns a VGroup of the faces with .mesh, .parts (the names of its parts)
    and .centres (each face's centre in scene units from the model's middle, before you move it).
    Files need the trimesh extra. Raises ValueError for a file or arrays it cannot draw."""
    mesh = load_mesh(source, max_faces=max_faces, up=up)
    lo, hi = mesh.vertices.min(axis=0), mesh.vertices.max(axis=0)
    span = float((hi - lo).max())
    if span <= 0:
        raise ValueError("the model has no size: every vertex is at one point")
    pts = (mesh.vertices - (lo + hi) / 2) * (size / span)
    faces = VGroup()
    for i, tri in enumerate(mesh.faces):
        c = (mesh.colors and mesh.colors[i]) or color
        # a stroke of the face's own colour closes the hairline gaps antialiasing leaves between faces
        stroke = (BG, 0.6) if wire else (c, 0.8)
        faces.add(Polygon(*pts[tri], fill_color=c, fill_opacity=1, stroke_color=stroke[0],
                          stroke_width=stroke[1], shade_in_3d=True))
    faces.mesh, faces.parts = mesh, tuple(sorted(set(mesh.parts)))
    faces.centres = pts[mesh.faces].mean(axis=1)
    return faces


def mesh_part(model, name=None, inside=None):
    """The faces of `model` in a part whose name contains `name` (any case; see model.parts), and/or whose
    centre (x, y, z), in scene units from the model's middle before it moved, makes `inside(x, y, z)` true.
    Returns a VGroup of those faces, which stay on the model: recolour them, or place a label by them.
    Raises ValueError when no face matches."""
    keep = np.ones(len(model.submobjects), bool)
    if name is not None:
        keep &= np.array([name.lower() in p.lower() for p in model.mesh.parts])
    if inside is not None:
        keep &= np.array([bool(inside(*c)) for c in model.centres])
    if not keep.any():
        raise ValueError(f"no face matches name={name!r} and inside; the parts are {', '.join(model.parts)}")
    return VGroup(*[f for f, k in zip(model.submobjects, keep) if k])
