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
- Manim cannot load 3D models (OBJ, glTF). Build from its shapes.
- No LaTeX: write formulas with `T()` and pin them.
- `manimvox check layout` sees 3D text where the camera shows it, and pinned text where it was put.

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
