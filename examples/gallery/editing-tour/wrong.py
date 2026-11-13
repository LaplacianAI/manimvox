"""A deliberately wrong hook, for a mistake the film shows (capture.py renders it and keeps the error)."""


def half(rgb, t):
    """An effect that gives back half the frame: the render stops and says why."""
    return rgb[::2]
