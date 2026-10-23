# 3D scenes

Manim draws in 3D: a camera you can tilt and turn, shapes with depth, and surfaces. Use it when depth is the idea: a surface or landscape, vectors in space, layers stacked on each other, a shape seen from several sides. Everything else stays 2D, which reads faster.

## Turn an episode 3D

Subclass `Episode3D` instead of `Episode`. Everything else about the episode stays the same.

- The camera: `self.move_camera(phi=..., theta=..., run_time=...)` tilts (`phi`, 0 is straight on) and turns (`theta`, -90° is straight on). Run it inside `with self.narrate(...)` so it moves while the line is spoken, and pass reveals along with `added_anims=[...]`. `self.set_camera_orientation(...)` jumps there with no animation.
- A slow orbit while talking: `self.begin_ambient_camera_rotation(rate=0.15)`. Keep the rate between 0.1 and 0.2, and orbit at most once a scene. `self.stop_ambient_camera_rotation()` stops it.
- Shapes: `ThreeDAxes`, `Surface`, `Sphere`, `Dot3D`, `Cube`, `Prism`, `Cylinder`, `Cone`, `Torus`, `Arrow3D`, `Line3D`. For a surface z = f(x, y), add the `surface-plot` block (`manimvox add surface-plot`).
- The header, chapter label and progress bar stay put on screen. `intro()`, `chapter()` and `outro()` clear the stage and put the camera back to the flat view, so their cards are never tilted.
- `self.camera_home()` turns the camera back to the flat view as an animation, to end a scene on a flat picture or to carry on in 2D.

## Labels

Text placed in the 3D scene turns and stretches with it. Pin headings, labels and numbers to the screen with `self.pin(...)` before revealing them; a pinned label stays where it was put while the camera moves.

A pinned label does not follow the 3D object either. Put it beside the object, not on it, and list labels in the order the viewer sees the parts after the tilt.

## Cost and limits

- 3D renders slowly. Keep a `Surface` at a resolution of 16 to 24, and draft (`manimvox draft epNN --every 3`) until the scene is right.
- The shading is flat: there is no real lighting, and the side facing the light washes towards white. Choose colours that stay apart when lightened.
- Where two objects cross, faces can be drawn in the wrong order, and axes show through a surface. Keep objects apart.
- Manim's shapes cover diagrams. For a real object (an organ, a machine part, a building), load a model: see below.
- No LaTeX: write formulas with `T()` and pin them.
- `manimvox check layout` sees 3D text where the camera shows it, and pinned text where it was put.

## 3D models from files

A model file (.glb, .gltf, .obj, .stl, .ply) goes in two ways. From Blender, export glTF 2.0 (`.glb`): it keeps the colours, the part names and the animations.

| | `mesh-model` block | `from_model` clip |
|---|---|---|
| Drawn by | Manim, one shaded face per triangle | a 3D renderer, with real lighting and materials |
| Camera | Manim's: tilt, orbit, `pin()` labels beside it | its own orbit, set when the clip is made |
| Detail | simplified to `max_faces` (default 1500, at most 5000) | every triangle |
| Parts | `mesh_part` picks faces to recolour or label | none: the clip is one picture |
| glTF animations | no | yes, played in step with the clip |
| Extra | `trimesh` | `pyvista` (needs OpenGL) |

Use the block when the narration points at parts or the camera moves with the rest of the scene. Use the clip when the model should look real, or it moves.

Both extras are installs: ask the user before adding one. A model from the web has a licence: check it allows the use, and put its credit on screen (a muted line at `STAGE_BOTTOM`) and in `FACTS.md`. Keep model files in the project's `research/` folder.

### The block

```python
from blocks.mesh_model import mesh_model, mesh_part
heart = mesh_model("research/heart.glb", size=5, max_faces=2000).move_to(DOWN * 0.6)
vessels = mesh_part(heart, inside=lambda x, y, z: z > 1.1)  # scene units from the model's middle, z up
self.say("Blood leaves through the vessels at the top.", vessels.animate.set_fill(WARN))
```

- Run `manimvox add mesh-model` first. `up="y"` suits glTF and OBJ; an STL standing on its side wants `up="z"`. Draft once and look.
- `mesh_part(model, name="aorta")` picks a glTF part by name; `model.parts` lists them.
- Manim's light washes the faces that face it towards white: pass a darker `color` than you want to see, such as `interpolate_color(ERROR, BG, 0.35)`.
- Every face costs render time on every frame: a 2500-face model made a one-minute episode take about two minutes to draft. Lower `max_faces` until the shape starts to suffer.
- Reveal it with `FadeIn`. `Create` draws every edge and is slow.

### The clip

```python
from manimvox.scenes import from_model, palette
clip = from_model("research/heart.glb", seconds=6, orbit=360, elevation=10, zoom=1.3, width=8.4)
self.pin(clip)  # in an Episode3D, or the tilted camera tilts the picture too
self.add(clip)
with self.narrate("Here it is, turning once all the way round.") as dur:
    self.play(clip.play(), run_time=dur)
```

- `orbit` is the turn over the clip in degrees (0 holds still), from `azimuth` round and `elevation` above. `zoom` above 1 moves closer.
- A glTF animation plays from its start: `animation=` takes its index or name, `None` for none, and `loop=True` repeats it.
- An OBJ, STL or PLY has no materials: it takes `color` (default the theme accent; `palette()["error"]` for a red).
- Each frame is drawn from its time, so a draft and a final render give the same frames. `seconds * fps` frames are rendered: keep `fps` at 15.
- It works in a plain `Episode` too, with no tilt.
- `clip.loop()` keeps it turning under several lines; `clip.at(x, y)` puts a label on a pixel of it.
- To cut a model open, light it your own way, or show scan or simulation data, use `from_pyvista` (see [adapters.md](adapters.md)). A downloaded surface model is hollow inside; a cut shows chambers and walls only on a volume mesh, such as a segmented scan.

## Pattern: tilt to show depth

What looks flat has depth. This complete chapter has been run through `manimvox draft`.

```python
class Ep01(Episode3D):
    EP = 1
    TITLE = "What an image is"
    TAGLINE = "Three layers of numbers"
    NCHAP = 1

    def build(self):
        self.intro("What is a picture, to a computer?", question="What is a picture, to a computer?")
        self.chapter("Three layers")
        h = heading("An image is three layers")
        # bottom to top: blue, green, red, so the labels below read in the order the stack shows them
        layers = VGroup(*[Prism(dimensions=[4, 3, 0.12]).set_fill(c, 0.85).set_stroke(BG, 1).shift(OUT * 0.7 * i)
                          for i, c in enumerate([BLUE, OK, ERROR])]).move_to(DOWN * 0.4)
        names = VGroup(*[T(n, 22, c, BOLD) for n, c in [("red", ERROR), ("green", OK), ("blue", BLUE)]])
        names.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([4.6, -0.4, 0])
        self.pin(h, names)
        self.say("Seen straight on, an image looks like one flat picture.", FadeIn(h, shift=DOWN * 0.2), FadeIn(layers))
        with self.narrate("Tilt it, and it is three layers stacked, one for each colour of light."):
            self.move_camera(phi=65 * DEGREES, theta=-40 * DEGREES, run_time=2)
        self.steps("Red, green and blue.", [FadeIn(n, shift=LEFT * 0.2) for n in names])
        self.begin_ambient_camera_rotation(rate=0.15)
        self.say("Every pixel is three numbers, one in each layer.")
        self.beat()
        self.camera_home()
        self.outro([], "So a picture is a stack of numbers.", answer="Three layers of numbers.")
```
