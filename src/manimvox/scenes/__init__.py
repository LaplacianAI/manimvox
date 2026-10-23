"""Scene adapters: frames from Pillow, Cairo, Matplotlib, Plotly or a 3D model as a Clip that an episode places
and plays; screenshots and screen recordings as a Clip, with overlays that point at what they show."""
from .charts import SERIES_ROLES, from_matplotlib, from_plotly, mpl_style, palette, plotly_template, series_colours
from .clip import DEFAULT_WIDTH, MAX_FRAMES, Clip, PlayClip, SceneError, Zoom, png, rgba
from .model import from_model, from_pyvista, screen_xy
from .raster import frame_count, from_cairo, from_frames, from_video, screenshot, still
from .screen import box_on, callout, click, cursor, point, spotlight, window

__all__ = ["DEFAULT_WIDTH", "MAX_FRAMES", "SERIES_ROLES", "Clip", "PlayClip", "SceneError", "Zoom", "box_on",
           "callout", "click", "cursor", "frame_count", "from_cairo", "from_frames", "from_matplotlib", "from_model",
           "from_plotly", "from_pyvista", "from_video", "mpl_style", "palette", "plotly_template", "png", "point",
           "rgba", "screen_xy", "screenshot", "series_colours", "spotlight", "still", "window"]
