"""Scene adapters: frames from Pillow, Cairo, Matplotlib or Plotly as a Clip that an episode places and plays."""
from .clip import DEFAULT_WIDTH, MAX_FRAMES, Clip, PlayClip, SceneError, png, rgba
from .raster import frame_count, from_cairo, from_frames, still

__all__ = ["DEFAULT_WIDTH", "MAX_FRAMES", "Clip", "PlayClip", "SceneError", "frame_count", "from_cairo",
           "from_frames", "png", "rgba", "still"]
