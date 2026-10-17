"""Charts in the theme: Matplotlib and Plotly figures as Clips, coloured with the project's roles."""
from __future__ import annotations

import importlib
import io

from ..voice.base import install_hint
from .clip import DEFAULT_WIDTH, Clip, SceneError
from .raster import frame_count

SERIES_ROLES = ("accent", "blue", "orange", "violet", "pink", "teal", "ok", "warn")


def _theme(theme):
    if theme is not None:
        return theme
    from ..kit._context import THEME  # the running episode's theme

    return THEME


def _need(module: str, extra: str):
    try:
        return importlib.import_module(module)
    except ImportError as e:
        raise SceneError(f"{module} is not installed; add the {extra} extra: {install_hint(extra)}") from e


def palette(theme=None) -> dict[str, str]:
    """Every theme role and named colour, by lower-case name."""
    th = _theme(theme)
    return {**th.roles, **{k.lower(): v for k, v in th.named.items()}}


def series_colours(theme=None) -> list[str]:
    """The colours a chart gives its first, second, … series."""
    th = _theme(theme)
    return [th[r] for r in SERIES_ROLES]


def mpl_style(theme=None) -> dict:
    """Matplotlib rcParams in the theme. Build the figure inside `with plt.rc_context(mpl_style()):`."""
    th = _theme(theme)
    cycler = _need("cycler", "matplotlib").cycler
    r = th.roles
    return {
        "figure.facecolor": r["bg"], "axes.facecolor": r["bg"], "savefig.facecolor": r["bg"],
        "axes.edgecolor": r["line"], "axes.labelcolor": r["muted"], "axes.titlecolor": r["ink"],
        "text.color": r["ink"], "xtick.color": r["muted"], "ytick.color": r["muted"],
        "grid.color": r["line"], "axes.grid": True, "grid.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.prop_cycle": cycler(color=series_colours(th)),
        "font.family": "sans-serif", "font.sans-serif": [th.font, "DejaVu Sans"],
        "font.monospace": [th.mono, "DejaVu Sans Mono"],
        "font.size": 14, "lines.linewidth": 2.5, "legend.frameon": False,
    }


def from_matplotlib(obj, fps: float = 15, width: float = DEFAULT_WIDTH, dpi: int = 150) -> Clip:
    """A Matplotlib Figure as one frame, or a FuncAnimation as all of its frames at `fps`."""
    _need("matplotlib", "matplotlib")
    from matplotlib.animation import AbstractMovieWriter, Animation
    from matplotlib.figure import Figure

    def save(fig, **kwargs) -> bytes:
        buf = io.BytesIO()
        kwargs = {"facecolor": fig.get_facecolor(), **kwargs, "dpi": dpi, "format": "png"}
        fig.savefig(buf, **kwargs)
        return buf.getvalue()

    if isinstance(obj, Figure):
        return Clip([save(obj)], 1, width)
    if not isinstance(obj, Animation):
        raise SceneError(f"from_matplotlib takes a Figure or a FuncAnimation, got {type(obj).__name__}")

    class Grab(AbstractMovieWriter):
        def setup(self, fig, outfile, dpi=None):
            super().setup(fig, outfile, dpi)
            self.frames = []

        def grab_frame(self, **savefig_kwargs):
            self.frames.append(save(self.fig, **savefig_kwargs))

        def finish(self):
            pass

    grab = Grab(fps=fps)
    obj.save("frames.png", writer=grab, dpi=dpi)  # the writer keeps frames in memory; no file is written
    return Clip(grab.frames, fps, width)


def plotly_template(theme=None) -> dict:
    """A Plotly template in the theme: `fig.update_layout(template=plotly_template())`."""
    th = _theme(theme)
    r = th.roles
    axis = {"gridcolor": r["line"], "linecolor": r["line"], "zerolinecolor": r["line"],
            "tickfont": {"color": r["muted"]}, "title": {"font": {"color": r["muted"]}}}
    return {"layout": {
        "paper_bgcolor": r["bg"], "plot_bgcolor": r["bg"],
        "font": {"family": th.font, "color": r["ink"], "size": 18},
        "colorway": series_colours(th),
        "xaxis": axis, "yaxis": dict(axis),
        "legend": {"font": {"color": r["ink"]}},
        "margin": {"l": 70, "r": 30, "t": 60, "b": 60},
    }}


def from_plotly(fig, seconds: float | None = None, fps: float = 10, size: tuple[int, int] = (1280, 720),
                width: float = DEFAULT_WIDTH) -> Clip:
    """A Plotly figure as one frame, or `fig(t)` (a function returning a figure) as `seconds` of frames at `fps`.
    Kaleido exports the frames, and it needs Chrome on the machine."""
    _need("plotly", "plotly")
    kaleido = _need("kaleido", "plotly")
    chrome_missing = _need("kaleido.errors", "plotly").ChromeNotFoundError
    if callable(fig):
        if seconds is None:
            raise SceneError("from_plotly(fig_of_t) needs seconds=: how long the frames should run")
        figs = [fig(i / fps) for i in range(frame_count(seconds, fps))]
    else:
        figs, fps = [fig], 1
    opts = {"format": "png", "width": size[0], "height": size[1]}
    try:
        kaleido.start_sync_server(silence_warnings=True)
        try:
            frames = [kaleido.calc_fig_sync(f, opts=opts) for f in figs]
        finally:
            kaleido.stop_sync_server(silence_warnings=True)
    except chrome_missing as e:
        raise SceneError("Plotly export needs Chrome and none was found. Install Google Chrome, or run "
                         "`plotly_get_chrome`, which downloads a copy (ask the user first).") from e
    return Clip(frames, fps, width)
