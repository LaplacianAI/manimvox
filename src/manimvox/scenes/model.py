"""A 3D model rendered with real lighting and materials (PyVista, on VTK) as a Clip, the camera orbiting it.

Each frame is drawn from its own time: the camera angle and the model's animation are set for t, then
the frame is rendered. Nothing runs on a clock, so a draft and a final render show the same frames."""
from __future__ import annotations

import math
from pathlib import Path

from .charts import _need, _theme
from .clip import DEFAULT_WIDTH, Clip, SceneError, png
from .raster import frame_count

GLTF = {".glb", ".gltf"}
OTHER = {".obj", ".stl", ".ply", ".vtk", ".vtp"}  # read as one mesh, coloured by `color`
VIEW_UP = {"y": (0, 1, 0), "z": (0, 0, 1)}


def _load(pl, path: Path, color: str, animation):
    """Put the model in the plotter. Returns the glTF importer and the animation's (start, end), or Nones."""
    pv = _need("pyvista", "pyvista")
    if path.suffix.lower() not in GLTF:
        try:
            mesh = pv.read(str(path))
        except Exception as e:  # VTK's readers raise several types
            raise SceneError(f"cannot read {path} as a 3D model: {e}") from e
        if not mesh.n_points:
            raise SceneError(f"{path} holds no geometry")
        pl.add_mesh(mesh, color=color, smooth_shading=True, specular=0.3)
        return None, None
    from vtkmodules.vtkCommonCore import reference, vtkDoubleArray
    from vtkmodules.vtkIOImport import vtkGLTFImporter

    imp = vtkGLTFImporter()
    imp.SetFileName(str(path))
    imp.SetRenderWindow(pl.render_window)
    imp.Update()
    if pl.renderer.GetActors().GetNumberOfItems() == 0:
        raise SceneError(f"cannot read {path} as a 3D model, or it holds no meshes")
    n = imp.GetNumberOfAnimations()
    if animation is None or n == 0:
        return imp, None
    if isinstance(animation, str):
        names = [imp.GetAnimationName(i) for i in range(n)]
        if animation not in names:
            raise SceneError(f"{path} has no animation {animation!r}; it has {', '.join(names)}")
        animation = names.index(animation)
    if not 0 <= animation < n:
        raise SceneError(f"{path} has {n} animation(s); animation must be 0 to {n - 1}, got {animation}")
    imp.EnableAnimation(animation)
    steps, span = reference(0), [0.0, 0.0]
    try:
        imp.GetTemporalInformation(animation, span, steps, vtkDoubleArray())  # VTK 9.6 and later
    except TypeError:
        imp.GetTemporalInformation(animation, 30, steps, span, vtkDoubleArray())
    return imp, (span[0], span[1])


def screen_xy(plotter, point) -> tuple[float, float]:
    """Where the 3D `point` shows in the plotter's frame, in pixels from the top left: give it to
    `clip.at(x, y)` to place a label or a path on the rendered picture. Call it inside `draw`, after the
    camera is set for that frame."""
    ren = plotter.renderer
    ren.SetWorldPoint(*point, 1.0)
    ren.WorldToDisplay()
    x, y, _ = ren.GetDisplayPoint()
    return x, plotter.window_size[1] - y


def from_pyvista(draw, seconds: float, fps: float = 15, size: tuple[int, int] = (1280, 720),
                 width: float = DEFAULT_WIDTH, setup=None) -> Clip:
    """Frames of a PyVista scene on a transparent background: `setup(plotter)` once (add meshes, lights),
    then `draw(plotter, t)` before each frame at t seconds (move the camera, swap a clipped mesh, recolour).
    Set the camera's position, focal_point and up in `draw`: PyVista's default up is z.
    The same plotter serves every frame, so meshes added in setup stay. Needs the pyvista extra and OpenGL."""
    n = frame_count(seconds, fps)
    pv = _need("pyvista", "pyvista")
    pl = pv.Plotter(off_screen=True, window_size=list(size))
    try:
        pl.set_background(_theme(None)["bg"])  # under any antialiased edge; the screenshot's background is clear
        if setup:
            setup(pl)
        frames = []
        for i in range(n):
            draw(pl, i / fps)
            pl.renderer.ResetCameraClippingRange()
            pl.render()  # VTK does not redraw for a screenshot by itself after the scene changes
            frames.append(png(pl.screenshot(transparent_background=True, return_img=True)))
    finally:
        pl.close()
    return Clip(frames, fps, width)


def from_model(path, seconds: float = 4, fps: float = 15, size: tuple[int, int] = (1280, 720),
               width: float = DEFAULT_WIDTH, orbit: float = 60, azimuth: float = -30, elevation: float = 20,
               zoom: float = 1.0, animation: int | str | None = 0, loop: bool = False, up: str = "y",
               color: str | None = None) -> Clip:
    """The model in `path` (.glb or .gltf with its materials and animations; .obj, .stl or .ply in `color`,
    default the theme accent) rendered with lighting on a transparent background, `seconds` long at `fps`.
    The camera starts `azimuth` degrees round the model and `elevation` degrees above it, and turns
    `orbit` degrees over the clip (0 holds still; 360 loops seamlessly); `zoom` above 1 moves it closer.
    `up` is the model's up axis, "y" for glTF and OBJ, "z" for STL and CAD. A glTF animation clip (an index
    or a name; None for none) plays from its start in step with the clip, holding its last pose, or
    repeating if `loop`. Needs the pyvista extra and OpenGL."""
    path = Path(path)
    if not path.is_file():
        raise SceneError(f"no model file at {path}")
    if path.suffix.lower() not in GLTF | OTHER:
        raise SceneError(f"{path.suffix or path.name} is not a model format; use .glb, .gltf, .obj, .stl or .ply")
    if up not in VIEW_UP:
        raise SceneError(f"up must be 'y' or 'z', got {up!r}")
    if not zoom > 0:
        raise SceneError(f"zoom must be greater than 0, got {zoom}")
    n = frame_count(seconds, fps)
    state = {}

    def setup(pl):
        imp, span = _load(pl, path, color or _theme(None)["accent"], animation)
        if span:
            imp.UpdateAtTimeValue(span[0])
        x0, x1, y0, y1, z0, z1 = pl.renderer.ComputeVisiblePropBounds()
        radius = max(1e-9, math.dist((x0, y0, z0), (x1, y1, z1)) / 2)
        state.update(imp=imp, span=span, centre=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
                     dist=radius / math.sin(math.radians(pl.camera.view_angle) / 2) / zoom)

    def draw(pl, t):
        span = state["span"]
        if span:
            length = span[1] - span[0]
            local = (t % length if loop else min(t, length)) if length > 0 else 0.0
            state["imp"].UpdateAtTimeValue(span[0] + local)
        az = math.radians(azimuth + orbit * round(t * fps) / n)  # so orbit=360 loops without a repeated frame
        el = math.radians(elevation)
        # the camera on a sphere round the model, measured from its front (+z for y-up, -y for z-up)
        if up == "y":
            offset = (math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el))
        else:
            offset = (math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))
        cam = pl.camera
        cam.position = tuple(c + state["dist"] * o for c, o in zip(state["centre"], offset))
        cam.focal_point = state["centre"]
        cam.up = VIEW_UP[up]

    return from_pyvista(draw, seconds, fps, size, width, setup=setup)
