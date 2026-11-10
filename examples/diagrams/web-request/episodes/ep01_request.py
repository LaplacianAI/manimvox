from manimvox.kit import *

BOX_W, BOX_H = 2.5, 0.8
BROWSER, LB, APP, CACHE, DB = ([0, 2.0, 0], [0, 0.6, 0], [0, -0.8, 0], [-1.6, -2.3, 0], [1.6, -2.3, 0])


def part(name, at):
    """A service as a box with its name; opaque, so the streams pass behind it."""
    b = box(BOX_W, BOX_H, fill=PANEL, stroke=LINE)
    b.add(T(name, 22, INK).move_to(b))
    return b.move_to(at).set_z_index(2)


class Ep01(Episode):
    EP = 1
    TITLE = "A web request"
    TAGLINE = "From a click to a page"
    NCHAP = 1

    def build(self):
        self.intro("Every page you open is a request that travels through several services.")
        self.chapter("The trip", "Follow one request from the browser.")
        browser, lb, app = part("Browser", BROWSER), part("Load balancer", LB), part("App server", APP)
        cache, db = part("Cache", CACHE), part("Database", DB)
        parts = VGroup(browser, lb, app, cache, db)

        names = leaders([(lb.get_left(), "spreads the traffic"), (cache.get_left(), "remembers answers")], side="left")
        names_r = leaders([(app.get_right(), "runs the code"), (db.get_right(), "keeps the records")], side="right")
        VGroup(names, names_r).set_z_index(3)
        in_arrow = enters(browser.get_left(), RIGHT, "a click", length=1.4)
        out_arrow = leaves(browser.get_right(), RIGHT, "a page", length=1.4)

        # the request runs down the middle, out to the database; the response comes back up beside it
        down = [browser.get_bottom() + RIGHT * -0.3, lb.get_top() + RIGHT * -0.3, app.get_bottom() + RIGHT * -0.3,
                db.get_top() + LEFT * 0.4]
        up = [db.get_top() + RIGHT * 0.1, app.get_bottom() + RIGHT * 0.3, lb.get_top() + RIGHT * 0.3,
              browser.get_bottom() + RIGHT * 0.3]
        request = stream(down, color=ACCENT).set_z_index(1)
        response = stream(up, color=OK).set_z_index(1)

        self.play(FadeIn(parts), run_time=0.8)
        self.add(request)
        self.say("A click leaves the browser as a request, and reaches the load balancer.",
                 FadeIn(in_arrow), names[0].grow())
        self.say("The load balancer hands it to an app server, which does the work.", names_r[0].grow())
        self.say("The app server asks the cache first, and falls back to the database.",
                 LaggedStart(names[1].grow(), names_r[1].grow(), lag_ratio=0.5))
        self.add(response)
        self.say("Then the response travels back the same way, and the page appears.",
                 request.fade_to(0.2), FadeIn(out_arrow))
        self.beat(0.5)
        request.stop(), response.stop()
        self.outro([], "A request goes in, and a page comes back.")
