from manimvox.kit import *
from blocks.surface_plot import downhill, surface_path, surface_plot, surface_point


def loss(x, y):
    return 0.12 * (x * x + y * y) - 0.9 * np.exp(-((x - 1) ** 2 + (y - 0.8) ** 2))


class Demo(Episode3D):
    def build(self):
        h = heading("A ball rolls downhill", sub="Loss for every pair of settings: lower is better")
        self.pin(h)
        plot = surface_plot(loss, resolution=20).move_to(DOWN * 0.8)
        route = downhill(plot, -2.6, -2.4)
        ball = Dot3D(surface_point(plot, *route[0], lift=0.16), radius=0.16, color=WARN)
        self.say("Here are two settings of a model, side by side.", FadeIn(h, shift=DOWN * 0.2), Create(plot.axes))
        with self.narrate("Tilt the picture, and the loss rises out of the floor as a landscape."):
            self.move_camera(phi=52 * DEGREES, theta=-60 * DEGREES, added_anims=[Create(plot.surface)], run_time=2.2)
        trail = surface_path(plot, route)
        roll = surface_path(plot, route, lift=0.16)
        self.steps("Drop a ball anywhere, and it rolls down into the lowest valley.",
                   [FadeIn(ball), [MoveAlongPath(ball, roll), Create(trail)]], run_time=2.5)
        self.wait(1)
