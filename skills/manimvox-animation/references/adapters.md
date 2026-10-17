# Charts and frames from other libraries

`manimvox.scenes` turns frames from Pillow, numpy, Cairo, Matplotlib or Plotly into a `Clip`, an image mobject that plays its frames. Import from `manimvox.scenes`.

## Clips

- Place a clip with `.move_to(...)`. Its width is in scene units (default 9.6) whatever the render quality, so a draft and a final render match. Pass `width=` to change it.
- Play it over a line:

  ```python
  clip = from_frames(lambda t: image_at(t), seconds=4)
  self.add(clip)
  with self.narrate("Watch the curve settle.") as dur:
      self.play(clip.play(), run_time=dur)
  ```

- Fade it in before playing it, because playing resets its opacity.
- A clip holds its frames in memory, at most 3600. Lower `fps` for long clips. Every frame must be one size.
- A one-frame clip is a still image: `still(image)`.

## Pillow or numpy

`from_frames(draw, seconds, fps=15)`, where `draw(t)` returns a PIL image or an (h, w, 3 or 4) uint8 array:

```python
from PIL import Image, ImageDraw
def image_at(t):
    im = Image.new("RGB", (1280, 720), palette()["bg"])
    ImageDraw.Draw(im).ellipse([100 + 200 * t, 200, 300 + 200 * t, 400], fill=palette()["accent"])
    return im
clip = from_frames(image_at, seconds=4)
```

## Cairo

`from_cairo(draw, seconds, fps=15, size=(1280, 720))`, with `draw(ctx, t, w, h)` painting on a transparent canvas. Take colours from `palette()`: `palette()["accent"]` is a `#RRGGBB` string, so convert it before `ctx.set_source_rgb`.

## Matplotlib

- The extra is `manimvox[kokoro,matplotlib]`. Ask the user before installing it.
- Build the figure inside `with plt.rc_context(mpl_style()):` so it wears the theme.
- `from_matplotlib(fig)` gives a still. `from_matplotlib(FuncAnimation(...), fps=15)` gives every frame of the animation. Call `plt.close(fig)` after.

```python
import matplotlib.pyplot as plt
from manimvox.scenes import from_matplotlib, mpl_style
with plt.rc_context(mpl_style()):
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    ax.plot([1, 2, 3], [2, 5, 3])
clip = from_matplotlib(fig)
plt.close(fig)
```

## Plotly

- The extra is `manimvox[kokoro,plotly]`.
- Kaleido needs Chrome. If it is missing, the error names `plotly_get_chrome`, which downloads Chrome. Ask the user first. With no way to ask, use Matplotlib instead.
- Use `fig.update_layout(template=plotly_template())`. `from_plotly(fig)` gives a still. `from_plotly(lambda t: make_fig(t), seconds=3, fps=10)` gives an animation, one export per frame, so keep `seconds * fps` small.

## Theme colours

`palette()` maps every role and named colour of the series theme to a hex string. `series_colours()` lists the order the charts use for several series.

## Numbers

Every number in a chart comes from `FACTS.md`, like any on-screen claim.
