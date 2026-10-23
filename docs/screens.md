# Screenshots and recordings

Product demos, "how to use this app" videos and PR walkthroughs whose change shows in the UI need the real screen on screen. manimvox doesn't open browsers or apps itself: your agent captures with the tools it already has (a browser tool such as Playwright MCP, or computer use), and manimvox presents the captures, timed to the narration.

## What you can do

| | |
|---|---|
| `screenshot(path)` | a PNG, JPEG or WebP file as a clip |
| `from_video(path, start=, end=)` | a screen recording (MP4, WebM, MOV) as a clip that plays |
| `clip.zoom(x, y, w, h)` / `clip.zoom_out()` | zoom into a region inside the clip's own frame, and back |
| `spotlight(clip, region)` | dim everything except a region, and outline it |
| `callout(clip, region, "text", side=)` | a label with an arrow to a region |
| `cursor()`, `point(pointer, spot)`, `click(pointer)` | a mouse pointer that moves and clicks |
| `window(clip, url=)` | browser or app chrome around a screenshot |

Regions are `(x, y, w, h)` in the pixels of the file, counted from the top left, so you can read them off the screenshot itself. They stay right however wide the clip is and however far it zooms.

## Example

```python
from manimvox.kit import *
from manimvox.scenes import callout, click, cursor, point, screenshot, spotlight, window

SEARCH = (1135, 9, 196, 35)        # the search box, in pixels of the screenshot


class Ep01(Episode):
    def build(self):
        shot = screenshot("research/screens/01-home.png", width=10.4).move_to(STAGE_CENTER + DOWN * 0.25)
        self.say("This is the home page.", FadeIn(Group(window(shot, url="example.com"), shot)))

        pointer = cursor().move_to(shot.get_center())
        self.say("Search finds any page.", FadeIn(pointer), point(pointer, shot.at(1160, 26)))
        self.say("Click it.", click(pointer))

        spot = spotlight(shot, SEARCH)
        self.say("Everything else fades back.", FadeIn(spot))

        self.say("Look closer.", FadeOut(spot), FadeOut(pointer), shot.zoom(*SEARCH))
        tag = callout(shot, SEARCH, "Ctrl+K", side="down")
        self.say("Or press Control K.", FadeIn(tag))
        self.say("Back to the page.", FadeOut(tag), shot.zoom_out())
```

A zoom stays inside the clip's frame, so it never covers the header. Make overlays after a zoom, because they point at the picture as it is when they're made.

## With an agent

The animation skill tells the agent how to capture: at 1920x1080, saved to `research/screens/`, with a fresh browser profile and nothing personal on screen, and with each capture cited in `FACTS.md`. The agent asks you before it opens a URL or an app, as for any web access. If it has no capture tool, it asks you for the screenshots.

Ask for it in plain words: *"make a 1-minute demo video of how to search this docs site"*, or *"walk through PR #42 and show the page before and after"*.
