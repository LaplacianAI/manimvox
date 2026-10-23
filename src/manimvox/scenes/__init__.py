"""Scene adapters: frames from Pillow, Cairo, Matplotlib, Plotly or a 3D model as a Clip that an episode places
and plays."""
from .charts import SERIES_ROLES, from_matplotlib, from_plotly, mpl_style, palette, plotly_template, series_colours
from .clip import DEFAULT_WIDTH, MAX_FRAMES, Clip, PlayClip, SceneError, png, rgba
from .model import from_model, from_pyvista, screen_xy
from .raster import frame_count, from_cairo, from_frames, still

__all__ = ["DEFAULT_WIDTH", "MAX_FRAMES", "SERIES_ROLES", "Clip", "PlayClip", "SceneError", "frame_count",
           "from_cairo", "from_frames", "from_matplotlib", "from_model", "from_plotly", "from_pyvista", "mpl_style",
           "palette", "plotly_template", "png", "rgba", "screen_xy", "series_colours", "still"]
