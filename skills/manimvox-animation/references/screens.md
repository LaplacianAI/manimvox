# Screenshots and screen recordings

For a product demo, a "how to use this app" video, or a PR walkthrough whose change shows in the UI. manimvox does not open browsers or apps: capture with your own tools, then present the captures with `manimvox.scenes`.

## Capture

- **Use a tool you already have:** a browser tool (Playwright MCP, a browser skill), computer use, or the app's own screenshot command. If you have none, ask the user for the screenshots. Opening a URL or an app is a fetch: ask first, as for any web access.
- **Size:** 1920x1080 for the whole screen or window, so it fills the clip sharply. A recording at 1280x720 or more.
- **Save** to `research/screens/`, named for what each shows: `01-home.png`, `02-search-open.png`, `03-results.mp4`.
- **Note the regions** you will point at, as pixel boxes `(x, y, w, h)` from the top left of the file: the button, the field, the result. Read them off the image (open it and measure) or from the browser tool (an element's bounding box). Write them as constants at the top of the episode.
- **Clean the screen first:** close banners and pop-ups, use a fresh profile with no personal data, and blur or avoid real names, emails and keys. A capture is published with the video.
- **Cite it:** add each capture to `FACTS.md` with what it shows, the URL or app and version, and the date.

## Present

```python
from manimvox.scenes import callout, click, cursor, point, screenshot, spotlight, window

SEARCH = (1135, 9, 196, 35)        # pixels in research/screens/01-home.png

shot = screenshot("research/screens/01-home.png", width=10.4).move_to(STAGE_CENTER + DOWN * 0.25)
chrome = window(shot, url="example.com")              # browser chrome; title="App" for an app
self.say("This is the home page.", FadeIn(Group(chrome, shot)))

pointer = cursor().move_to(shot.get_center())
self.say("Search finds any page.", FadeIn(pointer), point(pointer, shot.at(1160, 26)))
self.say("Click it.", click(pointer))                 # after the point, never alongside

spot = spotlight(shot, SEARCH)                        # dim everything else
self.say("Everything else fades back.", FadeIn(spot))

self.say("Look closer.", FadeOut(spot), FadeOut(pointer), shot.zoom(*SEARCH))
tag = callout(shot, SEARCH, "Ctrl+K", side="down")    # made after the zoom: it points at the zoomed picture
self.say("Or press Control K.", FadeIn(tag))
self.say("Back to the page.", FadeOut(tag), shot.zoom_out())
```

- **Regions are pixels of the source file**, whatever the clip's width or zoom. `shot.at(x, y)` is the scene point over a pixel.
- **`shot.zoom(x, y, w, h)` zooms inside the clip's own frame,** so it never covers the header. It keeps a margin and the clip's shape. A full-page screenshot is small on screen: zoom before asking the viewer to read anything.
- **Make overlays after the clip has moved or zoomed,** and fade them out before the next zoom: they are placed for the picture as it is when they are made. An overlay on a region the zoom has hidden is an error.
- **One thing at a time:** one spotlight or callout per line, faded out before the next.
- **Before and after:** two screenshots side by side, `Group(a, b).arrange(RIGHT, buff=0.4)`, each with `width=6.2`, then zoom into the same region of each.
- **A sequence of screens:** `self.swap(old, new)` between captures of one flow, with the same position and width, so only the content changes.

## Recordings

```python
from manimvox.scenes import from_video
rec = from_video("research/screens/03-results.mp4", fps=15, start=2.0, end=8.0).move_to(STAGE_CENTER)
self.add(rec)
with self.narrate("Results appear as you type.") as dur:
    self.play(rec.play(), run_time=dur)
```

- Trim with `start` and `end` (seconds) to the part the line talks about; a clip holds at most 3600 frames.
- Frames wider than 1280 pixels are scaled down to save memory; regions stay in the recording's own pixels.
- `rec.zoom(...)` and the overlays work on a recording as on a screenshot, and can run while it plays.
- Prefer screenshots with a cursor and zooms over long recordings: they are sharper, and every step can follow the narration.
