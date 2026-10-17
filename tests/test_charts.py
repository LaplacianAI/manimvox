import io
import logging
import sys
import types

import numpy as np
import pytest
from PIL import Image

from manimvox.kit.theme import Theme
from manimvox.scenes import SceneError, from_matplotlib, from_plotly, mpl_style, palette, plotly_template, png

TH = Theme.from_dict({"bg": "#000000", "accent": "#FF0000", "named": {"agent": "#3987E5"}, "source": "test"})


def test_palette_has_roles_and_named_colours():
    p = palette(TH)
    assert p["bg"] == "#000000" and p["accent"] == "#FF0000" and p["agent"] == "#3987E5"


def test_mpl_style_wears_the_theme():
    pytest.importorskip("matplotlib")
    s = mpl_style(TH)
    assert s["figure.facecolor"] == "#000000" and s["axes.facecolor"] == "#000000"
    assert s["axes.prop_cycle"].by_key()["color"][0] == "#FF0000"
    assert s["font.sans-serif"][0] == TH.font


def test_a_matplotlib_figure_is_one_frame_on_the_theme_background():
    mpl = pytest.importorskip("matplotlib")
    mpl.use("Agg")
    import matplotlib.pyplot as plt

    with plt.rc_context(mpl_style(TH)):
        fig, ax = plt.subplots(figsize=(4, 2.25))
        ax.plot([0, 1, 2], [0, 1, 4])
    clip = from_matplotlib(fig, dpi=50)
    plt.close(fig)
    assert len(clip.frames) == 1
    assert tuple(clip.pixel_array[1, 1, :3]) == (0, 0, 0)


def test_a_matplotlib_animation_gives_every_frame():
    mpl = pytest.importorskip("matplotlib")
    mpl.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation

    fig, ax = plt.subplots(figsize=(4, 2.25))
    (line,) = ax.plot([], [])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 144)

    def update(i):
        line.set_data(range(i + 1), [x * x for x in range(i + 1)])
        return (line,)

    anim = FuncAnimation(fig, update, frames=12)
    clip = from_matplotlib(anim, fps=12, dpi=50)
    plt.close(fig)
    assert len(clip.frames) == 12 and clip.seconds == pytest.approx(1.0)


def test_from_matplotlib_rejects_other_objects():
    pytest.importorskip("matplotlib")
    with pytest.raises(SceneError, match="Figure or a FuncAnimation"):
        from_matplotlib("not a figure")


def test_missing_matplotlib_names_the_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "matplotlib", None)
    with pytest.raises(SceneError, match=r"manimvox\[kokoro,matplotlib\]"):
        from_matplotlib(object())


def test_plotly_template_wears_the_theme():
    t = plotly_template(TH)["layout"]
    assert t["paper_bgcolor"] == "#000000" and t["colorway"][0] == "#FF0000" and t["font"]["family"] == TH.font


@pytest.fixture
def fake_kaleido(monkeypatch):
    errors = types.ModuleType("kaleido.errors")

    class ChromeNotFoundError(Exception):
        pass

    errors.ChromeNotFoundError = ChromeNotFoundError
    k = types.ModuleType("kaleido")
    k.errors = errors
    k.state = {"running": False, "fail": False, "figs": []}

    def start_sync_server(**kwargs):
        k.state["running"] = True

    def stop_sync_server(**kwargs):
        k.state["running"] = False

    def calc_fig_sync(fig, opts):
        if k.state["fail"]:
            raise ChromeNotFoundError("no chrome")
        assert k.state["running"], "the server must be started once for all frames"
        k.state["figs"].append(fig)
        return png(np.zeros((opts["height"], opts["width"], 3), np.uint8))

    k.start_sync_server, k.stop_sync_server, k.calc_fig_sync = start_sync_server, stop_sync_server, calc_fig_sync
    monkeypatch.setitem(sys.modules, "kaleido", k)
    monkeypatch.setitem(sys.modules, "kaleido.errors", errors)
    return k


def test_from_plotly_still(fake_kaleido):
    go = pytest.importorskip("plotly.graph_objects")
    clip = from_plotly(go.Figure(go.Bar(y=[1, 2])), size=(64, 36))
    assert len(clip.frames) == 1
    assert Image.open(io.BytesIO(clip.frames[0])).size == (64, 36)
    assert not fake_kaleido.state["running"]


def test_from_plotly_function_of_time(fake_kaleido):
    go = pytest.importorskip("plotly.graph_objects")
    clip = from_plotly(lambda t: go.Figure(go.Bar(y=[t, 1])), seconds=2, fps=5, size=(64, 36))
    assert len(clip.frames) == 10 and clip.fps == 5
    assert fake_kaleido.state["figs"][3].data[0].y[0] == pytest.approx(0.6)


def test_from_plotly_function_needs_seconds(fake_kaleido):
    pytest.importorskip("plotly")
    with pytest.raises(SceneError, match="seconds="):
        from_plotly(lambda t: None)


def test_from_plotly_without_chrome_names_the_fix_and_stops_the_server(fake_kaleido):
    go = pytest.importorskip("plotly.graph_objects")
    fake_kaleido.state["fail"] = True
    with pytest.raises(SceneError, match="plotly_get_chrome") as e:
        from_plotly(go.Figure())
    assert "ask the user first" in str(e.value)
    assert not fake_kaleido.state["running"]


@pytest.fixture(autouse=True)
def kaleido_loggers():
    """from_plotly leaves Kaleido's loggers at WARNING for the rest of the process; each test gets them back."""
    loggers = [logging.getLogger("kaleido"), logging.getLogger("choreographer")]
    saved = [lg.level for lg in loggers]
    yield loggers
    for lg, level in zip(loggers, saved):
        lg.setLevel(level)


def _chatty(original):
    def calc_fig_sync(fig, opts):
        logging.getLogger("kaleido").info("noise")
        logging.getLogger("choreographer.x").info("noise")
        return original(fig, opts)

    return calc_fig_sync


def test_kaleido_info_logs_stay_out_of_the_render(fake_kaleido, kaleido_loggers, caplog):
    go = pytest.importorskip("plotly.graph_objects")
    for lg in kaleido_loggers:
        lg.setLevel(logging.INFO)
    fake_kaleido.calc_fig_sync = _chatty(fake_kaleido.calc_fig_sync)
    with caplog.at_level(logging.INFO):
        from_plotly(go.Figure(), size=(64, 36))
    assert not [r for r in caplog.records if r.getMessage() == "noise"]
    assert [lg.level for lg in kaleido_loggers] == [logging.WARNING, logging.WARNING]


def test_kaleido_loggers_stay_at_warning_after_a_missing_chrome(fake_kaleido, kaleido_loggers, caplog):
    go = pytest.importorskip("plotly.graph_objects")
    for lg in kaleido_loggers:
        lg.setLevel(logging.INFO)
    fake_kaleido.calc_fig_sync = _chatty(fake_kaleido.calc_fig_sync)
    fake_kaleido.state["fail"] = True
    with caplog.at_level(logging.INFO), pytest.raises(SceneError, match="plotly_get_chrome"):
        from_plotly(go.Figure())
    assert not [r for r in caplog.records if r.getMessage() == "noise"]
    assert [lg.level for lg in kaleido_loggers] == [logging.WARNING, logging.WARNING]


def test_doctor_reports_the_chart_extras(capsys):
    from manimvox.cli import main

    main(["doctor"])
    out = capsys.readouterr().out
    assert "charts matplotlib" in out and "charts plotly" in out
