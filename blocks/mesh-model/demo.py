from manimvox.kit import *
from blocks.mesh_model import mesh_model, mesh_part


def torus(n=20, m=8, big=1.0, small=0.4):
    """A low-poly ring as (vertices, faces), z up: a model file goes in the same place."""
    u, v = np.meshgrid(np.linspace(0, TAU, n, endpoint=False), np.linspace(0, TAU, m, endpoint=False))
    r = big + small * np.cos(v)
    verts = np.stack([r * np.cos(u), r * np.sin(u), small * np.sin(v)], axis=-1).reshape(-1, 3)
    faces = []
    for j in range(m):
        for i in range(n):
            a, b = j * n + i, j * n + (i + 1) % n
            c, d = ((j + 1) % m) * n + i, ((j + 1) % m) * n + (i + 1) % n
            faces += [(a, b, d), (a, d, c)]
    return verts, np.array(faces)


class Demo(Episode3D):
    def build(self):
        h = heading("A ring has one hole", sub="Any model from a file works the same way")
        self.pin(h)
        ring = mesh_model(torus(), size=4.6, color=TEAL, up="z", wire=True).move_to(DOWN * 0.6)
        top = mesh_part(ring, inside=lambda x, y, z: z > 0.05 and y < 0)
        label = T("the near half of the top", 22, WARN, BOLD).move_to([4.4, -2.6, 0])
        self.pin(label)
        self.say("Seen from above, a ring is a flat loop.", FadeIn(h, shift=DOWN * 0.2), FadeIn(ring))
        with self.narrate("Tilt it, and it has depth all the way round."):
            self.move_camera(phi=62 * DEGREES, theta=-50 * DEGREES, run_time=2)
        self.say("Any part of it can be picked out.", top.animate.set_fill(WARN), FadeIn(label))
        self.begin_ambient_camera_rotation(rate=0.15)
        self.wait(1.5)
