from manimvox.kit import *

W, H = 2.4, 1.2
BROWSER, APP, CACHE, DB = ([-5.5, -0.5, 0], [-1.8, -0.5, 0], [1.8, 0.9, 0], [1.8, -1.9, 0])


def part(name, at, w=W):
    """A part of the system as a box with its name; opaque, so a flow passes behind it."""
    b = box(w, H, fill=PANEL, stroke=LINE)
    b.add(T(name, 28, INK).move_to(b))
    return b.move_to(at).set_z_index(2)


def state(box_, text, color=MUTED):
    """A small line under a box's name that says what it holds right now."""
    return T(text, 24, color).next_to(box_, DOWN, buff=0.12).set_z_index(2)


class Ep01(Episode):
    EP = 1
    TITLE = "Faster the second time?"
    TAGLINE = "A cache, in one request"
    NCHAP = 1
    CHROME = ()

    def build(self):
        browser, app = part("Browser", BROWSER, 2.0), part("App server", APP)
        cache, db = part("Cache", CACHE), part("Database", DB)
        parts = VGroup(browser, app, cache, db)
        empty = state(cache, "empty")
        eg = T("one common design: real sites differ", 20, MUTED, slant=ITALIC).move_to([0, STAGE_BOTTOM + 0.2, 0])

        # every flow is its own stream, so the picture shows exactly what the voice says
        req = stream([browser.get_right() + UP * 0.2, app.get_left() + UP * 0.2], color=ACCENT, n=16, speed=0.22, size=0.06)
        page = stream([app.get_left() + DOWN * 0.2, browser.get_right() + DOWN * 0.2], color=OK, n=16, speed=0.22, size=0.06)
        to_cache = stream([app.get_right() + UP * 0.3, cache.get_left() + DOWN * 0.1], color=ACCENT, n=14, speed=0.25, size=0.06)
        from_cache = stream([cache.get_left() + DOWN * 0.3, app.get_right() + UP * 0.1], color=OK, n=14, speed=0.25, size=0.06)
        to_db = stream([app.get_right() + DOWN * 0.1, db.get_left() + UP * 0.3], color=ACCENT, n=14, speed=0.25, size=0.06)
        from_db = stream([db.get_left() + UP * 0.1, app.get_right() + DOWN * 0.3], color=OK, n=14, speed=0.25, size=0.06)
        save = stream([app.get_right() + UP * 0.1, cache.get_left() + DOWN * 0.3], color=VIOLET, n=14, speed=0.25, size=0.06)
        flows = [req, page, to_cache, from_cache, to_db, from_db, save]
        for f in flows:
            f.level.set_value(0)
            f.set_z_index(1)

        names_cache = leader(cache.get_right(), "recent answers", side="right", x=3.6, size=24)
        names_db = leader(db.get_right(), "everything, slower", side="right", x=3.6, size=24)
        VGroup(names_cache, names_db).set_z_index(3)
        click = enters(browser.get_top(), DOWN, "a click", length=0.7, size=24)
        out = leaves(browser.get_bottom(), DOWN, "the page", length=0.7, size=24)

        ring = RoundedRectangle(width=W, height=H, corner_radius=0.12).set_stroke(ACCENT, 4).move_to(CACHE).set_z_index(3)
        self.add(*flows)
        self.play(FadeIn(parts), FadeIn(eg), run_time=0.8)
        self.intro("Why is the same page faster the second time?", card=False,
                   question="Why is the same page faster the second time?")
        self.beat(0.3)

        def only(*on, rest=0.0):
            """Brighten these flows and set every other to `rest`."""
            return [f.brighten() if f in on else f.fade_to(rest) for f in flows]

        # ---- the first time -------------------------------------------------
        self.say("The request goes to the app server.", FadeIn(click), *only(req))
        self.say("It asks the cache first. A cache keeps recent answers, and this one is empty.",
                 *only(to_cache, rest=0.25), FadeIn(empty), names_cache.grow())
        self.say("So it asks the database, which keeps everything and is slower.", *only(to_db, from_db, rest=0.2),
                 names_db.grow())
        saved = state(cache, "a saved copy", VIOLET)
        self.say("It saves a copy in the cache, then sends the page.", *only(save, page, rest=0.2),
                 Transform(empty, saved), FadeIn(out))
        saved = empty
        self.beat(0.3)

        # ---- the second time ------------------------------------------------
        self.say("Now open it again.", FadeIn(ring), *only(req))
        self.say("The app server asks the cache, and this time the answer is there.",
                 *only(req, to_cache, from_cache, rest=0.0), db.animate.set_opacity(0.3), names_db.animate.set_opacity(0.3))
        self.say("The database is never asked, so the page comes back sooner.", *only(from_cache, page, req, rest=0.3))
        # the short trip keeps flowing under the answer; the rest of the flows go
        trip = [req, to_cache, from_cache, page]
        gone = [f for f in flows if f not in trip]
        everything = VGroup(parts, saved, click, out, names_cache, names_db, ring, *trip)
        self.play(everything.animate.shift(DOWN * 0.5), *[f.fade_to(0) for f in gone], *[f.brighten() for f in trip],
                  run_time=0.8)  # room above for the answer
        self.remove(*gone)
        self.outro([], "Same request, shorter trip.",
                   answer="The second time, the app server answers from its cache and skips the slow database.",
                   keep=[everything, eg])
