"""manimvox's own lighting for 3D faces, and the camera that draws them.

Manim's 3D shading blends each face towards white by its angle to a light fixed in the scene, so colours wash
out as the camera moves. A face with a `lighting` attribute (a `Lighting`) is instead coloured from its own
base colour by a light fixed to the camera, vectorised over every such face once per frame, and drawn in bulk.
Faces keep `shade_in_3d` so the camera still sorts them by depth; the lit camera skips Manim's own shading
for them. Episode3D uses `LitCamera`."""
from __future__ import annotations

from dataclasses import dataclass

import cairo
import numpy as np
from manim.camera.camera import Camera
from manim.camera.three_d_camera import ThreeDCamera

DEFAULT_LIGHT = (-0.35, 0.45, 0.82)  # towards the light, as the viewer sees it: x right, y up, z out of the screen


@dataclass(frozen=True)
class Lighting:
    """ambient + diffuse (Lambert) from a light fixed to the camera, plus a small lift for faces seen edge-on
    so silhouettes read. `light` points towards the light in the viewer's frame (x right, y up, z towards
    the viewer); `ambient` is the share of the base colour a face turned from the light keeps; `rim` lifts
    edge-on faces; no face is brighter than its base colour times `cap`."""

    light: tuple[float, float, float] = DEFAULT_LIGHT
    ambient: float = 0.55
    rim: float = 0.12
    cap: float = 1.0


def shade_factors(normals: np.ndarray, rotation: np.ndarray, lighting: Lighting) -> np.ndarray:
    """Per face, the factor (0 to `lighting.cap`) its base colour is multiplied by. `normals` are (n, 3) in
    scene coordinates, `rotation` is the camera's rotation matrix. Faces are two-sided: a normal pointing away
    from the viewer is flipped, so open surfaces and badly wound faces light like the rest."""
    view = normals @ rotation.T
    view = view / np.maximum(np.linalg.norm(view, axis=1, keepdims=True), 1e-12)
    view = view * np.where(view[:, 2] < 0, -1.0, 1.0)[:, None]
    light = np.asarray(lighting.light, float)
    light = light / np.linalg.norm(light)
    diffuse = np.clip(view @ light, 0.0, 1.0)
    edge = (1.0 - view[:, 2]) ** 2
    k = lighting.ambient + (1.0 - lighting.ambient) * diffuse + lighting.rim * edge
    return np.clip(k, 0.0, lighting.cap)


def shade_colors(base: np.ndarray, normals: np.ndarray, rotation: np.ndarray, lighting: Lighting) -> np.ndarray:
    """`base` (n, 3) RGB in 0..1 scaled by shade_factors: hue is kept, nothing washes towards white."""
    return base * shade_factors(normals, rotation, lighting)[:, None]


def _lit(m) -> bool:
    return getattr(m, "lighting", None) is not None


def _corners(faces) -> np.ndarray:
    """(n, 3, 3): the three corners of each triangle face."""
    return np.array([f.points[0:9:4] for f in faces])


def _normals(corners: np.ndarray) -> np.ndarray:
    return np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])


class LitCamera(ThreeDCamera):
    """A ThreeDCamera that lights and draws faces with a `lighting` attribute itself (see the module note),
    and sorts them by depth in one numpy pass. Everything else draws as in Manim."""

    def modified_rgbas(self, vmobject, rgbas):
        return rgbas if _lit(vmobject) else super().modified_rgbas(vmobject, rgbas)

    def get_mobjects_to_display(self, *args, **kwargs):
        mobjects = Camera.get_mobjects_to_display(self, *args, **kwargs)
        rot = self.get_rotation_matrix()
        keys = np.full(len(mobjects), np.inf)
        flat = [i for i, m in enumerate(mobjects) if _lit(m) and len(m.points) == 12]
        if flat:
            keys[flat] = (_corners([mobjects[i] for i in flat]).mean(axis=1) @ rot.T)[:, 2]
        flat = set(flat)
        for i, m in enumerate(mobjects):
            if i not in flat and getattr(m, "shade_in_3d", False):
                keys[i] = np.dot(m.get_z_index_reference_point(), rot.T)[2]
        return [mobjects[i] for i in np.argsort(keys, kind="stable")]

    def display_multiple_non_background_colored_vmobjects(self, vmobjects, pixel_array):
        ctx = self.get_cairo_context(pixel_array)
        run = []
        for m in vmobjects:
            if _lit(m) and len(m.points) == 12 and m not in self.fixed_in_frame_mobjects:
                run.append(m)
                continue
            self._draw_lit(run, ctx)
            run = []
            self.display_vectorized(m, ctx)
        self._draw_lit(run, ctx)

    def _draw_lit(self, faces, ctx):
        """Light, project and draw a run of triangles at once: one projection and one shading for all."""
        if not faces:
            return
        corners = _corners(faces)
        flat = self.project_points(corners.reshape(-1, 3)).reshape(-1, 3, 3)[:, :, :2]
        fills = np.array([f.fill_rgbas[0] for f in faces])
        strokes = np.array([f.stroke_rgbas[0] for f in faces])
        # one lighting per run in practice; group so a mixed run still shades each face with its own
        factor = np.empty(len(faces))
        rot = self.get_rotation_matrix()
        normals = _normals(corners)
        by = {}
        for i, f in enumerate(faces):
            by.setdefault(f.lighting, []).append(i)
        for lighting, idx in by.items():
            factor[idx] = shade_factors(normals[idx], rot, lighting)
        fills[:, :3] *= factor[:, None]
        # a face's edge takes the same lit colour as its fill unless it was given a stroke of its own colour
        own = np.array([getattr(f, "lit_stroke", True) for f in faces])
        strokes[:, :3] = np.where(own[:, None], fills[:, :3], strokes[:, :3])
        widths = (np.array([f.get_stroke_width() for f in faces]) * self.cairo_line_width_multiple).tolist()
        ctx.set_line_join(cairo.LineJoin.MITER)  # what Manim's AUTO joins and caps draw as
        ctx.set_line_cap(cairo.LineCap.BUTT)
        new_path, move_to, line_to, close_path = ctx.new_path, ctx.move_to, ctx.line_to, ctx.close_path
        set_rgba, fill, stroke, set_width = ctx.set_source_rgba, ctx.fill_preserve, ctx.stroke_preserve, ctx.set_line_width
        for (p0, p1, p2), (fr, fg, fb, fa), (sr, sg, sb, sa), w in zip(flat.tolist(), fills.tolist(), strokes.tolist(), widths):
            new_path()
            move_to(*p0)
            line_to(*p1)
            line_to(*p2)
            close_path()
            set_rgba(fb, fg, fr, fa)  # cairo's pixels are BGR
            fill()
            if w > 0:
                set_rgba(sb, sg, sr, sa)
                set_width(w)
                stroke()
